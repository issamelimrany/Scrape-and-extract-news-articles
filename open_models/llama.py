import os
from groq import Groq
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
from open_models.trained_classifier import classify_article  
import json

# Initialize Groq client
client = Groq(api_key=os.getenv('groq_api_key'))

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

def extract_information_open(article_text, theme):
    output_format, prompt_template = get_config(theme)

    if not output_format or not prompt_template:
        raise ValueError(f"Configuration for theme '{theme}' not found.")

    print("+"*50)
    print(prompt_template.format(article_text=article_text, output_format=output_format))
    print("+"*50)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_template.format(article_text=article_text, output_format=output_format),
            }
        ],
        model="llama3-70b-8192",
    )
    return chat_completion.choices[0].message.content


def parse_extracted_info(info_text):
    # print(f"Trying to parse >>>>>> \n {info_text}")
    rslts_json = json.loads(info_text)
    print(f"Json Object >>>>>> \n {type(rslts_json)} \n {rslts_json}")
    return rslts_json

def process_llama(input_file_path):
    themes = ["Funding Rounds", "Exits"]  

    df = pd.read_excel(input_file_path)
    
    articles_data = []

    # Process each article
    for index, row in df.iterrows():
        article_text = row['content']
        link = row['link']  

        # Classify the article to determine the theme
        theme = classify_article(article_text)

        # Pass to the next articles if it doesn't make part of any theme
        if theme not in themes: 
            continue  

        # Extract and parse information
        extracted_info = extract_information_open(article_text, theme)
        info_list = parse_extracted_info(extracted_info)

        # Create a dictionary for each article's data
        output_format, _ = get_config(theme)  # Get output format for the theme
        output_fields = output_format.split(";")
        
        article_data = {}
        article_data = info_list

        # article_data = {field.strip(): info_list[i].strip() if i < len(info_list) else None 
        #                 for i, field in enumerate(output_fields)}
        
        if isinstance(article_data, list):
            # If article_data is a list, iterate over each element and add the fields
            for article in article_data:
                article["link"] = link
                article["published_date"] = pd.Timestamp(row['date'].value).to_pydatetime().strftime('%Y-%m-%d')
                article["theme"] = theme

                print("---------------------- Inserted Article Data ----------------------")
                print(article)
                print("-------------------------------------------------------------------")
                    
                # Add the dictionary to the list
                articles_data.append(article)
        else:
            # If article_data is a dictionary, add the fields directly
            article_data["link"] = link
            article_data["published_date"] = pd.Timestamp(row['date'].value).to_pydatetime().strftime('%Y-%m-%d')
            article_data["theme"] = theme
            
            # Add the dictionary or list to the articles_data list
            articles_data.append(article_data)

            print("---------------------- Inserted Article Data ----------------------")
            print(article_data)
            print("-------------------------------------------------------------------")


    if len(articles_data) > 0:
        # Insert the articles data into the MongoDB collection
        collection = db['app_collection']
        collection.insert_many(articles_data)
        
        # Print processing completion message
        file_name = os.path.basename(input_file_path)

        print(f"Processing of {file_name} is complete. Results saved to MongoDB database.")
    else:
        print("No articles to process.")