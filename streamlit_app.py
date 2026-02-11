"""
Dog Breed Selector - Streamlit Web Application
===============================================

A Streamlit application that helps users find their perfect dog breed match using:
1. Characteristic-based search (LLM with RAG pipeline)
2. Quiz-based survey (11 questions about lifestyle and preferences)

Both methods use an LLM to analyze user input against dog breed data
and provide personalized breed recommendations.

Main Features:
- Interactive search by characteristics
- 11-question quiz for guided breed selection
- Data scraping controls (fetch fresh Royal Kennel Club data)
- RAG pipeline integration for intelligent recommendations
"""

import streamlit as st
import os
import json
from scrapper import scrape_dog_breeds_rkc, save_documents_to_json
from rag_module import get_rag_pipeline

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Dog Breed Selector",
    page_icon="🐕",
    layout="wide"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
# Streamlit session state persists data across reruns within a single user session

if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False  # Controls whether to display quiz form

if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None  # Cached RAG pipeline instance

if "scraped_data_loaded" not in st.session_state:
    st.session_state.scraped_data_loaded = False  # Tracks if scraped data is loaded


# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("🐕 Dog Breed Selector")
st.write("Find your perfect dog breed match using AI-powered recommendations!")
st.markdown("---")

# ============================================================================
# DATA SOURCE MANAGEMENT
# ============================================================================
# Allows users to scrape fresh breed data from Royal Kennel Club

data_file = "dog_breeds_rkc.json"  # File where scraped breed data is stored
has_scraped_data = os.path.exists(data_file)  # Check if scraped data exists

with st.expander("⚙️ Data Source Settings", expanded=False):
    st.write("**Current Data Status:**")
    
    if has_scraped_data:
        # Scraped data exists - show stats and refresh options
        with open(data_file, "r") as f:
            data = json.load(f)
        
        st.success(f"✓ Using Royal Kennel Club data ({len(data)} breeds)")
        
        col1, col2 = st.columns(2)
        
        # Refresh button: Re-scrape fresh data from Royal Kennel Club
        with col1:
            if st.button("🔄 Refresh Scraped Data"):
                with st.spinner("Scraping fresh breed data from Royal Kennel Club..."):
                    try:
                        docs = scrape_dog_breeds_rkc()
                        if docs:
                            save_documents_to_json(docs, data_file)
                            # Clear cached pipeline so it reloads fresh data
                            st.session_state.scraped_data_loaded = False
                            st.session_state.rag_pipeline = None
                            st.success(f"✓ Successfully scraped {len(docs)} breeds!")
                            st.rerun()
                        else:
                            st.error("Failed to scrape data. Using existing data.")
                    except Exception as e:
                        st.error(f"Error during scraping: {str(e)}")
        
        # Reload button: Clear cache to reload existing data
        with col2:
            if st.button("♻️ Reload RAG Pipeline"):
                st.session_state.rag_pipeline = None
                st.session_state.scraped_data_loaded = False
                st.success("RAG pipeline will be reloaded on next query")
    
    else:
        # No scraped data - show warning and offer to scrape
        st.warning("⚠ No scraped data found. Using built-in fallback dataset (5 breeds)")
        
        if st.button("🌐 Scrape Royal Kennel Club Data"):
            with st.spinner("Scraping from Royal Kennel Club... This may take a minute."):
                try:
                    docs = scrape_dog_breeds_rkc()
                    if docs:
                        save_documents_to_json(docs, data_file)
                        st.session_state.scraped_data_loaded = False
                        st.session_state.rag_pipeline = None
                        st.success(f"✓ Successfully scraped {len(docs)} breeds!")
                        st.rerun()
                    else:
                        st.error("Failed to scrape data. Please try again later.")
                except Exception as e:
                    st.error(f"Error during scraping: {str(e)}")


# ============================================================================
# MAIN APPLICATION: TWO-COLUMN LAYOUT
# ============================================================================
# Left column: Search by characteristics
# Right column: Quiz-based selection

st.markdown("---")
left_col, right_col = st.columns(2)


# ============================================================================
# LEFT COLUMN: SEARCH BY CHARACTERISTICS
# ============================================================================
# User enters desired dog characteristics as free text
# RAG pipeline uses semantic search and LLM to find matching breeds

with left_col:
    st.subheader("🔍 Search by Characteristics")
    
    st.write("Tell us what characteristics you're looking for in a dog:")
    
    # Input field for characteristics
    characteristics = st.text_input(
        "Enter characteristics",
        placeholder="e.g., high energy, good with kids, low shedding, apartment-friendly...",
        help="You can enter multiple traits, separated by commas or spaces"
    )
    
    # Search button
    if st.button("Search breeds"):
        if characteristics:
            # ================================================================
            # Initialize RAG pipeline if not already done
            # ================================================================
            if st.session_state.rag_pipeline is None:
                with st.spinner("Initializing AI recommendation system..."):
                    try:
                        # Load RAG with scraped data if available, otherwise fallback
                        st.session_state.rag_pipeline = get_rag_pipeline(use_scraped_data=has_scraped_data)
                        st.session_state.scraped_data_loaded = has_scraped_data
                    except ValueError as e:
                        # API key validation error
                        st.error(str(e))
                        st.stop()
                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"Error initializing AI system: {error_msg}")
                        if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                            st.warning(
                                "**API Key Issue:**\n\n"
                                "1. Get your key: https://platform.openai.com/account/api-keys\n"
                                "2. Set it in terminal: `export OPENAI_API_KEY='sk-proj-your-key'`\n"
                                "3. Restart Streamlit"
                            )
                        st.stop()
            
            # ================================================================
            # Get AI recommendation from RAG pipeline
            # ================================================================
            with st.spinner("Finding the best breeds for you..."):
                try:
                    # Build question for LLM
                    question = f"I'm looking for a dog with these characteristics: {characteristics}. What breeds would be the best match for me?"
                    
                    # Get recommendation from RAG pipeline
                    answer = st.session_state.rag_pipeline.answer_question(question)
                    
                    # Display results
                    st.success("**Breed Recommendations:**")
                    st.markdown(answer)
                    
                    # Show data source attribution
                    if st.session_state.scraped_data_loaded:
                        st.caption("_Based on Royal Kennel Club breed data_")
                    else:
                        st.caption("_Based on built-in dataset. Scrape more data for better recommendations!_")
                        
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"Error getting recommendation: {error_msg}")
                    if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                        st.warning(
                            "**API Key Issue Detected:**\n\n"
                            "Your OpenAI API key is invalid or not set.\n\n"
                            "**To fix:**\n"
                            "1. Get your key from: https://platform.openai.com/account/api-keys\n"
                            "2. In your terminal, run:\n"
                            "   ```bash\n"
                            "   export OPENAI_API_KEY='sk-proj-your-actual-key'\n"
                            "   ```\n"
                            "3. Restart Streamlit:\n"
                            "   ```bash\n"
                            "   streamlit run streamlit_app.py\n"
                            "   ```"
                        )
                    else:
                        st.info("Troubleshooting: Try restarting Streamlit and check your API key setup.")
        else:
            st.warning("Please enter some characteristics first.")



# ============================================================================
# RIGHT COLUMN: QUIZ-BASED BREED SELECTION
# ============================================================================
# 11-question survey about lifestyle, space, experience, and preferences
# Answers are used to generate a comprehensive profile for the LLM

with right_col:
    st.subheader("📋 Quiz: Find Your Best Fit")
    
    st.write("Answer these questions to get personalized breed recommendations:")
    
    # Toggle quiz display
    if st.button("Take quiz", type="primary", use_container_width=True):
        st.session_state.show_quiz = not st.session_state.show_quiz
    
    # Display quiz form if toggled on
    if st.session_state.show_quiz:
        st.write("**Please answer all questions to get recommendations:**")
        
        # Create form to collect all answers before processing
        with st.form("breed_quiz"):
            
            # Question 1: Living situation
            q1 = st.radio(
                "1. What kind of space do you live in?",
                ["Small House", "Large House", "Flat/Apartment", "Other"],
                key="q1"
            )
            
            # Question 2: Preferred size
            q2 = st.radio(
                "2. What size dog do you prefer?",
                ["Small", "Small-Medium", "Medium", "Large", "Extra Large", "No preference"],
                key="q2"
            )
            
            # Question 3: Grooming frequency
            q3 = st.radio(
                "3. How often are you willing to groom your dog?",
                ["Daily", "Once a week", "More than once a week", "Less often than once a week"],
                key="q3"
            )
            
            # Question 4: Shedding tolerance
            q4 = st.radio(
                "4. Do you mind shedding?",
                ["Yes, I mind shedding", "No, shedding is fine", "No preference"],
                key="q4"
            )
            
            # Question 5: Coat length preference
            q5 = st.radio(
                "5. Do you have a preference for coat length?",
                ["Short", "Medium", "Long", "No preference"],
                key="q5"
            )
            
            # Question 6: Exercise commitment
            q6 = st.radio(
                "6. How much exercise can you give the dog daily?",
                ["30 minutes or less", "1 hour", "2 hours", "More than 2 hours"],
                key="q6"
            )
            
            # Question 7: Other animals
            q7 = st.radio(
                "7. Do you or will you have other animals around the dog?",
                [
                    "No, no other animals",
                    "Yes, I have dogs", 
                    "Yes, I have cats", 
                    "Yes, multiple animals (dogs, cats, etc.)"
                ],
                key="q7"
            )
            
            # Question 8: Children
            q8 = st.radio(
                "8. Do you or will you have children around the dog?",
                ["Yes", "No", "Unsure"],
                key="q8"
            )
            
            # Question 9: Experience level
            q9 = st.radio(
                "9. How much experience do you have with dogs?",
                [
                    "None",
                    "Very little",
                    "Average amount",
                    "A lot of experience",
                    "Very well informed on dog care"
                ],
                key="q9"
            )
            
            # Question 10: Dog type preference (by AKC group)
            q10 = st.radio(
                "10. What type of dog are you looking for?",
                [
                    "Toy", 
                    "Hound", 
                    "Working", 
                    "Gundog", 
                    "Pastoral", 
                    "Utility", 
                    "Unsure/No preference"
                ],
                key="q10"
            )
            
            # Question 11: Lifespan preference
            q11 = st.radio(
                "11. What age range are you interested in?",
                [
                    "Younger (under 8 years typical lifespan)", 
                    "Medium (8-12 years)", 
                    "Longer (over 12 years)",
                    "No preference"
                ],
                key="q11"
            )
            
            # Submit button
            submitted = st.form_submit_button(
                "Get my breed recommendations",
                use_container_width=True,
                type="primary"
            )
        
        # ================================================================
        # Process quiz results
        # ================================================================
        if submitted:
            # Initialize RAG pipeline if not already done
            if st.session_state.rag_pipeline is None:
                with st.spinner("Initializing AI recommendation system..."):
                    try:
                        st.session_state.rag_pipeline = get_rag_pipeline(use_scraped_data=has_scraped_data)
                        st.session_state.scraped_data_loaded = has_scraped_data
                    except ValueError as e:
                        # API key validation error
                        st.error(str(e))
                        st.stop()
                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"Error initializing AI system: {error_msg}")
                        if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                            st.warning(
                                "**API Key Issue:**\n\n"
                                "1. Get your key: https://platform.openai.com/account/api-keys\n"
                                "2. Set it in terminal: `export OPENAI_API_KEY='sk-proj-your-key'`\n"
                                "3. Restart Streamlit"
                            )
                        st.stop()
                        st.stop()
            
            # ================================================================
            # Generate comprehensive profile question for LLM
            # ================================================================
            with st.spinner("Analyzing your profile and finding the best breeds..."):
                try:
                    # Build detailed profile question from all quiz answers
                    profile_question = f"""Based on this person's profile, what dog breeds would be the best match?

LIFESTYLE PROFILE:
- Living space: {q1}
- Preferred size: {q2}
- Grooming frequency: {q3}
- Shedding tolerance: {q4}
- Coat length preference: {q5}
- Daily exercise available: {q6}
- Other animals: {q7}
- Children: {q8}
- Dog experience: {q9}
- Dog type preference: {q10}
- Desired lifespan: {q11}

Please recommend the 2-3 best breed matches with explanations for why they suit this lifestyle."""
                    
                    # Get recommendations from RAG pipeline
                    answer = st.session_state.rag_pipeline.answer_question(profile_question)
                    
                    # Display results
                    st.success("**Your Personalized Breed Recommendations:**")
                    st.markdown(answer)
                    
                    # Show data source attribution
                    if st.session_state.scraped_data_loaded:
                        st.caption("_Based on Royal Kennel Club breed data_")
                    else:
                        st.caption("_Based on built-in dataset. Scrape more data for better recommendations!_")
                        
                except Exception as e:
                    st.error(f"Error getting recommendation: {str(e)}")
                    st.info("Troubleshooting: Make sure OPENAI_API_KEY is set with: `export OPENAI_API_KEY='your-key'`")
