from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash
from pymongo.mongo_client import MongoClient
import pandas as pd
from datetime import datetime
from bson.objectid import ObjectId
from io import BytesIO  

# Importing processing functions for different models : 

from closed_models.openai import process_openai
from closed_models.anthropic import process_anthropic
from closed_models.google import process_gemini
from scraping.src.main import main as run_scraper
from open_models.mixtral import process_mixtral
from open_models.llama import process_llama
from open_models.gemma import process_gemma
from open_models.gemma2 import process_gemma2


import os
from glob import glob


app = Flask(__name__)
app.secret_key = "something"


# MongoDB setup
from pymongo.server_api import ServerApi
client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))

db = client['app']
collection = db['app_collection'] # extracted data for each .xlsx article from the each folder
articles_collection = db['articles_collection'] # Manually added articles     
config_collection = db['configurations'] # LLM model configuration
config_collection_p = db['configurations_prompt'] # Output structure configuration

@app.route('/', methods=['GET', 'POST'])
def index():
    theme = request.form.get('theme', 'Funding Rounds')
    selected_date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

    query = {
        "published_date": selected_date,
        "theme": theme
    }

    articles = list(collection.find(query))

    return render_template('index.html', articles=articles, message=None, datetime=datetime, selected_theme=theme, selected_date=selected_date)


@app.route('/export', methods=['POST'])
def export():
    theme = request.form.get('theme', 'default_theme')
    selected_date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

    query = {
        "published_date": selected_date,
        "theme": theme
    }
    articles = list(collection.find(query))

    if not articles:
        return jsonify({"error": "No data available for the selected date."}), 400

    df = pd.DataFrame(articles)
    csv_data = df.to_csv(index=False).encode('utf-8')  # Encode to bytes

    buffer = BytesIO()  # Use BytesIO instead of StringIO
    buffer.write(csv_data)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'{selected_date}_{theme}_data.csv',
        mimetype='text/csv'
    )

@app.route('/delete', methods=['POST'])
def delete_article():
    article_id = request.form.get('article_id')
    result = collection.delete_one({"_id": ObjectId(article_id)})
    if result.deleted_count > 0:
        return jsonify({"success": True, "message": "Article deleted successfully."})
    else:
        return jsonify({"success": False, "message": "Article not found or could not be deleted."}), 404


from bson import ObjectId
import json

@app.route('/edit/<string:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    article = collection.find_one({"_id": ObjectId(article_id)})
    if request.method == 'POST':
        updated_article = {}
        for key, value in request.form.items():
            if key != '_id':  # Skip the _id field
                updated_article[key] = value

        collection.update_one({"_id": ObjectId(article_id)}, {"$set": updated_article})
        flash('Article updated successfully!', 'success')
        return redirect(url_for('index'))
    
    # Convert ObjectId to string and prepare article data for JSON
    article_data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in article.items()}
    return render_template('edit_article.html', article=json.dumps(article_data))

@app.route('/add_article', methods=['GET', 'POST'])
def add_article():
    if request.method == 'POST':
        theme = request.form.get('theme')
        
        if theme == "Funding Rounds":
            fields = ["Startup Name", "Country", "Year of Establishment", "Sector", "Amount Raised", "Valuation", "Announced Date", "Funding Stage", "Type of Funding", "Investors", "Lead Investors", "Founders", "CEO"]
        elif theme == "Exits":
            fields = ["Announced Date", "Type", "Type of acquisition", "Companies", "Acquirer", "Acquiree", "Country of the acquiree", "Acquiree's Year of Establishment", "Sector of the acquiree", "Sector of Merged Company 1", "Sector of Merged Company 2", "Country of merged company 1", "Country of merged company 2", "Amount", "Stake acquired"]
        else:
            flash('Invalid theme selected.')
            return redirect(url_for('add_article'))

        article_data = {field: request.form.get(field) for field in fields}
        article_data["theme"] = theme
        article_data["published_date"] = datetime.now().strftime('%Y-%m-%d')

        collection.insert_one(article_data)
        flash('Article added successfully!')
        return redirect(url_for('index'))
    
    return render_template('add_article.html')

@app.route('/configure_llm', methods=['GET', 'POST'])
def configure_llm():
    if request.method == 'POST':
        selected_model = request.form.get('llm_model')
        config_collection.update_one(
            {"config_type": "llm_model"},
            {"$set": {"model": selected_model}},
            upsert=True
        )
        flash(f'LLM Model {selected_model} configured successfully!')
        return redirect(url_for('index'))
    
    config = config_collection.find_one({"config_type": "llm_model"})
    current_model = config.get("model") if config else None
    
    llm_models = ["gpt-4o", "claude", "gemini", "mixtral", "llama", "gemma", "gemma2"]  # List of available models
    return render_template('configure_llm.html', llm_models=llm_models, current_model=current_model)

@app.route('/modify_structure', methods=['GET', 'POST'])
def modify_structure():
    if request.method == 'POST':
        new_structure = request.form.get('structure')
        new_prompt = request.form.get('prompt')
        theme = request.form.get('theme')
        config_collection_p.update_one(
            {"config_type": "output_structure", "theme": theme},
            {"$set": {"structure": new_structure, "prompt": new_prompt}},
            upsert=True
        )
        flash('Output file structure and prompt modified successfully!')
        return redirect(url_for('index'))
    
    themes = ["Funding Rounds", "Exits"]
    structures = {}
    prompts = {}
    for theme in themes:
        config = config_collection_p.find_one({"config_type": "output_structure", "theme": theme})
        if config:
            structures[theme] = config.get('structure', "")
            prompts[theme] = config.get('prompt', "")
        else:
            structures[theme] = ""
            prompts[theme] = ""
    return render_template('modify_structure.html', structures=structures, prompts=prompts)



@app.route('/scrape_and_extract', methods=['GET', 'POST'])
def scrape_and_extract():
    if request.method == 'POST':
        target_date = request.form['target_date']
        
        # Run the scraper
        run_scraper(target_date)

        # Get the configured LLM model
        config = config_collection.find_one({"config_type": "llm_model"})
        selected_model = config.get("model") if config else "gemini"

        # Get the configured output structure
        structure_config = config_collection_p.find_one({"config_type": "output_structure"})
        output_structure = structure_config.get("structure") if structure_config else []

        # Process Excel files in the output folder
        output_folder = os.getenv('articles_output_path') + "/" + target_date
        excel_files = glob(os.path.join(output_folder, "*.xlsx"))

        for excel_file in excel_files:
            if selected_model == "gpt-4o":
                process_openai(excel_file, output_structure)
            elif selected_model == "claude":
                process_anthropic(excel_file, output_structure)
            elif selected_model == "gemini":
                process_gemini(excel_file, output_structure)
            elif selected_model == "mixtral":
                process_mixtral(excel_file, output_structure)
            elif selected_model == "llama":
                process_llama(excel_file, output_structure)
            elif selected_model == "gemma":
                process_gemma(excel_file, output_structure)
            elif selected_model == "gemma2":
                process_gemma2(excel_file, output_structure)
            else:
                process_mixtral(excel_file, output_structure)

        return "Scraping and extraction completed successfully!"
    
    return render_template('scrape_and_extract.html')

if __name__ == '__main__':
    app.run(debug=True)