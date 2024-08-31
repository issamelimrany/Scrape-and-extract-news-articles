import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from newspaper import Article
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
from datetime import datetime, timedelta
from dateutil import parser

# Function to extract base URL
def extract_base_url(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


def fetch_article_links(page_url, headers, target_date=None, navigation_type="pagination"):
    base_url = extract_base_url(page_url)

    if target_date is None:
        target_date = datetime.today().date()

    article_links = set()
    try:
        if navigation_type == "pagination":
            pages = navigate_to_date_pagination(page_url, headers, target_date)
            for page_soup in pages:
                for link in page_soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    article_links.add(full_url)
        elif navigation_type == "infinite_scroll":
            soup = navigate_to_date_infinite_scroll(page_url, headers, target_date)
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                article_links.add(full_url)
        elif navigation_type == "load_more_button":
            soup = navigate_to_date_load_more(page_url, headers, target_date)
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                article_links.add(full_url)

        return list(article_links)

    except requests.exceptions.RequestException as e:
        print(f"Error during request to {page_url}: {e}")
        return []








def navigate_to_date_pagination(page_url, headers, target_date, start_page=1):
    current_page = start_page
    pages_with_target_date = []

    while True:
        # Construct the URL for the current page
        paginated_url = f"{page_url}/page/{current_page}/"
        
        # Make the HTTP request to get the page content
        try:
            response = requests.get(paginated_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Request failed for page {current_page}: {e}")
            break
        
        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Track the most recent date on the current page
        most_recent_date = track_most_recent_date(soup)
        
        if not most_recent_date:
            print(f"No valid dates found on page {current_page}. Stopping pagination.")
            break
        
        # Stop the loop if the most recent date is older than the target date
        if most_recent_date < target_date:
            print(f"Most recent date {most_recent_date} is older than the target date {target_date}. Stopping pagination.")
            break
        
        # Check if the target date is found on the current page
        if date_found_in_page(soup, target_date):
            print(f"Target date {target_date} found on page {current_page}.")
            pages_with_target_date.append(soup)
        
        # Move to the next page
        current_page += 1
        
        # Check if there is a next page
        

    # Return all pages that had the target date
    return pages_with_target_date 




def track_most_recent_date(soup):
    """Find the most recent date on the page."""
    most_recent_date = None
    current_datetime = datetime.now()

    # Loop through all date elements on the page
    for date_tag in soup.find_all('span', class_="post-meta post-date"):
        article_date_str = date_tag.get_text().strip()

        if 'day' in article_date_str or 'hour' in article_date_str or 'minute' in article_date_str:
            # Handle relative dates like "1 day ago", "3 hours ago", or "15 minutes ago"
            if 'day' in article_date_str:
                days_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(days=days_ago)
            elif 'hour' in article_date_str:
                hours_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(hours=hours_ago)
            elif 'minute' in article_date_str:
                minutes_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(minutes=minutes_ago)

        else:
            # Handle other date formats like "2024-08-30"
            try:
                article_date = parser.parse(article_date_str).date()
            except (ValueError, TypeError) as e:
                print(f"Unable to parse date '{article_date_str}': {e}")
                continue

        # Update the most recent date if this one is more recent
        if most_recent_date is None or article_date > most_recent_date:
            most_recent_date = article_date

    return most_recent_date

def navigate_to_date_infinite_scroll(page_url, headers, target_date):
    service = Service(executable_path=r"C:\Users\dell\Downloads\chromedriver-win64\chromedriver.exe")  # Update with your chromedriver path
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

        # Track the most recent date on the current page
        most_recent_date = track_most_recent_date(soup)

        # Stop scrolling if the most recent date is older than the target date
        if most_recent_date and most_recent_date < target_date:
            break

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break

        last_height = new_height

    driver.quit()
    return soup



# Function to navigate to a specific date using "Load More" button
def navigate_to_date_load_more(base_url, target_date, button_text="Load More"):
    """
    Navigate through a page using the 'Load More' button identified by its text to find articles up to a specific target date.

    """
    service = Service(executable_path=r"C:\Users\dell\Downloads\chromedriver-win64\chromedriver.exe")  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)

    while True:
        try:
            # Find the 'Load More' button by its text
            more_button = driver.find_element(By.XPATH, f"//button[text()='{button_text}']")
            more_button.click()
            time.sleep(2)  # Adjust this delay based on the website's loading time

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Check if the most recent date on the page is older than the target date
            most_recent_date = track_most_recent_date(soup)
            if most_recent_date and most_recent_date < target_date:
                break
        except Exception as e:
            print(f"No more 'Load More' buttons or an error occurred: {e}")
            break

    driver.quit()
    return soup

# Function to check if the target date is found on the page



def date_found_in_page(soup, target_date):
    current_datetime = datetime.now()

    # Iterate over all <span> tags with the relevant class
    for date_tag in soup.find_all('span', class_='post-meta post-date'):
        article_date_str = date_tag.get_text().strip()  # Get text inside the span tag

        if 'day' in article_date_str or 'hour' in article_date_str or 'minute' in article_date_str:
            # Handle relative dates like "1 day ago", "3 hours ago", or "15 minutes ago"
            if 'day' in article_date_str:
                days_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(days=days_ago)
            elif 'hour' in article_date_str:
                hours_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(hours=hours_ago)
            elif 'minute' in article_date_str:
                minutes_ago = int(article_date_str.split()[0])
                article_date = current_datetime - timedelta(minutes=minutes_ago)
            
            # Compare the parsed date with the target date
            if article_date.date() == target_date:
                return True

        else:  # Handle other date formats like "2024-08-30"
            try:
                article_date = parser.parse(article_date_str).date()
                if article_date == target_date:
                    return True
            except (ValueError, TypeError) as e:
                print(f"Unable to parse date '{article_date_str}': {e}")

    # Return False if the target date is not found
    return False



# Function to filter articles by a specific date and scrape content
def filter_and_scrape_articles(article_links, today):
    results = []
    for article_url in article_links:
        try:
            article = Article(article_url)
            article.download()
            article.parse()
            
            # Retrieve the publish_date
            article_date = article.publish_date
            
          
            if article_date:
                # Ensure article_date is a datetime object
                if not isinstance(article_date, datetime):
                    try:
                        article_date = parser.parse(article_date)
                    except ValueError:
                        print(f"Unable to parse date for {article_url}: {article_date}")
                        article_date = None
            
            # Check if the article date matches today's date
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

#save results to a CSV file
def save_results_to_csv(results, filename):
    keys = results[0].keys() if results else ['title', 'content', 'date', 'link']
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)

# Function to load URLs from a CSV file
def load_urls_from_csv(filename):
    sites = []
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sites.append({"page_url": row["page_url"], "base_url": row["base_url"]})
    return sites