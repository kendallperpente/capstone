"""
rag_module.py — RAG pipeline for dog breed recommendations
===========================================================
Imported by:  streamlit_app.py  (as `from rag_module import get_rag_pipeline`)
              dog_breed_pipeline.py (as `from rag import get_rag_pipeline`)
              → rag.py is a one-line shim that re-exports from here.
"""

import os
import json
from typing import List

from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack import Document, Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator

# ---------------------------------------------------------------------------
# Fallback built-in dataset (used when no scraped JSON exists)
# ---------------------------------------------------------------------------

FALLBACK_BREEDS: List[dict] = [
    {
        "title": "Labrador Retriever",
        "content": (
            "Friendly, outgoing, and high-energy. Great for active families and training, "
            "needs daily exercise and enjoys retrieving games."
        ),
        "source": "Built-in",
    },
    {
        "title": "Golden Retriever",
        "content": (
            "Affectionate, patient, and eager to please. Excellent with kids, "
            "requires regular grooming and lots of activity."
        ),
        "source": "Built-in",
    },
    {
        "title": "French Bulldog",
        "content": (
            "Compact, calm, and good for apartment living. Moderate exercise needs, "
            "sensitive to heat and benefits from short walks."
        ),
        "source": "Built-in",
    },
    {
        "title": "Poodle (Standard)",
        "content": (
            "Highly intelligent and trainable. Low-shedding coat but needs regular grooming, "
            "enjoys mental and physical activity."
        ),
        "source": "Built-in",
    },
    {
        "title": "Beagle",
        "content": (
            "Curious, friendly, and social. Moderate exercise needs, "
            "can be vocal and enjoys scent games."
        ),
        "source": "Built-in",
    },
]

# ---------------------------------------------------------------------------
# RAG Pipeline class
# ---------------------------------------------------------------------------

class DogBreedRAG:
    """
    Retrieval-Augmented Generation pipeline for dog breed recommendations.

    Parameters
    ----------
    use_scraped_data : bool
        If True, load breed data from ``dog_breeds_rkc.json``.
        Falls back to the built-in 5-breed dataset if the file is missing.
    data_file : str
        Path to the scraped JSON file (default: ``dog_breeds_rkc.json``).
    """

    def __init__(
        self,
        use_scraped_data: bool = False,
        data_file: str = "dog_breeds_rkc.json",
    ):
        # ── Validate API key ─────────────────────────────────────────────
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key.startswith("your-key"):
            raise ValueError(
                "OPENAI_API_KEY not set or invalid. "
                "Set it with: export OPENAI_API_KEY='sk-proj-your-actual-key'"
            )

        # ── Load documents ───────────────────────────────────────────────
        docs: List[Document] = []

        if use_scraped_data and os.path.exists(data_file):
            print(f"✓ Loading Royal Kennel Club data from '{data_file}'...")
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            docs = [
                Document(
                    content=item["content"],
                    meta={
                        "title": item.get("title", "Unknown"),
                        "url": item.get("url", ""),
                        "source": item.get("source", "Royal Kennel Club"),
                    },
                )
                for item in data
            ]
        else:
            if use_scraped_data:
                print(f"⚠  '{data_file}' not found — falling back to built-in dataset.")
            else:
                print("✓ Loading built-in breed dataset...")
            docs = [
                Document(
                    content=item["content"],
                    meta={"title": item["title"], "source": item["source"]},
                )
                for item in FALLBACK_BREEDS
            ]

        # ── Build document store ─────────────────────────────────────────
        self.document_store = InMemoryDocumentStore()

        doc_embedder = SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        doc_embedder.warm_up()
        docs_with_embeddings = doc_embedder.run(docs)
        self.document_store.write_documents(docs_with_embeddings["documents"])

        # ── Query embedder ───────────────────────────────────────────────
        self.text_embedder = SentenceTransformersTextEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )

        # ── Retriever — top 5 so we always have multiple breed candidates ─
        self.retriever = InMemoryEmbeddingRetriever(
            self.document_store,
            top_k=5,
        )

        # ── Prompt template ──────────────────────────────────────────────
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

        # ── LLM ──────────────────────────────────────────────────────────
        self.chat_generator = OpenAIChatGenerator(model="gpt-4o-mini")

        # ── Wire the pipeline ─────────────────────────────────────────────
        self.pipeline = Pipeline()
        self.pipeline.add_component("text_embedder", self.text_embedder)
        self.pipeline.add_component("retriever", self.retriever)
        self.pipeline.add_component("prompt_builder", self.prompt_builder)
        self.pipeline.add_component("llm", self.chat_generator)

        self.pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.pipeline.connect("retriever.documents", "prompt_builder.documents")
        self.pipeline.connect("prompt_builder.prompt", "llm.messages")

    def answer_question(self, question: str) -> str:
        """Run the RAG pipeline and return the LLM's answer as a string."""
        response = self.pipeline.run(
            {
                "text_embedder": {"text": question},
                "prompt_builder": {"question": question},
            }
        )
        return response["llm"]["replies"][0].text


# ---------------------------------------------------------------------------
# Public factory functions
# ---------------------------------------------------------------------------

def get_rag_pipeline(
    use_scraped_data: bool = False,
    data_file: str = "dog_breeds_rkc.json",
) -> DogBreedRAG:
    """
    Create and return a new DogBreedRAG instance.
    Caching across Streamlit reruns is handled by ``st.session_state``
    in streamlit_app.py — do not cache here.
    """
    return DogBreedRAG(use_scraped_data=use_scraped_data, data_file=data_file)


def reload_rag_pipeline(
    use_scraped_data: bool = False,
    data_file: str = "dog_breeds_rkc.json",
) -> DogBreedRAG:
    """Force-create a fresh pipeline instance (convenience alias)."""
    return DogBreedRAG(use_scraped_data=use_scraped_data, data_file=data_file)