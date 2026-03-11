"""
rag.py — thin shim so dog_breed_pipeline.py can use `from rag import get_rag_pipeline`
while streamlit_app.py uses `from rag_module import get_rag_pipeline`.

Both names resolve to the same implementation in rag_module.py.
"""

from rag_module import DogBreedRAG, get_rag_pipeline, reload_rag_pipeline

__all__ = ["DogBreedRAG", "get_rag_pipeline", "reload_rag_pipeline"]