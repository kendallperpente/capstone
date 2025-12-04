# Capstone Project

A collection of Python applications including a dog medical chatbot, web scraper, and RAG pipeline.

## Applications

### 1. Dog Medical Assistant (`streamlit_app.py`)
A Streamlit web application that provides educational guidance for dog health questions.

**Features:**
- Interactive chat interface for multiple dogs
- Safety notices and emergency vet finder
- Conversation history and export functionality
- OpenAI GPT-powered responses

**Usage:**
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 2. Web Scraper (`scrapper.py`)
A simple web scraping tool using BeautifulSoup and requests.

**Usage:**
```bash
python scrapper.py
```

### 3. RAG Pipeline (`ragpipeline.py`)
Retrieval-Augmented Generation pipeline implementation.

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

- The chatbot is for educational purposes only and does not replace professional veterinary care
- Ensure you have a valid OpenAI API key for the chatbot functionality