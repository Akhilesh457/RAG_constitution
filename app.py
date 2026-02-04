"""
Step 9-10: Streamlit Web Interface
Beautiful UI for Constitution RAG system
"""

import streamlit as st
import sys
from step6_8_llama_rag import ConstitutionRAG
from step4_5_embeddings_vectordb import ConstitutionVectorDB

# Page config
st.set_page_config(
    page_title="Indian Constitution AI Assistant",
    page_icon="🇮🇳",
    layout="wide"
)

# Custom CSS
# Replace the existing st.markdown block for CSS with this:
st.markdown("""
    <style>
    /* Main Header with consistent Indian Flag Gradient */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(90deg, #FF9933 10%, #121212 50%, #138808 90%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    
    /* Answer Box - High Contrast */
    .answer-box {
        background-color: #ffffff;
        color: #1a1a1a !important; /* Forces dark text */
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #FF9933;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 25px;
    }

    /* Source Cards - Better Visibility */
    .source-box {
        background-color: #f8f9fa;
        color: #333333 !important; /* Forces dark text */
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        height: 100%; /* Ensures uniform height in columns */
        transition: transform 0.2s;
    }
    
    .source-box:hover {
        border-color: #138808;
        transform: translateY(-2px);
    }

    /* Typography fixes for cards */
    .source-box strong { color: #d9534f; font-size: 1rem; }
    .source-box small { color: #666666; display: block; margin-top: 5px; }
    
    /* Make Streamlit buttons more vibrant */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #138808;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_rag_system():
    """Load RAG system (cached)"""
    with st.spinner("🔧 Loading Constitution knowledge base..."):
        # Load vector database
        vector_db = ConstitutionVectorDB()
        try:
            vector_db.load_index()
        except FileNotFoundError:
            st.error("❌ Vector database not found. Please run steps 1-5 first.")
            st.stop()
        
        # Initialize RAG
        try:
            rag = ConstitutionRAG(
                vector_db,
                llm_type='ollama',
                model_path='mistral'
            )
            return rag
        except Exception as e:
            st.error(f"❌ Error loading LLaMA model: {e}")
            st.info("💡 Make sure Ollama is installed and running: `ollama serve`")
            st.stop()

def main():
    # Header
    st.markdown('<h1 class="main-header">🇮🇳 Indian Constitution AI Assistant</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <p style='text-align: center; color: #666;'>
    Ask questions about the Indian Constitution and get accurate, cited answers
    </p>
    """, unsafe_allow_html=True)
    
    # Load RAG system
    rag = load_rag_system()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        k_value = st.slider(
            "Number of sources to retrieve",
            min_value=1,
            max_value=7,
            value=3,
            help="More sources = more context but slower"
        )
        
        show_sources = st.checkbox("Show source articles", value=True)
        show_context = st.checkbox("Show retrieved context", value=False)
        
        st.divider()
        
        st.subheader("📚 Example Questions")
        example_questions = [
            "What are the fundamental rights?",
            "What does the Preamble say?",
            "Can Parliament amend the Constitution?",
            "What is Right to Equality?",
            "Explain Directive Principles of State Policy",
            "What is Article 370?"
        ]
        
        for question in example_questions:
            if st.button(question, key=question, use_container_width=True):
                st.session_state.example_question = question
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Check if example question was clicked
        default_question = ""
        if 'example_question' in st.session_state:
            default_question = st.session_state.example_question
            del st.session_state.example_question
        
        question = st.text_input(
            "🔍 Ask your question:",
            value=default_question,
            placeholder="E.g., What is Article 21 of the Indian Constitutio?"
        )
    
    with col2:
        search_button = st.button("🔎 Search", type="primary", use_container_width=True)
    
    # Process query
    if question and (search_button or default_question):
        with st.spinner("🤔 Analyzing Constitution..."):
            try:
                response = rag.query(question, k=k_value, verbose=False)
                
                # Display answer
                st.markdown("### 💡 Answer")
                st.markdown(f'<div class="answer-box">{response["answer"]}</div>', 
                           unsafe_allow_html=True)
                
                # Display sources
                if show_sources and response['sources']:
                    st.markdown("### 📖 Sources")
                    
                    cols = st.columns(len(response['sources']))
                    for i, (col, source) in enumerate(zip(cols, response['sources'])):
                        with col:
                            st.markdown(f"""
                            <div class="source-box">
                                <strong>{source['article']}</strong><br>
                                <small>{source['title']}</small><br>
                                <small>Relevance: {source['similarity']:.1%}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show context if requested
                if show_context:
                    with st.expander("📄 View Retrieved Context"):
                        st.text(response['context_used'])
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")
    
    # Footer
    st.divider()
    st.markdown("""
    <p style='text-align: center; color: #999; font-size: 0.9rem;'>
    Built with LLaMA + FAISS + Sentence Transformers | 
    Data source: Constitution of India
    </p>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
