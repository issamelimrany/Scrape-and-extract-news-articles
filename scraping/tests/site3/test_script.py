import os
import sys
import json
from datetime import datetime

# Adjust the path to include the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils2 import fetch_article_links, filter_and_scrape_articles, save_results_to_csv

# Define target date
target_date = datetime.strptime("06-08-2024", "%d-%m-%Y").date()

def test_single_site():
    # Load site configuration
    config_path = os.path.join(os.path.dirname(__file__), 'site_config.json')
    
    with open(config_path, 'r') as file:
        site_config = json.load(file)
    
    page_url = site_config['page_url']
    navigation_type = site_config['navigation_type']
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # Fetch article links for the site
        print(f"Fetching article links from {page_url}...")
        article_links = fetch_article_links(page_url, headers, target_date, navigation_type)
        
        # Filter articles published on the target date and scrape their content
        print("Filtering and scraping articles...")
        results = filter_and_scrape_articles(article_links, target_date)
        
        # Generate the output filename with the target date
        target_date_str = target_date.strftime('%d-%m-%Y')
        output_csv_file = os.path.join(os.path.dirname(__file__), f'scraped_article_{target_date_str}.csv')
        
        # Save results to CSV file
        save_results_to_csv(results, output_csv_file)
        
        print(f"Results saved to {output_csv_file}")
    
    except Exception as e:
        print(f"Error processing site {page_url}: {e}")

if __name__ == "__main__":
    test_single_site()