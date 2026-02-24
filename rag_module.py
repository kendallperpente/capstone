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
    """

    def __init__(self, use_scraped_data=False):
        # ====================================================================
        # VALIDATION: Check for OpenAI API Key
        # ====================================================================
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your-key":
            raise ValueError(
                "OPENAI_API_KEY not set or invalid. "
                "Set it with: export OPENAI_API_KEY='sk-proj-your-actual-key'"
            )

        # ====================================================================
        # STEP 1: Initialize Document Store
        # ====================================================================
        self.document_store = InMemoryDocumentStore()

        # ====================================================================
        # STEP 2: Load Dataset
        # ====================================================================
        docs = []

        if use_scraped_data and os.path.exists("dog_breeds_rkc.json"):
            print("✓ Loading Royal Kennel Club dog breeds data...")
            with open("dog_breeds_rkc.json", "r") as f:
                data = json.load(f)
            docs = [
                Document(
                    content=item["content"],
                    meta={
                        "title": item.get("title", "Unknown"),
                        "url": item.get("url", ""),
                        "source": item.get("source", "Scraped"),
                    }
                )
                for item in data
            ]
        else:
            if use_scraped_data:
                print("⚠ No scraped data found. Falling back to built-in dataset.")
            else:
                print("✓ Loading built-in breed dataset...")

            fallback_data = [
                {
                    "title": "Labrador Retriever",
                    "content": "Friendly, outgoing, and high-energy. Great for active families and training, "
                               "needs daily exercise and enjoys retrieving games.",
                    "source": "Built-in",
                },
                {
                    "title": "Golden Retriever",
                    "content": "Affectionate, patient, and eager to please. Excellent with kids, "
                               "requires regular grooming and lots of activity.",
                    "source": "Built-in",
                },
                {
                    "title": "French Bulldog",
                    "content": "Compact, calm, and good for apartment living. Moderate exercise needs, "
                               "sensitive to heat and benefits from short walks.",
                    "source": "Built-in",
                },
                {
                    "title": "Poodle (Standard)",
                    "content": "Highly intelligent and trainable. Low-shedding coat but needs regular grooming, "
                               "enjoys mental and physical activity.",
                    "source": "Built-in",
                },
                {
                    "title": "Beagle",
                    "content": "Curious, friendly, and social. Moderate exercise needs, "
                               "can be vocal and enjoys scent games.",
                    "source": "Built-in",
                },
            ]
            docs = [
                Document(
                    content=item["content"],
                    meta={"title": item["title"], "source": item["source"]}
                )
                for item in fallback_data
            ]

        # ====================================================================
        # STEP 3: Create Embeddings for Documents
        # ====================================================================
        doc_embedder = SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        doc_embedder.warm_up()
        docs_with_embeddings = doc_embedder.run(docs)
        self.document_store.write_documents(docs_with_embeddings["documents"])

        # ====================================================================
        # STEP 4: Initialize Text Embedder for User Queries
        # ====================================================================
        self.text_embedder = SentenceTransformersTextEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )

        # ====================================================================
        # STEP 5: Create Retriever — top_k=5 so we consider multiple breeds
        # ====================================================================
        self.retriever = InMemoryEmbeddingRetriever(
            self.document_store,
            top_k=5  # BUG FIX: was defaulting to 1, so only 1 breed was ever considered
        )

        # ====================================================================
        # STEP 6: Create LLM Prompt Template
        # ====================================================================
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

        self.prompt_builder = ChatPromptBuilder(template=template)

        # ====================================================================
        # STEP 7: Initialize Chat Generator (LLM)
        # ====================================================================
        self.chat_generator = OpenAIChatGenerator(model="gpt-4o-mini")

        # ====================================================================
        # STEP 8: Build the Pipeline
        # BUG FIX: Use explicit "retriever.documents" -> "prompt_builder.documents"
        # instead of ambiguous "retriever" -> "prompt_builder"
        # ====================================================================
        self.pipeline = Pipeline()

        self.pipeline.add_component("text_embedder", self.text_embedder)
        self.pipeline.add_component("retriever", self.retriever)
        self.pipeline.add_component("prompt_builder", self.prompt_builder)
        self.pipeline.add_component("llm", self.chat_generator)

        self.pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.pipeline.connect("retriever.documents", "prompt_builder.documents")  # BUG FIX: explicit output slot
        self.pipeline.connect("prompt_builder.prompt", "llm.messages")

    def answer_question(self, question: str) -> str:
        """Get a dog breed recommendation using the RAG pipeline."""
        response = self.pipeline.run({
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question},
        })
        return response["llm"]["replies"][0].text


# ============================================================================
# NOTE: The module-level singleton (_rag_instance global) has been removed.
# Streamlit reruns the entire script on every interaction, so module-level
# globals reset and are unreliable. Use st.session_state in the app instead
# (which is already done correctly in streamlit_app.py).
# ============================================================================

def get_rag_pipeline(use_scraped_data=False) -> DogBreedRAG:
    """
    Create a new RAG pipeline instance.
    Caching is handled by st.session_state in the Streamlit app.
    """
    return DogBreedRAG(use_scraped_data=use_scraped_data)


def reload_rag_pipeline(use_scraped_data=False) -> DogBreedRAG:
    """Force-create a fresh RAG pipeline instance."""
    return DogBreedRAG(use_scraped_data=use_scraped_data)
