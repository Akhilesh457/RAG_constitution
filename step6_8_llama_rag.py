"""
Step 6-8: Groq Cloud Integration with RAG Pipeline
Optimized for CitizenQuery.streamlit.app
UPDATED: Uses current Groq models (Feb 2026)
"""

from typing import List, Dict
import json
import requests
import streamlit as st

class ConstitutionRAG:
    def __init__(self, vector_db, llm_type: str = 'ollama', model_path: str = None):
        """
        Initialize RAG system targeting Groq Cloud
        """
        self.vector_db = vector_db
        self.llm_type = llm_type # We keep this as 'ollama' to avoid breaking other files
        
        # Groq Cloud Settings - UPDATED to use current models
        # Options as of Feb 2026:
        # - "llama-3.3-70b-versatile" (RECOMMENDED - Fast & High Quality)
        # - "llama-3.1-70b-versatile" (Alternative)
        # - "mixtral-8x7b-32768" (Good for long context)
        # - "llama-3.1-8b-instant" (Fastest, smaller model)
        
        self.model_name = "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Retrieve API Key safely
        try:
            self.api_key = st.secrets["GROQ_API_KEY"]
        except:
            # Fallback for local testing only (NEVER commit real API keys!)
            self.api_key = "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"

    def retrieve_context(self, query: str, k: int = 3) -> tuple[List[Dict], str]:
        """Retrieve relevant chunks and format for LLM"""
        results = self.vector_db.search(query, k=k)
        
        context_parts = []
        for i, result in enumerate(results, 1):
            article = result['metadata'].get('article_number', 'Unknown Article')
            text = result['chunk'].get('text', '')
            context_parts.append(f"[Source {i}] {article}\n{text}\n")
        
        formatted_context = "\n".join(context_parts)
        return results, formatted_context
    
    def create_prompt(self, query: str, context: str) -> str:
        """Create structured prompt for legal accuracy"""
        return f"""You are a legal assistant specializing in the Indian Constitution.

INSTRUCTIONS:
1. Answer the question using ONLY the provided context.
2. If the answer is not in the context, say "This information is not found in the provided Constitutional text."
3. Always cite the Article number (e.g., "According to Article 21...").
4. Keep the tone professional and factual.

CONTEXT FROM CONSTITUTION:
{context}

QUESTION:
{query}

ANSWER:"""

    def generate_answer(self, prompt: str) -> str:
        """Generate answer using Groq Cloud API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Groq expects 'messages' format, not a raw string prompt
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a legal assistant specializing in the Indian Constitution."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                # Extracting the content from Groq's JSON response structure
                return response.json()['choices'][0]['message']['content'].strip()
            elif response.status_code == 401:
                return "Error 401: Invalid API Key. Check your Streamlit Secrets."
            elif response.status_code == 400:
                error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                return f"Error 400: {error_detail}\n\nTip: Check if the model name is correct in step6_8_llama_rag.py"
            else:
                return f"Groq Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Cloud Connection Error: {str(e)}"

    def query(self, question: str, k: int = 3, verbose: bool = True) -> Dict:
        """Complete RAG pipeline"""
        results, context = self.retrieve_context(question, k=k)
        prompt = self.create_prompt(question, context)
        answer = self.generate_answer(prompt)
        
        return {
            'question': question,
            'answer': answer,
            'sources': [
                {
                    'article': r['metadata'].get('article_number', 'Unknown'),
                    'title': r['metadata'].get('title', 'No Title'),
                    'similarity': r.get('similarity', 0)
                } for r in results
            ],
            'context_used': context
        }
