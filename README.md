# 🐕 Dog Breed Selector - AI-Powered Breed Recommendation System

## Project Goal

Create an intelligent LLM-based system that helps users find their perfect dog breed match using:
1. **Characteristic-Based Search**: Users describe desired traits, system recommends matching breeds
2. **Survey-Based Recommendation**: 11-question quiz about lifestyle generates tailored suggestions

Both leverage a **Retrieval-Augmented Generation (RAG) pipeline** combining semantic search with LLM intelligence.

---

## System Architecture

### 1. **Web Scraper** (`scrapper.py`)
Collects dog breed information from the Royal Kennel Club website.

- Scrapes all breeds from https://www.royalkennelclub.com/search/breeds-a-to-z
- Extracts breed names, descriptions, and characteristics
- Saves to `dog_breeds_rkc.json` (300+ breeds)
- Respectful scraping with delays between requests

```bash
python scrapper.py
```

### 2. **RAG Pipeline Module** (`rag_module.py`)
Implements Retrieval-Augmented Generation for personalized recommendations.

**Components:**
- Document Store (in-memory breed database)
- Embeddings (Sentence Transformers for semantic search)
- Retriever (finds relevant breeds)
- Prompt Builder (constructs context-aware prompts)
- LLM (OpenAI GPT-4o-mini generates responses)

**Usage:**
```python
from rag_module import get_rag_pipeline
rag = get_rag_pipeline(use_scraped_data=True)
answer = rag.answer_question("I need a dog good with kids and low energy")
print(answer)
```

### 3. **Streamlit Web Application** (`streamlit_app.py`)
Interactive user interface with two parallel recommendation methods.

**Left Panel: Search by Characteristics**
- Free-text input for desired traits
- Instant AI-powered recommendations
- Shows top breed matches with explanations

**Right Panel: Quiz-Based Selection**
- 11-question survey on lifestyle, space, experience, preferences
- Generates comprehensive profile
- Delivers tailored breed matches

**Data Management**
- Auto-detects scraped breed data
- Offers fresh scraping from Royal Kennel Club
- Shows data source attribution
- Pipeline reload controls

```bash
export OPENAI_API_KEY='your-key'
streamlit run streamlit_app.py
```

---

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='sk-your-actual-key'
   ```

3. **Run the app:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open browser to:** `http://localhost:8501`

5. **(Optional) Scrape fresh data:**
   ```bash
   python scrapper.py
   ```

---

## File Structure

```
├── streamlit_app.py          # Web UI (2 recommendation methods)
├── rag_module.py             # RAG pipeline (embeddings + LLM)
├── scrapper.py               # Royal Kennel Club web scraper
├── dog_breeds_rkc.json       # Breed database (generated)
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

---

## Features

✅ Dual input methods (characteristics + quiz)  
✅ RAG-powered recommendations (semantic + LLM)  
✅ Fresh data scraping from Royal Kennel Club  
✅ Fallback support (built-in 5-breed dataset)  
✅ Well-documented code  
✅ User-friendly Streamlit interface  

---

## Troubleshooting

**"OpenAI API error"**: Set `export OPENAI_API_KEY='sk-your-key'`  
**"No scraped data found"**: Use app's "Scrape Data" button or run `python scrapper.py`  
**Low recommendation quality**: Ensure you have 300+ breeds (not fallback dataset)

---

## Dependencies

- streamlit (UI)
- openai (GPT API)
- haystack-ai (RAG framework)
- sentence-transformers (embeddings)
- requests, beautifulsoup4 (web scraping)
- datasets (utilities)