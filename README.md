# Article Data Management System

This project is a Flask-based web application for managing article data, including scraping, processing, and storing articles using various AI models.

## Features

- Scrape articles from multiple sources
- Process articles using different AI models (OpenAI, Anthropic, Google, Mixtral, LLaMA, Gemma)
- Store and manage article data in MongoDB
- Filter and export article data
- Configure AI models and output structures

## Prerequisites

- Python 3.12.3+
- MongoDB
- Chrome WebDriver (for scraping)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/issamelimrany/Scrape-and-extract-news-articles.git
   cd Scrape-and-extract-news-articles
   ```

2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Add you keys to the `.env` file in the `api`.

## Running the Application

1. Start the Flask server:

   ```bash
   flask run
   ```

2. Open a web browser and navigate to `http://localhost:5000`

## Usage

1. **Home Page**: View and filter articles by theme and date.
2. **Add Article**: Manually add new articles.
3. **Configure LLM**: Select the AI model for processing articles.
4. **Modify Output Structure**: Customize the output structure for different themes.
5. **Scrape and Extract**: Run the scraper and process articles using the selected AI model.

## Project Structure

- `api/`: Main application directory
  - `app.py`: Flask application and routes
  - `scraping/`: Web scraping scripts
  - `closed_models/`: AI model processing scripts (OpenAI, Anthropic, Google)
  - `open_models/`: Open-source AI model processing scripts (Mixtral, LLaMA, Gemma)
  - `templates/`: HTML templates for the web interface
