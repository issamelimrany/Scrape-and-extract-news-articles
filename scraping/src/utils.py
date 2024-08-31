import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from newspaper import Article
import csv
import pandas as pd  
from datetime import datetime, timedelta
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Function to extract base URL
def extract_base_url(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

# Function to read configuration from CSV
def read_config(file_path):
    config = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            config.append(row)
    return config

# Function to fetch article links from a page using different navigation types
def fetch_article_links(page_url, headers, target_date=None, navigation_type="pagination", time_tag="time", time_class="entry-date published"):
    base_url = extract_base_url(page_url)

    if target_date is None:
        target_date = datetime.today().date()

    article_links = set()

    try:
        if navigation_type == "pagination":
            pages = navigate_to_date_pagination(page_url, headers, target_date, time_tag, time_class)
            for page_soup in pages:
                for link in page_soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    article_links.add(full_url)

        elif navigation_type == "infinite_scroll":
            soup = navigate_to_date_infinite_scroll(page_url, headers, target_date, time_tag, time_class)
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                article_links.add(full_url)

        elif navigation_type == "load_more_button":
            soup = navigate_to_date_load_more(page_url, headers, target_date, time_tag, time_class)
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                article_links.add(full_url)

        return list(article_links)

    except requests.exceptions.RequestException as e:
        print(f"Error during request to {page_url}: {e}")
        return []

# Function to navigate pages using pagination until the target date is found
def navigate_to_date_pagination(page_url, headers, target_date, time_tag, time_class, start_page=1):
    current_page = start_page
    pages_with_target_date = []

    while True:
        paginated_url = f"{page_url}/page/{current_page}/"

        try:
            response = requests.get(paginated_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Request failed for page {current_page}: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        most_recent_date = track_most_recent_date(soup, time_tag, time_class)

        if not most_recent_date:
            print(f"No valid dates found on page {current_page}. Stopping pagination.")
            break

        if most_recent_date < target_date:
            print(f"Most recent date {most_recent_date} is older than the target date {target_date}. Stopping pagination.")
            break

        if date_found_in_page(soup, target_date, time_tag, time_class):
            print(f"Target date {target_date} found on page {current_page}.")
            pages_with_target_date.append(soup)

        current_page += 1

    return pages_with_target_date

import os 
# Function to navigate pages using infinite scroll until the target date is found
def navigate_to_date_infinite_scroll(page_url, headers, target_date, time_tag, time_class):
    service = Service(executable_path=os.getenv('chromedriver_path'))  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service)
    driver.get(page_url)

    last_height = driver.execute_script("return document.body.scrollHeight")
    soup = None
    most_recent_date = None

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Adjust this delay based on the website's loading time

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        most_recent_date = track_most_recent_date(soup, time_tag, time_class)

        if most_recent_date and most_recent_date < target_date:
            break

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break

        last_height = new_height

    driver.quit()
    return soup

# Function to navigate pages using a "Load More" button until the target date is found
def navigate_to_date_load_more(page_url, headers, target_date, time_tag, time_class):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Optional: run headless for performance

    service = Service(executable_path=os.getenv('chromedriver_path'))  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(page_url)

    soup = None
    most_recent_date = None

    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        most_recent_date = track_most_recent_date(soup, time_tag, time_class)

        if most_recent_date and most_recent_date < target_date:
            break

        try:
            load_more_button = driver.find_element(By.CSS_SELECTOR, 'button.btn-load-more-posts')  # Adjust the selector as needed
            load_more_button.click()
            time.sleep(2)  # Adjust this delay based on the website's loading time
        except:
            break

    driver.quit()
    return soup

# Function to track the most recent date on the page
def track_most_recent_date(soup, time_tag, time_class):
    most_recent_date = None
    current_datetime = datetime.now()

    for date_tag in soup.find_all(time_tag, class_=time_class):
        article_date_str = date_tag.get_text().strip()

        # Handle relative time expressions
        if 'day' in article_date_str or 'hour' in article_date_str or 'minute' in article_date_str:
            if 'day' in article_date_str:
                days_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(days=days_ago)
            elif 'hour' in article_date_str:
                hours_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(hours=hours_ago)
            elif 'minute' in article_date_str:
                minutes_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(minutes=minutes_ago)
            
            article_date = article_date.date()  # Convert to date object
        else:
            try:
                article_date = parser.parse(article_date_str).date()
            except (ValueError, TypeError) as e:
                print(f"Unable to parse date '{article_date_str}': {e}")
                continue

        # Update the most recent date if this one is more recent
        if most_recent_date is None or article_date > most_recent_date:
            most_recent_date = article_date

    return most_recent_date

def date_found_in_page(soup, target_date, time_tag, time_class):
    current_datetime = datetime.now()

    for date_tag in soup.find_all(time_tag, class_=time_class):
        article_date_str = date_tag.get_text().strip()

        # Handle relative time expressions
        if 'day' in article_date_str or 'hour' in article_date_str or 'minute' in article_date_str:
            if 'day' in article_date_str:
                days_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(days=days_ago)
            elif 'hour' in article_date_str:
                hours_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(hours=hours_ago)
            elif 'minute' in article_date_str:
                minutes_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(minutes=minutes_ago)

            article_date = article_date.date()  # Convert to date object

            # Compare the parsed date with the target date
            if article_date == target_date:
                return True
        else:
            try:
                article_date = parser.parse(article_date_str).date()
                if article_date == target_date:
                    return True
            except (ValueError, TypeError) as e:
                print(f"Unable to parse date '{article_date_str}': {e}")

    return False


# Function to filter articles by a specific date and scrape content
def filter_and_scrape_articles(article_links, today):
    results = []

    for article_url in article_links:
        try:
            article = Article(article_url)
            article.download()
            article.parse()

            article_date = article.publish_date

            if article_date:
                if not isinstance(article_date, datetime):
                    try:
                        article_date = parser.parse(article_date)
                    except ValueError:
                        print(f"Unable to parse date for {article_url}: {article_date}")
                        article_date = None

            if article_date and article_date.date() == today:
                results.append({
                    "title": article.title,
                    "content": article.text,
                    "date": article_date.date(),
                    "link": article_url
                })

        except Exception as e:
            print(f"Error processing {article_url}: {e}")

    return results


# Save results to individual CSV files
def save_articles_per_date(results, target_date):
    # Ensure the Output/per_date directory exists
    output_dir = os.path.join("api/src/Output", "per_date", str(target_date))
    os.makedirs(output_dir, exist_ok=True)
    
    # Save each article to a separate CSV file
    for article in results:
        # Create a sanitized filename from the article title
        sanitized_title = "".join(x for x in article['title'] if x.isalnum() or x in "._- ").strip()
        if not sanitized_title:
            sanitized_title = "untitled_article"
        
        # Create the filename
        file_name = f"{sanitized_title}.csv"
        output_file = os.path.join(output_dir, file_name)
        
        # Define the CSV header
        keys = article.keys()
        
        # Write the article to a CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerow(article)

    print(f"Articles have been saved as individual files in the 'Output/per_date/{target_date}' directory.")



