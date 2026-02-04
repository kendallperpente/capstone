#!/usr/bin/env python3
"""
Test script to verify the integration between scrapper and RAG module.
"""

import os
from scrapper import scrape_dog_breeds_rkc, save_documents_to_json
from rag_module import get_rag_pipeline

def test_integration():
    print("="*60)
    print("TESTING SCRAPPER + RAG INTEGRATION")
    print("="*60)
    print()
    
    # Step 1: Check if scraped data exists
    data_file = "dog_breeds_rkc.json"
    has_scraped_data = os.path.exists(data_file)
    
    print(f"1. Scraped data file exists: {has_scraped_data}")
    
    if not has_scraped_data:
        print("\n2. Scraping data from Royal Kennel Club...")
        print("   (This will take a minute...)")
        try:
            docs = scrape_dog_breeds_rkc()
            if docs:
                save_documents_to_json(docs, data_file)
                print(f"   ✓ Scraped {len(docs)} breeds successfully")
                has_scraped_data = True
            else:
                print("   ✗ No data scraped. Will use fallback dataset.")
        except Exception as e:
            print(f"   ✗ Error during scraping: {e}")
            print("   Will use fallback dataset.")
    else:
        print("   ✓ Using existing scraped data")
    
    # Step 2: Initialize RAG pipeline
    print(f"\n3. Initializing RAG pipeline (use_scraped_data={has_scraped_data})...")
    try:
        rag = get_rag_pipeline(use_scraped_data=has_scraped_data)
        print("   ✓ RAG pipeline initialized")
    except Exception as e:
        print(f"   ✗ Error initializing RAG: {e}")
        return
    
    # Step 3: Test query
    print("\n4. Testing breed recommendation query...")
    test_query = "I want a dog that is good with kids, has high energy, and doesn't shed much"
    print(f"   Query: '{test_query}'")
    
    try:
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠ Warning: OPENAI_API_KEY not set. Query will fail.")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
            return
        
        answer = rag.answer_question(test_query)
        print("\n   Answer:")
        print("   " + "-"*56)
        for line in answer.split("\n"):
            print(f"   {line}")
        print("   " + "-"*56)
        print("\n   ✓ Query successful!")
        
    except Exception as e:
        print(f"   ✗ Error during query: {e}")
    
    print("\n" + "="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)
    print("\nThe streamlit app is now ready to use!")
    print("Run: streamlit run streamlit_app.py")
    print("="*60)

if __name__ == "__main__":
    test_integration()
