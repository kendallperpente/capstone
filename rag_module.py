"""
RAG (Retrieval-Augmented Generation) Pipeline for Dog Breed Recommendations
==============================================================================

This module implements a Retrieval-Augmented Generation pipeline that:
1. Loads dog breed information from JSON (scraped by scrapper.py)
2. Embeds the breed data using sentence transformers
3. Retrieves relevant breeds based on user queries
4. Uses OpenAI's GPT model to generate personalized breed recommendations

The pipeline combines retrieval (finding relevant breeds) with generation
(creating personalized responses) to provide accurate, context-aware recommendations.

Classes:
- DogBreedRAG: Main RAG pipeline class

Functions:
- get_rag_pipeline(): Get or create RAG instance (singleton pattern)
- reload_rag_pipeline(): Force rebuild of RAG instance
"""

import os
import json
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack import Document, Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder, 
    SentenceTransformersTextEmbedder
)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator


class DogBreedRAG:
    """
    Retrieval-Augmented Generation pipeline for dog breed recommendations.
    
    This class:
    1. Loads breed data (from scraper.py JSON or built-in fallback)
    2. Creates embeddings for semantic search
    3. Sets up retrieval and LLM components
    4. Orchestrates recommendation generation
    """
    
    def __init__(self, use_scraped_data=False):
        """
        Initialize the RAG pipeline for dog breed recommendations.

        Args:
            use_scraped_data (bool): If True, load from dog_breeds_rkc.json (scraped data).
                                    If False, use small built-in dataset as fallback.
        """
        # ========================================================================
        # VALIDATION: Check for OpenAI API Key
        # ========================================================================
        # The LLM component requires a valid OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your-key":
            raise ValueError(
                "❌ OPENAI_API_KEY not set or invalid!\n\n"
                "To fix this:\n"
                "1. Get your API key from: https://platform.openai.com/account/api-keys\n"
                "2. Set it in your terminal:\n"
                "   export OPENAI_API_KEY='sk-proj-your-actual-key'\n"
                "3. Restart Streamlit:\n"
                "   streamlit run streamlit_app.py\n\n"
                f"Current value: {api_key[:20]}..." if api_key else "Not set"
            )
        
        # ========================================================================
        # STEP 1: Initialize Document Store
        # ========================================================================
        # In-memory document store for fast, lightweight operations
        self.document_store = InMemoryDocumentStore()
        
        # ========================================================================
        # STEP 2: Load Dataset - Scraped Data First, Then Fallback
        # ========================================================================
        
        if use_scraped_data:
            data_file = None
            # Check if scraped data file exists
            if os.path.exists("dog_breeds_rkc.json"):
                data_file = "dog_breeds_rkc.json"
                print("✓ Loading Royal Kennel Club dog breeds data...")
            
            # Load from scraped JSON file if it exists
            if data_file:
                with open(data_file, "r") as f:
                    data = json.load(f)
                docs = [
                    Document(
                        content=item["content"],
                        meta={
                            "title": item.get("title", "Unknown"),
                            "url": item.get("url", ""),
                            "source": item.get("source", "Scraped")
                        }
                    )
                    for item in data
                ]
            else:
                print("⚠ No scraped data found. Falling back to built-in dataset.")
                use_scraped_data = False  # Use fallback instead
        
        # ========================================================================
        # STEP 2B: Fallback Dataset (if scraped data not available or not requested)
        # ========================================================================
        
        if not use_scraped_data:
            print("✓ Loading built-in breed dataset...")
            # Small dataset to provide basic functionality without scraping
            fallback_data = [
                {
                    "title": "Labrador Retriever",
                    "content": "Friendly, outgoing, and high-energy. Great for active families and training,"
                               " needs daily exercise and enjoys retrieving games.",
                    "source": "Built-in"
                },
                {
                    "title": "Golden Retriever",
                    "content": "Affectionate, patient, and eager to please. Excellent with kids,"
                               " requires regular grooming and lots of activity.",
                    "source": "Built-in"
                },
                {
                    "title": "French Bulldog",
                    "content": "Compact, calm, and good for apartment living. Moderate exercise needs,"
                               " sensitive to heat and benefits from short walks.",
                    "source": "Built-in"
                },
                {
                    "title": "Poodle (Standard)",
                    "content": "Highly intelligent and trainable. Low-shedding coat but needs regular grooming,"
                               " enjoys mental and physical activity.",
                    "source": "Built-in"
                },
                {
                    "title": "Beagle",
                    "content": "Curious, friendly, and social. Moderate exercise needs,"
                               " can be vocal and enjoys scent games.",
                    "source": "Built-in"
                },
            ]
            docs = [
                Document(content=item["content"], meta={"title": item["title"], "source": item["source"]})
                for item in fallback_data
            ]
        
        # ========================================================================
        # STEP 3: Create Embeddings for Documents
        # ========================================================================
        # Uses sentence transformers to convert text to vectors for semantic search
        doc_embedder = SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        doc_embedder.warm_up()  # Initialize the model
        docs_with_embeddings = doc_embedder.run(docs)
        # Store documents in document store for retrieval
        self.document_store.write_documents(docs_with_embeddings["documents"])
        
        # ========================================================================
        # STEP 4: Initialize Text Embedder for User Queries
        # ========================================================================
        self.text_embedder = SentenceTransformersTextEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # ========================================================================
        # STEP 5: Create Retriever Component
        # ========================================================================
        # Retriever finds the most relevant breed documents based on user query
        self.retriever = InMemoryEmbeddingRetriever(self.document_store)
        
        # ========================================================================
        # STEP 6: Create LLM Prompt Template
        # ========================================================================
        # This template defines how the LLM should format its response
        template = [
            ChatMessage.from_user(
                """You are a warm, friendly assistant that recommends dog breeds based on a user's lifestyle.

TASK: Based on the breed information provided, answer the user's question.

INSTRUCTIONS:
- Provide 1-3 breed recommendations with brief explanations
- Each recommendation should list 2-4 key reasons why it's suitable
- Consider the user's lifestyle, space, energy level, and preferences
- If information doesn't directly address the question, make reasonable inferences
- Be personable and encouraging

BREED INFORMATION:
{% for document in documents %}
- {{ document.meta['title'] }}: {{ document.content }}
{% endfor %}

USER QUESTION: {{question}}

RESPONSE:"""
            )
        ]
        
        # Initialize prompt builder that combines documents with the template
        self.prompt_builder = ChatPromptBuilder(template=template)
        
        # ========================================================================
        # STEP 7: Initialize Chat Generator (LLM)
        # ========================================================================
        # Uses OpenAI's GPT model to generate recommendations
        # Requires OPENAI_API_KEY environment variable
        self.chat_generator = OpenAIChatGenerator(model="gpt-4o-mini")
        
        # ========================================================================
        # STEP 8: Build the Pipeline (Connect Components)
        # ========================================================================
        # Pipeline orchestrates the flow: Query -> Embed -> Retrieve -> Prompt -> Generate
        self.pipeline = Pipeline()
        
        # Add components to pipeline
        self.pipeline.add_component("text_embedder", self.text_embedder)
        self.pipeline.add_component("retriever", self.retriever)
        self.pipeline.add_component("prompt_builder", self.prompt_builder)
        self.pipeline.add_component("llm", self.chat_generator)
        
        # Connect components in sequence
        self.pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.pipeline.connect("retriever", "prompt_builder")
        self.pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    def answer_question(self, question: str) -> str:
        """
        Get a dog breed recommendation using the RAG pipeline.
        
        This method:
        1. Converts the question to an embedding vector
        2. Retrieves relevant breed documents
        3. Downloads and builds prompt with documents
        4. Sends to LLM for personalized response
        
        Args:
            question (str): The user's question about dog breeds
            
        Returns:
            str: LLM-generated breed recommendation response
        """
        # Run the pipeline with the user's question
        response = self.pipeline.run({
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question}
        })
        
        # Extract and return the text response from the LLM
        return response["llm"]["replies"][0].text


# ============================================================================
# SINGLETON PATTERN: Manage RAG Instance to Avoid Recreating Each Query
# ============================================================================

# Global variables to cache RAG instance
_rag_instance = None  # Stores the RAG instance
_rag_instance_use_scraped = None  # Tracks which data type the instance uses


def get_rag_pipeline(use_scraped_data=False):
    """
    Get or create the RAG pipeline instance (singleton pattern).
    
    This function ensures only one RAG instance exists, improving performance
    by avoiding redundant initialization of embeddings and models.
    
    Args:
        use_scraped_data (bool): Load from scraped breed data if True.
                                If instance exists with different setting,
                                it will be recreated.
    
    Returns:
        DogBreedRAG: The RAG pipeline instance
    """
    global _rag_instance, _rag_instance_use_scraped
    
    # Create new instance if:
    # 1. No instance exists yet, OR
    # 2. Switching between scraped/built-in data
    if _rag_instance is None or _rag_instance_use_scraped != use_scraped_data:
        _rag_instance = DogBreedRAG(use_scraped_data=use_scraped_data)
        _rag_instance_use_scraped = use_scraped_data
    
    return _rag_instance


def reload_rag_pipeline(use_scraped_data=False):
    """
    Force rebuild of the RAG pipeline instance (clears cache).
    
    Use this when you want to reload fresh data from disk
    (e.g., after scraping new breed data).
    
    Args:
        use_scraped_data (bool): Load from scraped breed data if True
        
    Returns:
        DogBreedRAG: The newly created RAG pipeline instance
    """
    global _rag_instance, _rag_instance_use_scraped
    
    # Force create new instance regardless of current state
    _rag_instance = DogBreedRAG(use_scraped_data=use_scraped_data)
    _rag_instance_use_scraped = use_scraped_data
    
    return _rag_instance
