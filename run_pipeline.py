"""
Complete Pipeline: Run all steps to build the RAG system
"""

import os
import sys

def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")
    
    required = {
        'pdfplumber': 'pdfplumber',
        'sentence_transformers': 'sentence-transformers',
        'faiss': 'faiss-cpu',
        'streamlit': 'streamlit',
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"\n📦 Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All requirements satisfied\n")
    return True

def run_pipeline(pdf_path: str):
    """
    Run the complete pipeline
    
    Args:
        pdf_path: Path to Constitution PDF
    """
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        print("Please provide the correct path to the Constitution PDF")
        return False
    
    print("=" * 80)
    print("🇮🇳 INDIAN CONSTITUTION RAG SYSTEM - COMPLETE PIPELINE")
    print("=" * 80)
    
    # Step 2: Extract PDF
    print("\n📄 STEP 2: Extracting PDF...")
    print("-" * 80)
    from step2_extract_pdf import ConstitutionPDFExtractor
    
    extractor = ConstitutionPDFExtractor(pdf_path)
    extractor.extract_text()
    extractor.clean_text()
    articles = extractor.extract_articles()
    extractor.save_articles(articles)
    
    if not articles:
        print("❌ No articles extracted. Check your PDF format.")
        return False
    
    # Step 3: Chunk text
    print("\n✂️  STEP 3: Chunking text...")
    print("-" * 80)
    from step3_chunk_text import ConstitutionChunker
    
    chunker = ConstitutionChunker(chunk_size=600, overlap=100)
    chunks = chunker.chunk_by_article(articles)
    chunks = chunker.add_special_sections(chunks)
    chunker.save_chunks(chunks)
    chunker.get_chunk_stats(chunks)
    
    # Step 4-5: Create embeddings and vector database
    print("\n🧮 STEP 4-5: Creating embeddings and vector database...")
    print("-" * 80)
    from step4_5_embeddings_vectordb import ConstitutionVectorDB
    
    vector_db = ConstitutionVectorDB(model_name='all-MiniLM-L6-v2')
    vector_db.build_index(chunks)
    vector_db.save_index()
    
    # Test search
    print("\n🔍 Testing search...")
    test_queries = [
        "What is Article 21?",
        "fundamental rights",
        "freedom of speech"
    ]
    vector_db.test_search(test_queries)
    
    # Success summary
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\n📊 Summary:")
    print(f"   • Articles extracted: {len(articles)}")
    print(f"   • Chunks created: {len(chunks)}")
    print(f"   • Vector database size: {vector_db.index.ntotal} vectors")
    print("\n📁 Generated files:")
    print("   • constitution_articles.json")
    print("   • constitution_chunks.json")
    print("   • constitution_faiss.index")
    print("   • constitution_metadata.pkl")
    
    print("\n🚀 Next steps:")
    print("   1. Install Ollama: https://ollama.ai")
    print("   2. Download LLaMA model: ollama pull llama2")
    print("   3. Start Ollama: ollama serve")
    print("   4. Run the app: streamlit run app.py")
    print("\n   Or test directly: python step6_8_llama_rag.py")
    
    return True

if __name__ == "__main__":
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Get PDF path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("📄 Enter path to Constitution PDF: ").strip()
    
    # Run pipeline
    success = run_pipeline(pdf_path)
    
    if success:
        print("\n🎉 All done! Your Constitution RAG system is ready.")
    else:
        print("\n❌ Pipeline failed. Please check the errors above.")
        sys.exit(1)
