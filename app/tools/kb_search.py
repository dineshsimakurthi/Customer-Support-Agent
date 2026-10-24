"""Vector search over the knowledge base (ChromaDB + MiniLM embeddings).

Plug your existing RAG project in here: keep the kb_search() signature and the
rest of the agent does not change.
"""
from functools import lru_cache
from typing import Optional

from app import config


@lru_cache(maxsize=1)
def _store():
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(config.VECTORSTORE_DIR),
    )


def kb_search(query: str, category: Optional[str] = None,
              doc_type: Optional[str] = None, k: int = 3) -> list[dict]:
    conditions = []
    if category:
        conditions.append({"category": category})
    if doc_type:
        conditions.append({"type": doc_type})
    flt = None
    if len(conditions) == 1:
        flt = conditions[0]
    elif len(conditions) > 1:
        flt = {"$and": conditions}

    results = _store().similarity_search_with_relevance_scores(query, k=k, filter=flt)
    return [
        {
            "content": d.page_content,
            "source": d.metadata.get("source", "unknown"),
            "type": d.metadata.get("type", ""),
            "category": d.metadata.get("category", ""),
            "score": round(float(s), 3),
        }
        for d, s in results
    ]
