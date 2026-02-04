# Streamlit + Scraper Integration Guide

## Overview
The Streamlit app is now fully integrated with the scraper and RAG module. When users type in breed characteristics, the AI uses scraped Royal Kennel Club data to provide recommendations.

## How It Works

### 1. Data Flow
```
User Input → Streamlit App → RAG Pipeline → Scraped Breed Data → AI Answer
```

### 2. Key Features

#### A. Search by Characteristics
- Users type characteristics (e.g., "high energy, good with kids, low shedding")
- Click "Search breeds" button
- AI uses RAG pipeline to search scraped breed data
- Returns personalized recommendations with reasoning

#### B. Quiz-Based Recommendations
- Users answer 11 questions about their lifestyle
- Submit quiz
- AI analyzes all answers and recommends best-fit breeds
- Provides alternatives with explanations

#### C. Data Source Management
- **Settings Expander**: Shows current data status
- **Scrape Data Button**: Fetches fresh breed data from Royal Kennel Club
- **Refresh Button**: Re-scrapes data if website updates
- **Reload Pipeline**: Resets RAG pipeline with new data

### 3. Data Sources

The app intelligently handles two data sources:

1. **Scraped Data** (Primary): 
   - File: `dog_breeds_rkc.json`
   - Source: Royal Kennel Club website
   - ~30 breeds with detailed information
   - Created by running the scraper

2. **Fallback Data** (Backup):
   - Built-in dataset in `rag_module.py`
   - 5 common breeds
   - Used when no scraped data exists

## Setup & Usage

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

### Running the App

#### Option 1: Quick Start (Use Built-in Data)
```bash
streamlit run streamlit_app.py
```
The app will use the built-in 5-breed dataset.

#### Option 2: With Scraped Data
```bash
# Step 1: Scrape Royal Kennel Club data
python scrapper.py

# Step 2: Run the app
streamlit run streamlit_app.py
```

#### Option 3: Scrape from Within App
1. Start the app: `streamlit run streamlit_app.py`
2. Click "⚙️ Data Source Settings" expander
3. Click "🌐 Scrape Royal Kennel Club Data"
4. Wait for scraping to complete
5. Start searching for breeds!

### Testing the Integration
```bash
python test_integration.py
```

## Code Changes Made

### streamlit_app.py
1. **Import Integration**
   - Added imports for `scrapper` and `rag_module`
   - Added session state for RAG pipeline management

2. **Data Source UI**
   - Added settings expander showing data status
   - Scrape/refresh buttons for data management
   - Status indicators for scraped vs built-in data

3. **Search Functionality**
   - Initializes RAG pipeline on first search
   - Queries scraped breed data
   - Displays AI-generated recommendations
   - Shows data source being used

4. **Quiz Integration**
   - Builds detailed query from all quiz answers
   - Uses same RAG pipeline for recommendations
   - Provides personalized results based on lifestyle

## User Experience Flow

### Scenario 1: Characteristic Search
1. User opens app
2. Types: "friendly, apartment-friendly, low maintenance"
3. Clicks "Search breeds"
4. App initializes RAG (if needed)
5. AI searches scraped breed database
6. Returns: French Bulldog, Cavalier King Charles Spaniel, etc.
7. Shows reasoning for each recommendation

### Scenario 2: First-Time User with Scraping
1. User opens app (no scraped data)
2. Sees warning: "No scraped data found"
3. Clicks "🌐 Scrape Royal Kennel Club Data"
4. App scrapes ~30 breeds (takes ~2 minutes)
5. Success message appears
6. User can now search with full dataset

### Scenario 3: Quiz Flow
1. User clicks "Take quiz"
2. Answers 11 lifestyle questions
3. Clicks "Get my breed suggestion"
4. App processes all answers
5. Returns comprehensive recommendations
6. Shows top match + alternatives

## Technical Details

### RAG Pipeline Initialization
- **Lazy Loading**: Pipeline initializes only when first needed
- **Cached**: Reused across multiple queries in same session
- **Reloadable**: Can refresh if data changes

### Scraper Integration
- **On-Demand**: Can scrape fresh data anytime
- **Persistent**: Saves to JSON file for reuse
- **Royal Kennel Club Focus**: Only scrapes official breed data

### Error Handling
- Checks for OPENAI_API_KEY
- Handles scraping failures gracefully
- Falls back to built-in data if needed
- Shows helpful error messages to users

## Troubleshooting

### Issue: "Error getting recommendation"
**Solution**: Make sure OPENAI_API_KEY is set
```bash
export OPENAI_API_KEY='sk-...'
```

### Issue: "No scraped data found"
**Solution**: 
- Click the scrape button in settings expander, OR
- Run `python scrapper.py` manually

### Issue: Recommendations seem limited
**Solution**: Scrape fresh data for more breeds
- Current built-in: 5 breeds
- After scraping: ~30 breeds

### Issue: Scraping fails
**Solution**: 
- Check internet connection
- Website might have changed structure
- Use built-in data as fallback

## File Structure
```
streamlit_app.py       # Main UI with integrated scraper + RAG
scrapper.py           # Royal Kennel Club scraper
rag_module.py         # RAG pipeline implementation
dog_breeds_rkc.json   # Scraped breed data (created by scraper)
test_integration.py   # Integration test script
```

## Next Steps

### Enhancements You Can Make:
1. Add more breeds by increasing `max_breeds` in scrapper.py
2. Add breed images to recommendations
3. Save user preferences/history
4. Add comparison feature between breeds
5. Export recommendations as PDF
6. Add filters (size, energy level, etc.)

## Summary

The integration is complete! Users can now:
- ✅ Type characteristics and get AI-powered breed recommendations
- ✅ Take a quiz for personalized suggestions
- ✅ Scrape fresh data from Royal Kennel Club
- ✅ Use fallback data when needed
- ✅ See which data source is being used
- ✅ Refresh data anytime

The scraper and RAG pipeline work seamlessly together to provide accurate, personalized dog breed recommendations based on real breed data.
