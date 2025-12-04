# rag_module.py - RAG Pipeline as a reusable module

import os
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
import json

class DogHealthRAG:
    def __init__(self, use_scraped_data=False):
        """Initialize the RAG pipeline for dog health questions
        
        Args:
            use_scraped_data: If True, load from dog_diseases.json (from scrapper.py)
                             If False, use the default seven-wonders dataset
        """
        # Document Store
        self.document_store = InMemoryDocumentStore()
        
        # Load dataset
        if use_scraped_data and os.path.exists("dog_diseases.json"):
            print("Loading scraped dog diseases data...")
            with open("dog_diseases.json", "r") as f:
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
            print("Loading default dataset...")
            from datasets import load_dataset
            dataset = load_dataset("bilgeyucel/seven-wonders", split="train")
            docs = [Document(content=doc["content"], meta=doc["meta"]) for doc in dataset]
        
        # Document Embedder
        doc_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        doc_embedder.warm_up()
        docs_with_embeddings = doc_embedder.run(docs)
        self.document_store.write_documents(docs_with_embeddings["documents"])
        
        # Text Embedder
        self.text_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        
        # Retriever
        self.retriever = InMemoryEmbeddingRetriever(self.document_store)
        
        # Prompt Template
        template = [
            ChatMessage.from_user(
                """You are a warm, friendly assistant specialized in dog (canine) health and basic first aid.

Given the following information, answer the question. If the information doesn't directly address the question, 
provide general guidance while emphasizing this is educational only and not a substitute for veterinary care.

Context:
{% for document in documents %}
    {{ document.content }}
{% endfor %}

Question: {{question}}
Answer:"""
            )
        ]
        
        self.prompt_builder = ChatPromptBuilder(template=template)
        
        # Chat Generator
        self.chat_generator = OpenAIChatGenerator(model="gpt-4o-mini")
        
        # Build Pipeline
        self.pipeline = Pipeline()
        self.pipeline.add_component("text_embedder", self.text_embedder)
        self.pipeline.add_component("retriever", self.retriever)
        self.pipeline.add_component("prompt_builder", self.prompt_builder)
        self.pipeline.add_component("llm", self.chat_generator)
        self.pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.pipeline.connect("retriever", "prompt_builder")
        self.pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    def answer_question(self, question: str) -> str:
        """Get an answer to a dog health question using RAG"""
        response = self.pipeline.run({
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question}
        })
        return response["llm"]["replies"][0].text

# Initialize once
_rag_instance = None

def get_rag_pipeline(use_scraped_data=False):
    """Get or create the RAG pipeline instance (singleton)
    
    Args:
        use_scraped_data: Load from scraped Wikipedia data if True
    """
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = DogHealthRAG(use_scraped_data=use_scraped_data)
    return _rag_instance
