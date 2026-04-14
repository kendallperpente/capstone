"""
rag_module.py — RAG pipeline for dog breed recommendations
===========================================================
Imported by:  streamlit_app.py  (as `from rag_module import get_rag_pipeline`)
              run_batch_qa.py

CHANGES:
- DogBreedRAG.__init__ now accepts an optional `api_key` parameter.
  The Streamlit app passes the key entered in the sidebar; this fix ensures
  it actually reaches the OpenAI client instead of being silently ignored.
- get_rag_pipeline() and reload_rag_pipeline() both forward api_key.
"""

import os
import json
from typing import List, Optional

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
    {
        "title": "German Shepherd",
        "content": (
            "Loyal, confident, and highly intelligent. Excellent working dog and family protector, "
            "needs plenty of exercise and mental stimulation."
        ),
        "source": "Built-in",
    },
    {
        "title": "Bulldog",
        "content": (
            "Calm, courageous, and friendly. Low exercise needs, good for apartments, "
            "prone to breathing issues due to flat face."
        ),
        "source": "Built-in",
    },
    {
        "title": "Siberian Husky",
        "content": (
            "Energetic, mischievous, and loyal. Bred for cold climates, "
            "needs lots of exercise and has a thick double coat."
        ),
        "source": "Built-in",
    },
    {
        "title": "Rottweiler",
        "content": (
            "Loyal, loving, and confident guardian. Powerful and protective, "
            "requires firm training and regular exercise."
        ),
        "source": "Built-in",
    },
    {
        "title": "Border Collie",
        "content": (
            "Extremely intelligent and energetic. Originally bred for herding sheep in Scotland, "
            "needs a job to do and lots of mental and physical stimulation."
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
        Falls back to the built-in dataset if the file is missing.
    data_file : str
        Path to the scraped JSON file (default: ``dog_breeds_rkc.json``).
    api_key : str, optional
        OpenAI API key. If provided, takes precedence over the OPENAI_API_KEY
        environment variable. This is the key entered in the Streamlit sidebar.
    """

    def __init__(
        self,
        use_scraped_data: bool = False,
        data_file: str = "dog_breeds_rkc.json",
        api_key: Optional[str] = None,
    ):
        # ── Resolve and validate API key ─────────────────────────────────
        # Prefer the explicitly-passed key (from Streamlit sidebar),
        # fall back to the environment variable.
        resolved_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not resolved_key or resolved_key.startswith("your-key"):
            raise ValueError(
                "OPENAI_API_KEY not set or invalid. "
                "Either set it with: export OPENAI_API_KEY='sk-proj-your-actual-key' "
                "or enter it in the Streamlit sidebar."
            )
        # Write it back to the environment so Haystack's OpenAIChatGenerator
        # picks it up automatically (it reads os.environ internally).
        os.environ["OPENAI_API_KEY"] = resolved_key

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

        # ── Retriever ────────────────────────────────────────────────────
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
    api_key: Optional[str] = None,
) -> DogBreedRAG:
    """
    Create and return a new DogBreedRAG instance.

    Parameters
    ----------
    use_scraped_data : bool
        Load from dog_breeds_rkc.json if True, else use built-in fallback.
    data_file : str
        Path to the scraped JSON.
    api_key : str, optional
        OpenAI API key. Passed through from the Streamlit sidebar so the
        user-entered key is actually used rather than silently ignored.

    Caching across Streamlit reruns is handled by st.session_state
    in streamlit_app.py — do not cache here.
    """
    return DogBreedRAG(
        use_scraped_data=use_scraped_data,
        data_file=data_file,
        api_key=api_key,
    )


def reload_rag_pipeline(
    use_scraped_data: bool = False,
    data_file: str = "dog_breeds_rkc.json",
    api_key: Optional[str] = None,
) -> DogBreedRAG:
    """Force-create a fresh pipeline instance (convenience alias)."""
    return DogBreedRAG(
        use_scraped_data=use_scraped_data,
        data_file=data_file,
        api_key=api_key,
    )
