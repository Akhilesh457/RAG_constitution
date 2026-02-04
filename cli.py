"""
Simple CLI Interface for Constitution RAG
Quick testing without web interface
"""

import sys
from step6_8_llama_rag import ConstitutionRAG
from step4_5_embeddings_vectordb import ConstitutionVectorDB

class ConstitutionCLI:
    def __init__(self):
        print("🇮🇳 Indian Constitution AI Assistant (CLI)")
        print("=" * 60)
        print("Loading system...")
        
        # Load vector database
        self.vector_db = ConstitutionVectorDB()
        try:
            self.vector_db.load_index()
            print("✅ Knowledge base loaded")
        except FileNotFoundError:
            print("❌ Vector database not found.")
            print("Run: python run_pipeline.py <pdf_path>")
            sys.exit(1)
        
        # Load RAG system
        try:
            self.rag = ConstitutionRAG(
                self.vector_db,
                llm_type='ollama',
                model_path='llama2'
            )
            print("✅ AI model ready\n")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Make sure Ollama is running: ollama serve")
            sys.exit(1)
    
    def print_response(self, response):
        """Pretty print response"""
        print("\n" + "=" * 60)
        print("💡 ANSWER:")
        print("=" * 60)
        print(response['answer'])
        
        print("\n" + "-" * 60)
        print("📚 SOURCES:")
        print("-" * 60)
        for i, source in enumerate(response['sources'], 1):
            print(f"{i}. {source['article']} - {source['title']}")
            print(f"   Relevance: {source['similarity']:.1%}")
        print("=" * 60 + "\n")
    
    def interactive_mode(self):
        """Interactive question-answer loop"""
        print("Commands:")
        print("  • Type your question and press Enter")
        print("  • 'examples' - Show example questions")
        print("  • 'quit' or 'exit' - Exit the program")
        print()
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() in ['examples', 'help']:
                    self.show_examples()
                    continue
                
                # Process query
                print("\n🤔 Searching Constitution...")
                response = self.rag.query(question, k=3, verbose=False)
                self.print_response(response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    def show_examples(self):
        """Show example questions"""
        examples = [
            "What is Article 21?",
            "What are the fundamental rights?",
            "Explain the Preamble",
            "Can Parliament amend the Constitution?",
            "What is Right to Equality?",
            "What are Directive Principles of State Policy?",
            "What does Article 14 say?",
            "Is Right to Privacy a fundamental right?",
            "What is Article 370?",
            "Explain separation of powers"
        ]
        
        print("\n📖 Example Questions:")
        print("-" * 60)
        for i, ex in enumerate(examples, 1):
            print(f"{i}. {ex}")
        print("-" * 60 + "\n")
    
    def batch_mode(self, questions):
        """Process multiple questions at once"""
        print(f"\n🔄 Processing {len(questions)} questions...\n")
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {question}")
            response = self.rag.query(question, k=3, verbose=False)
            self.print_response(response)

def main():
    cli = ConstitutionCLI()
    
    # Check if questions provided as arguments
    if len(sys.argv) > 1:
        questions = sys.argv[1:]
        cli.batch_mode(questions)
    else:
        cli.interactive_mode()

if __name__ == "__main__":
    main()
