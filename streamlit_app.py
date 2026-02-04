import streamlit as st
import os
import json
from scrapper import scrape_dog_breeds_rkc, save_documents_to_json
from rag_module import get_rag_pipeline, reload_rag_pipeline

# Initialize session state
if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "scraped_data_loaded" not in st.session_state:
    st.session_state.scraped_data_loaded = False

st.set_page_config(page_title="Dog Breed Selector")

st.title("Dog Breed Selector")
st.write("Use the tools below to explore dog breeds and find a great match for you.")

# Check for scraped data
data_file = "dog_breeds_rkc.json"
has_scraped_data = os.path.exists(data_file)

# Data source indicator and scraper controls
with st.expander("⚙️ Data Source Settings", expanded=False):
    st.write("**Current Data Status:**")
    if has_scraped_data:
        with open(data_file, "r") as f:
            data = json.load(f)
        st.success(f"✓ Using scraped data from Royal Kennel Club ({len(data)} breeds)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Scraped Data"):
                with st.spinner("Scraping fresh breed data from Royal Kennel Club..."):
                    try:
                        docs = scrape_dog_breeds_rkc()
                        if docs:
                            save_documents_to_json(docs, data_file)
                            st.session_state.scraped_data_loaded = False
                            st.session_state.rag_pipeline = None
                            st.success(f"✓ Successfully scraped {len(docs)} breeds!")
                            st.rerun()
                        else:
                            st.error("Failed to scrape data. Using existing data.")
                    except Exception as e:
                        st.error(f"Error during scraping: {str(e)}")
        
        with col2:
            if st.button("♻️ Reload RAG Pipeline"):
                st.session_state.rag_pipeline = None
                st.session_state.scraped_data_loaded = False
                st.success("RAG pipeline will be reloaded on next query")
    else:
        st.warning("⚠ No scraped data found. Using built-in fallback dataset (5 breeds)")
        if st.button("🌐 Scrape Royal Kennel Club Data"):
            with st.spinner("Scraping breed data from Royal Kennel Club... This may take a minute."):
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

# Two main columns: left = search by characteristics, right = quiz
left_col, right_col = st.columns(2)

# ---------------------------
# LEFT: Search by characteristics
# ---------------------------
with left_col:
    st.subheader("Search by Characteristics")

    st.write("Type the dog characteristics you're looking for:")

    characteristics = st.text_input(
        "Enter characteristics",
        placeholder="e.g., high energy, good with kids, low shedding...",
        help="Separate multiple traits with commas"
    )

    if st.button("Search breeds"):
        if characteristics:
            # Initialize RAG pipeline if not already done
            if st.session_state.rag_pipeline is None:
                with st.spinner("Initializing AI system..."):
                    try:
                        st.session_state.rag_pipeline = get_rag_pipeline(use_scraped_data=has_scraped_data)
                        st.session_state.scraped_data_loaded = has_scraped_data
                    except Exception as e:
                        st.error(f"Error initializing RAG pipeline: {str(e)}")
                        st.stop()
            
            # Get AI recommendation
            with st.spinner("Finding the best breeds for you..."):
                try:
                    question = f"I'm looking for a dog with these characteristics: {characteristics}. What breeds would you recommend?"
                    answer = st.session_state.rag_pipeline.answer_question(question)
                    
                    st.success("**Breed Recommendations:**")
                    st.markdown(answer)
                    
                    # Show data source
                    if st.session_state.scraped_data_loaded:
                        st.caption("_Based on Royal Kennel Club breed data_")
                    else:
                        st.caption("_Based on built-in dataset. Scrape data for more breeds!_")
                        
                except Exception as e:
                    st.error(f"Error getting recommendation: {str(e)}")
                    st.info("Make sure you have set your OPENAI_API_KEY environment variable.")
        else:
            st.warning("Please enter some characteristics first.")

# ---------------------------
# RIGHT: 10-question quiz 
# ---------------------------
with right_col:
    st.subheader("Find Your Best-Fit Breed")

    st.write("Click the button below to take a short quiz and get a breed suggestion.")

    if st.button("Take quiz", type="primary", use_container_width=True):
        st.session_state.show_quiz = True

    if st.session_state.show_quiz:
        st.write("Answer these 10 quick questions to get a recommended breed.")

        with st.form("breed_quiz"):
            q1 = st.radio("What kind of space do you live in?", ["Small House", "Large House", "Flat/Apartment", "Other"])
            q2 = st.radio("What size dog do you prefer?", ["Small", "Small-Medium", "Medium", "Large", "Extra Large", "No preference"])
            q3 = st.radio("How often do you want to groom your dog?", ["Daily", "Once a week", "More than once a week", "Less often than once a week"])
            q4 = st.radio("Do you mind shedding?", ["Yes", "No", "No preference"])
            q5 = st.radio("Do you have a preference for coat length?", ["Short", "Medium", "Long", "No preference"])
            q6 = st.radio("How much exercise can you give the dog daily?", ["30 minutes", "1 hour", "2 hours", "More than 2 hours"])
            q7 = st.radio("Do you or will you have other animals around the dog?", [
                "Yes I have dogs", 
                "Yes I have cats", 
                "Yes I have multiple animals (dogs, cats, etc.)", 
                "Yes I have other animals", 
                "No I do not have other animals"
            ])
            q8 = st.radio("Do you or will you have children around the dog?", ["Yes", "No", "Unsure"])
            q9 = st.radio("How much experience do you have with dogs?", [
                "None",
                "Very little",
                "Average amount",
                "A lot of experience",
                "I am very well informed on how to take care of dogs and what they need to thrive"
            ])
            q10 = st.radio("What type of dog are you looking for?", [
                "Toy", 
                "Hound", 
                "Working", 
                "Gundog", 
                "Pastoral", 
                "Utility", 
                "Unsure/No preference"
            ])
            q11 = st.radio("What age range are you looking for in a dog?", [
                "Less than 10 years", 
                "Over 10 years", 
                "Over 12 years", 
                "No preference"
            ])

            submitted = st.form_submit_button("Get my breed suggestion")

        # Placeholder "result" logic: purely front-end, no real model yet
        if submitted:
            # Initialize RAG pipeline if not already done
            if st.session_state.rag_pipeline is None:
                with st.spinner("Initializing AI system..."):
                    try:
                        st.session_state.rag_pipeline = get_rag_pipeline(use_scraped_data=has_scraped_data)
                        st.session_state.scraped_data_loaded = has_scraped_data
                    except Exception as e:
                        st.error(f"Error initializing RAG pipeline: {str(e)}")
                        st.stop()
            
            # Build a detailed question from quiz answers
            with st.spinner("Analyzing your answers and finding the best breeds..."):
                try:
                    question = f"""Based on this profile, recommend dog breeds:
- Living space: {q1}
- Preferred size: {q2}
- Grooming frequency: {q3}
- Shedding tolerance: {q4}
- Coat length preference: {q5}
- Daily exercise: {q6}
- Other animals: {q7}
- Children: {q8}
- Dog experience: {q9}
- Dog type: {q10}
- Desired lifespan: {q11}

What breeds would be the best match?"""
                    
                    answer = st.session_state.rag_pipeline.answer_question(question)
                    
                    st.success("**Your Personalized Breed Recommendations:**")
                    st.markdown(answer)
                    
                    # Show data source
                    if st.session_state.scraped_data_loaded:
                        st.caption("_Based on Royal Kennel Club breed data_")
                    else:
                        st.caption("_Based on built-in dataset. Scrape data for more breeds!_")
                        
                except Exception as e:
                    st.error(f"Error getting recommendation: {str(e)}")
                    st.info("Make sure you have set your OPENAI_API_KEY environment variable.")
