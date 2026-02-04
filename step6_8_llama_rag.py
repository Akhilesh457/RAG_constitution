"""
Step 6-8: LLaMA Integration with RAG Pipeline
Updated with Mistral support and robust error handling
"""

from typing import List, Dict
import json
import requests

# For local LLaMA via llama-cpp-python (optional)
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

class ConstitutionRAG:
    def __init__(self, vector_db, llm_type: str = 'ollama', model_path: str = None):
        """
        Initialize RAG system
        """
        self.vector_db = vector_db
        self.llm_type = llm_type
        
        if llm_type == 'llama-cpp':
            self._init_llama_cpp(model_path)
        elif llm_type == 'ollama':
            # Updated default to 'mistral' to match your setup
            self._init_ollama(model_path or 'mistral')
        else:
            raise ValueError("llm_type must be 'ollama' or 'llama-cpp'")
    
    def _init_llama_cpp(self, model_path: str):
        """Initialize llama.cpp model"""
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not installed")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=0
        )
    
    def _init_ollama(self, model_name: str):
        """Initialize Ollama model and test connection"""
        self.ollama_model = model_name
        self.ollama_url = "https://api.groq.com/openai/v1/chat/completions"
        
        try:
            # Short timeout for initial check
            response = requests.post(
                self.ollama_url,
                json={"model": model_name, "prompt": "hi", "stream": False},
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Connected to Ollama with model: {model_name}")
            else:
                print(f"⚠️ Ollama returned status {response.status_code}. Check if '{model_name}' is pulled.")
        except Exception as e:
            print(f"⚠️ Connection failed: {e}. Ensure 'ollama serve' is running.")
    
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
        """Generate answer with error catching to prevent UI 500s"""
        if self.llm_type == 'ollama':
            try:
                response = requests.post(
                    self.ollama_url,
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": 4096,
                            "num_predict": 512
                        }
                    },
                    timeout=90  # Generous timeout for slow CPUs
                )
                
                if response.status_code == 200:
                    return response.json().get('response', 'No response field in JSON').strip()
                elif response.status_code == 404:
                    return f"Error 404: Model '{self.ollama_model}' not found. Run 'ollama pull {self.ollama_model}'."
                else:
                    return f"Ollama Error {response.status_code}: {response.text}"
                    
            except requests.exceptions.Timeout:
                return "Error: Ollama timed out. The context might be too large or your CPU is overloaded."
            except Exception as e:
                return f"Connection Error: {str(e)}"
        
        elif self.llm_type == 'llama-cpp':
            output = self.llm(prompt, max_tokens=512, temperature=0.1, stop=["QUESTION:"])
            return output['choices'][0]['text'].strip()
    
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
                    'article': r['metadata']['article_number'],
                    'title': r['metadata'].get('title', 'No Title'),
                    'similarity': r['similarity']
                } for r in results
            ],
            'context_used': context
        }

if __name__ == "__main__":
    # Test script for standalone verification
    print("Testing RAG Backend...")
    # Add your testing logic here if needed
