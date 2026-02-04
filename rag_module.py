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

class DogBreedRAG:
    def __init__(self, use_scraped_data=False):
        """Initialize the RAG pipeline for dog breed recommendations.

        Args:
            use_scraped_data: If True, load from dog_breeds_rkc.json (from scrapper.py - Royal Kennel Club).
                              If False, use a small built-in dataset as a fallback.
        """
        # Document Store
        self.document_store = InMemoryDocumentStore()
        
        # Load dataset - prioritize Royal Kennel Club data, fall back to built-in data
        if use_scraped_data:
            data_file = None
            if os.path.exists("dog_breeds_rkc.json"):
                data_file = "dog_breeds_rkc.json"
                print("Loading Royal Kennel Club dog breeds data...")
            
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
                use_scraped_data = False
        
        if not use_scraped_data:
            print("Loading built-in breed dataset...")
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
                """You are a warm, friendly assistant that recommends dog breeds based on a user's lifestyle.

Given the following information, answer the question. If the information doesn't directly address the question,
ask a brief follow-up and provide a few reasonable options.

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
        """Get a dog breed recommendation using RAG"""
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
        _rag_instance = DogBreedRAG(use_scraped_data=use_scraped_data)
    return _rag_instance
