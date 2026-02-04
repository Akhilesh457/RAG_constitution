"""
Step 4 & 5: Generate Embeddings and Store in FAISS Vector Database
Uses SentenceTransformers for embeddings
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from typing import List, Dict
from tqdm import tqdm

class ConstitutionVectorDB:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize vector database
        
        Args:
            model_name: SentenceTransformer model
                - 'all-MiniLM-L6-v2' (fast, 384 dim)
                - 'all-mpnet-base-v2' (better quality, 768 dim)
                - 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' (multilingual)
        """
        print(f"🔧 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"   Embedding dimension: {self.dimension}")
        
        self.index = None
        self.chunks = []
        self.metadata = []
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for all chunks
        """
        print(f"\n🧮 Generating embeddings for {len(chunks)} chunks...")
        
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings with progress bar
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        print(f"✅ Generated embeddings shape: {embeddings.shape}")
        return embeddings
    
    def build_index(self, chunks: List[Dict]):
        """
        Build FAISS index from chunks
        """
        print("\n🏗️  Building FAISS index...")
        
        # Store chunks and metadata
        self.chunks = chunks
        self.metadata = [chunk['metadata'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Create FAISS index
        # Using IndexFlatL2 for exact search (good for <100k vectors)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to index
        self.index.add(embeddings.astype('float32'))
        
        print(f"✅ Index built with {self.index.ntotal} vectors")
    
    def save_index(self, index_path: str = 'constitution_faiss.index', 
                   metadata_path: str = 'constitution_metadata.pkl'):
        """Save FAISS index and metadata"""
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        print(f"💾 Saved FAISS index to {index_path}")
        
        # Save metadata and chunks
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'dimension': self.dimension
            }, f)
        print(f"💾 Saved metadata to {metadata_path}")
    
    def load_index(self, index_path: str = 'constitution_faiss.index',
                   metadata_path: str = 'constitution_metadata.pkl'):
        """Load existing FAISS index and metadata"""
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        print(f"📂 Loaded FAISS index: {self.index.ntotal} vectors")
        
        # Load metadata
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
            self.dimension = data['dimension']
        print(f"📂 Loaded metadata: {len(self.chunks)} chunks")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for top-k most similar chunks
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of dicts with chunk, metadata, and score
        """
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search in FAISS
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Prepare results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            results.append({
                'chunk': self.chunks[idx],
                'metadata': self.metadata[idx],
                'score': float(dist),
                'similarity': 1 / (1 + float(dist))  # Convert distance to similarity
            })
        
        return results
    
    def test_search(self, test_queries: List[str]):
        """Test search with sample queries"""
        print("\n🔍 Testing search...")
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = self.search(query, k=3)
            
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] {result['metadata']['article_number']}")
                print(f"      Similarity: {result['similarity']:.3f}")
                print(f"      {result['chunk']['text'][:150]}...")

# Usage Example
if __name__ == "__main__":
    # Load chunks from step 3
    with open('constitution_chunks.json', 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # Initialize vector DB
    vector_db = ConstitutionVectorDB(model_name='all-MiniLM-L6-v2')
    
    # Build index
    vector_db.build_index(chunks)
    
    # Save index
    vector_db.save_index()
    
    # Test searches
    test_queries = [
        "What is Article 21?",
        "Right to equality",
        "Fundamental rights",
        "Can Parliament amend the Constitution?",
        "Freedom of speech"
    ]
    
    vector_db.test_search(test_queries)
