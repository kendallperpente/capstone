# Capstone Project

A collection of Python applications including a dog breed recommender, web scraper, and RAG pipeline.

## Applications

### 1. Dog Breed Recommender (`streamlit_app.py`)
A Streamlit web application that recommends dog breeds based on user lifestyle and preferences.

**Features:**
- Interactive chat interface for multiple dogs
- Lifestyle-based breed matching
- Conversation history and export functionality
- OpenAI GPT-powered responses (optional RAG grounding)

**Usage:**
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 2. Web Scraper (`scrapper.py`)
A web scraping tool that collects dog breed information from the Royal Kennel Club website.

**Features:**
- Scrapes breed information from https://www.royalkennelclub.com/search/breeds-a-to-z
- Extracts detailed breed descriptions and characteristics
- Saves data to JSON format for use with the RAG pipeline
- Respectful scraping with delays between requests

**Usage:**
```bash
python scrapper.py
```

This will create `dog_breeds_rkc.json` with breed data that can be loaded by the RAG pipeline.

### 3. RAG Pipeline (`rag_module.py`)
Retrieval-Augmented Generation pipeline for breed recommendations.

**Usage:**
```bash
python ragpipeline.py
```

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set OpenAI API key: `export OPENAI_API_KEY=your_api_key`
4. Run any application as shown above

## Notes

- Ensure you have a valid OpenAI API key for the chatbot functionality