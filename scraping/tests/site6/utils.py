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
from dateutil import parser

# Function to extract base URL
def extract_base_url(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

# Function to fetch article links from a page
def fetch_article_links(page_url, headers, target_date=None, navigation_type="pagination"):
    base_url = extract_base_url(page_url)

    if target_date is None:
        target_date = datetime.today().date()

    article_links = set()
    try:
        if navigation_type == "pagination":
            soup = navigate_to_date_pagination(page_url, headers, target_date)
        elif navigation_type == "infinite_scroll":
            soup = navigate_to_date_infinite_scroll(page_url, headers, target_date)
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

# Function to navigate to a specific date using pagination




def date_found_in_page(soup, target_date):
    """Check if the target date is present in the page."""
    for date_tag in soup.find_all('time', class_='entry-date published'):
        article_date_str = date_tag.get('datetime')
        if article_date_str:
            try:
                article_date = parser.parse(article_date_str).date()
                if article_date == target_date:
                    return True
            except (ValueError, TypeError) as e:
                print(f"Unable to parse date '{article_date_str}': {e}")
    return False

def navigate_to_date_pagination(page_url, headers, target_date, start_page=1):
   
    current_page = start_page
    found_target_date = False
    last_page_with_target_date = None

    while True:
        # Construct the URL for the current page
        paginated_url = f"{page_url}/page/{current_page}/"
        
        # Make the HTTP request to get the page content
        response = requests.get(paginated_url, headers=headers)
        response.raise_for_status()
        
        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if the target date is found on this page
        if date_found_in_page(soup, target_date):
            print(f"Target date {target_date} found on page {current_page}.")
            found_target_date = True
            last_page_with_target_date = soup
        else:
            # If we previously found the target date but it's not on this page, stop
            if found_target_date:
                print(f"Target date {target_date} not found on page {current_page}. Stopping pagination.")
                break
        
        # If no next page is available and the target date hasn't been found yet, stop the loop
        
        
        # Move to the next page
        current_page += 1

    # Return the last page that had the target date
    return last_page_with_target_date



# Function to navigate to a specific date using infinite scroll
def navigate_to_date_infinite_scroll(page_url, headers, target_date):
    service = Service(executable_path=r'scrapingenv\Lib\site-packages\selenium\webdriver\chrome\webdriver.py')  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service)
    driver.get(page_url)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        if date_found_in_page(soup, target_date):
            break

    driver.quit()
    return soup

# Function to navigate to a specific date using "Load More" button
def navigate_to_date_load_more(base_url, headers, target_date):
    service = Service(executable_path=r'scrapingenv\Lib\site-packages\selenium\webdriver\chrome\webdriver.py')  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)

    while True:
        try:
            more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')]")
            more_button.click()
            time.sleep(2)  # Wait for new content to load

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            if date_found_in_page(soup, target_date):
                break
        except Exception as e:
            print(f"No more 'Load More' buttons or an error occurred: {e}")
            break

    driver.quit()
    return soup

# Function to check if the target date is found on the page


def date_found_in_page(soup, target_date):
    
    # Iterate over all <time> tags with the relevant class (adjust selector as needed)
    for date_tag in soup.find_all('time', class_='entry-date published'):
        # Extract the datetime attribute value
        article_date_str = date_tag.get('datetime')
        
        if article_date_str:
            try:
                # Parse the datetime string into a date object
                article_date = parser.parse(article_date_str).date()
                
                # Compare the parsed date with the target date
                if article_date == target_date:
                    return True
            except (ValueError, TypeError) as e:
                # Print an error message if parsing fails
                print(f"Unable to parse date '{article_date_str}': {e}")

    # Return False if the target date is not found
    return False
from dateutil import parser
from bs4 import BeautifulSoup

def date_found_earlier_than_target(soup, target_date):
   
    # Iterate over all <time> tags with the relevant class (adjust selector as needed)
    for date_tag in soup.find_all('time', class_='entry-date published'):
        # Extract the datetime attribute value
        article_date_str = date_tag.get('datetime')
        
        if article_date_str:
            try:
                # Parse the datetime string into a date object
                article_date = parser.parse(article_date_str).date()
                
                # Check if the parsed date is earlier than the target date
                if article_date < target_date:
                    return True
            except (ValueError, TypeError) as e:
                # Print an error message if parsing fails
                print(f"Unable to parse date '{article_date_str}': {e}")

    # Return False if no earlier date is found
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
            
            # Debugging output
            print(f"Article URL: {article_url}")
            print(f"Original publish_date: {article_date}")
            print(f"Type of publish_date: {type(article_date)}")
            
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