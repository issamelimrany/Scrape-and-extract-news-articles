import os

from groq import Groq
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import google.generativeai as genai
from open_models.trained_classifier import classify_article  # Added import for classifier

# Configure Google Generative AI
API_KEY = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-pro')

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

def extract_information_gemini(article_text, theme):
    output_format, prompt_template = get_config(theme)
    
    if not output_format or not prompt_template:
        raise ValueError(f"Configuration for theme '{theme}' not found.")

    print("+"*50)
    print(prompt_template.format(article_text=article_text, output_format=output_format))
    print("+"*50)
    
    prompt = prompt_template.format(article_text=article_text, output_format=output_format)
    return model.generate_content(prompt).text

def parse_extracted_info(info_text):
    return info_text.split(";")

def process_gemini(input_file_path):
    themes = ["Funding Rounds", "Exits"]  # Define the themes to classify
    # Read the Excel file
    df = pd.read_excel(input_file_path)
    
    articles_data = []

    for index, row in df.iterrows():
        article_text = row['content']

        link = row['link']  # Correctly accessing the 'link' column for each row

        theme = classify_article(article_text)

        if theme not in themes: 
            continue  

        extracted_info = extract_information_gemini(article_text, theme)
        info_list = parse_extracted_info(extracted_info)
        
        print("-"*50)
        print(extracted_info)
        print("-"*50)

        output_format, _ = get_config(theme)
        output_fields = output_format.split(";")

        article_data = {field.strip(): info_list[i].strip() if i < len(info_list) else None 
                        for i, field in enumerate(output_fields)}
        
        article_data["link"] = link  
        # article_data["published_date"] = datetime.today().strftime('%Y-%m-%d')
        article_data["published_date"] = pd.Timestamp(row['date'].value).to_pydatetime().strftime('%Y-%m-%d')
        article_data["theme"] = theme
        
        articles_data.append(article_data)

    collection = db['app_collection']
    collection.insert_many(articles_data)
    
    file_name = os.path.basename(input_file_path)

    print(f"Processing of {file_name} is complete. Results saved to MongoDB database.")


