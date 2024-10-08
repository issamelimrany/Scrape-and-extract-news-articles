import os
import openai
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize MongoDB client
from pymongo.server_api import ServerApi
mongo_client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))
db = mongo_client['app']
config_collection = db['configurations_prompt']

def get_config(theme):
    config = config_collection.find_one({"config_type": "output_structure", "theme": theme})
    if config:
        return config.get('structure', ''), config.get('prompt', '')
    return '', ''

def extract_information_openai(article_text, theme):
    output_format, prompt_template = get_config(theme)
    
    if not output_format or not prompt_template:
        raise ValueError(f"Configuration for theme '{theme}' not found.")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are an expert in information extraction"},
            {"role": "user", "content": prompt_template.format(article_text=article_text, output_format=output_format)}
        ]
    )
    return response.choices[0].message['content'].strip()

def parse_extracted_info(info_text):
    return info_text.split(";")

def process_openai(input_file_path, theme):
    # Read the Excel file
    df = pd.read_excel(input_file_path)
    
    # Initialize a list to store the results
    articles_data = []

    # Get the output format for the theme
    output_format, _ = get_config(theme)
    output_fields = output_format.split(";")

    # Process each article
    for article_text in df['content']:
        # Extract and parse information
        extracted_info = extract_information_openai(article_text, theme)
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
