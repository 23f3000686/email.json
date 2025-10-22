from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Initialize FastAPI app
app = FastAPI(title="InfoCore Semantic Search API")

# Enable CORS (allowing all origins, headers, and POST/OPTIONS methods)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict later)
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Define request body schema
class SimilarityRequest(BaseModel):
    docs: List[str]
    query: str

# Function to compute cosine similarity
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Define /similarity endpoint
@app.post("/similarity")
async def get_similarity(data: SimilarityRequest):
    # Generate embeddings for all docs + query
    texts = data.docs + [data.query]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    embeddings = [np.array(e.embedding) for e in response.data]
    doc_embeddings = embeddings[:-1]
    query_embedding = embeddings[-1]

    # Compute similarity scores
    similarities = [cosine_similarity(doc_emb, query_embedding) for doc_emb in doc_embeddings]

    # Rank documents by similarity (descending)
    ranked_indices = np.argsort(similarities)[::-1]
    top_indices = ranked_indices[:3]

    # Prepare ranked matches
    top_matches = [data.docs[i] for i in top_indices]

    return {"matches": top_matches}
