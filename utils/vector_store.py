import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import streamlit as st


# using a small but decent embedding model
# didn't want to use OpenAI embeddings since we're on Gemini
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# chunk size - i tested a few values, 500 worked best for academic text
CHUNK_SIZE = 200
CHUNK_OVERLAP = 50


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """split big text into overlapping chunks so context isn't lost"""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def build_vector_store(documents):
    """
    documents = list of dicts with keys: filename, content_type, text
    returns: faiss index + metadata list
    """
    model = load_embedding_model()
    all_chunks = []
    all_metadata = []

    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "filename": doc["filename"],
                "content_type": doc["content_type"],
                "chunk_index": i,
                "text": chunk
            })

    if not all_chunks:
        return None, []

    # embed everything
    embeddings = model.encode(all_chunks, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    # build faiss index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, all_metadata


def search_vector_store(query, index, metadata, top_k=5):
    """find the most relevant chunks for a given query"""
    if index is None:
        return []

    model = load_embedding_model()
    query_embedding = model.encode([query]).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            result = metadata[idx].copy()
            result["score"] = float(distances[0][i])
            results.append(result)

    return results