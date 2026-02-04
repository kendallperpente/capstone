# Scrapper Update - Royal Kennel Club Integration

## What Changed

The web scrapper has been updated to collect dog breed information from the **Royal Kennel Club** website.

## New Data Source

- **URL**: https://www.royalkennelclub.com/search/breeds-a-to-z
- **Content**: Comprehensive dog breed information including characteristics and breed standards
- **Output File**: `dog_breeds_rkc.json`

## Updated Files

### 1. `scrapper.py`
- **Main function**: `scrape_dog_breeds_rkc()` (replaces `scrape_dog_diseases()`)
- Scrapes breed listing page to find all breed links
- Visits individual breed pages to extract detailed information
- Includes rate limiting (2 second delay between requests) to be respectful to the server
- Limited to 20 breeds by default (configurable via `max_breeds` variable)

### 2. `rag_module.py`
- Updated to use breed data from `dog_breeds_rkc.json`
- Falls back to a small built-in dataset if the file is missing

### 3. `streamlit_app.py`
- Updated checkbox label: "Use Royal Kennel Club Dog Breeds Data"
- Updated help text to reference new output file

### 4. `README.md`
- Updated documentation for the scrapper section
- Clarified purpose and data source

## How to Use

1. **Run the scrapper:**
   ```bash
   python scrapper.py
   ```

2. **Output:**
   - Creates `dog_breeds_rkc.json` with breed information
   - Each document includes: breed name, content, URL, and source

3. **Use with RAG Pipeline:**
   - In Streamlit app, enable "Use Knowledge Base (RAG)"
   - Check "Use Royal Kennel Club Dog Breeds Data"
   - The RAG module will automatically load `dog_breeds_rkc.json`

## Configuration

To scrape more breeds, edit `scrapper.py`:
```python
max_breeds = 20  # Change this value (line ~105)
```

**Note**: Be respectful when scraping - the current implementation includes delays and limits to avoid overloading the server.

## Fallback Behavior

If `dog_breeds_rkc.json` is missing, the app uses a small built-in breed dataset.

## Data Structure

Each document in the JSON file contains:
```json
{
  "title": "Breed Name",
  "content": "Detailed breed information...",
  "url": "https://www.royalkennelclub.com/dog-breeds/...",
  "source": "Royal Kennel Club"
}
```
