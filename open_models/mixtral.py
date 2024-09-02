import os
from groq import Groq
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('groq_api_key')

# Initialize Groq client
client = Groq(api_key="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")

# Initialize MongoDB client
mongo_client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))
db = mongo_client['app']
config_collection = db['configurations_prompt']

def get_config(theme):
    config = config_collection.find_one({"config_type": "output_structure", "theme": theme})
    if config:
        return config.get('structure', ''), config.get('prompt', '')
    return '', ''

def extract_information_open(article_text, theme):
    output_format, prompt_template = get_config(theme)
    
    if not output_format or not prompt_template:
        raise ValueError(f"Configuration for theme '{theme}' not found.")

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_template.format(article_text=article_text, output_format=output_format),
            }
        ],
        model="mixtral-8x7b-32768",
    )
    return chat_completion.choices[0].message.content

def parse_extracted_info(info_text):
    return info_text.split(";")

def process_mixtral(input_file_path, theme):
    # Read the Excel file
    df = pd.read_excel(input_file_path)
    
    # Initialize a list to store the results
    articles_data = []

    # Get the output format for the theme
    output_format, _ = get_config(theme)
    output_fields = output_format.split(";")

    # Process each article
    for article_text in df['Article Text']:
        # Extract and parse information
        extracted_info = extract_information_open(article_text, theme)
        info_list = parse_extracted_info(extracted_info)

        # Create a dictionary for each article's data
        article_data = {field.strip(): info_list[i].strip() if i < len(info_list) else None 
                        for i, field in enumerate(output_fields)}
        
        # Add additional fields
        article_data["link"] = "link"  # TODO: Replace with actual link
        article_data["published_date"] = datetime.today().strftime('%Y-%m-%d')
        article_data["theme"] = theme
        
        # Add the dictionary to the list
        articles_data.append(article_data)

    # Insert the articles data into the MongoDB collection
    collection = db['app_collection']
    collection.insert_many(articles_data)
    
    # Print processing completion message
    file_name = os.path.basename(input_file_path)
    print(f"Processing of {file_name} is complete. Results saved to MongoDB database.")

#test_path = "C:/Users/Issam/code/api/scraping/src/Output/Article_100.xlsx"

#process_mixtral(test_path, "Funding Rounds")


