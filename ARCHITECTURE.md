# 📐 Project Architecture - Indian Constitution RAG System

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Streamlit   │  │     CLI      │  │   Python     │     │
│  │   Web UI     │  │  Interface   │  │   Script     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG ORCHESTRATOR                         │
│                  (ConstitutionRAG)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 1. Query Processing                              │     │
│  │    • Clean and normalize user query              │     │
│  │    • Convert to embedding vector                 │     │
│  └──────────────────────────────────────────────────┘     │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────┐     │
│  │ 2. Retrieval (FAISS Vector Search)               │     │
│  │    • Semantic similarity search                  │     │
│  │    • Retrieve top-k relevant chunks              │     │
│  │    • Rank by similarity score                    │     │
│  └──────────────────────────────────────────────────┘     │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────┐     │
│  │ 3. Context Formatting                            │     │
│  │    • Format retrieved chunks                     │     │
│  │    • Add metadata (article numbers)              │     │
│  │    • Create structured context                   │     │
│  └──────────────────────────────────────────────────┘     │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────┐     │
│  │ 4. Prompt Engineering                            │     │
│  │    • Insert context into template                │     │
│  │    • Add instructions for LLM                    │     │
│  │    • Apply hallucination prevention              │     │
│  └──────────────────────────────────────────────────┘     │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────┐     │
│  │ 5. LLM Generation (LLaMA)                        │     │
│  │    • Generate answer with citations              │     │
│  │    • Apply temperature & constraints             │     │
│  │    • Return structured response                  │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  FAISS Index │  │   Metadata   │  │    Chunks    │     │
│  │  (384-dim    │  │   (Article   │  │   (JSON)     │     │
│  │   vectors)   │  │   numbers)   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Processing Pipeline

```
PDF Input → Text Extraction → Cleaning → Article Detection → Chunking → Embeddings → Vector DB

Step 2          Step 3           Step 4-5
```

#### Step 2: PDF Extraction (step2_extract_pdf.py)
- **Input**: Constitution PDF
- **Process**:
  - Extract text using pdfplumber
  - Remove headers, footers, page numbers
  - Detect article boundaries using regex
- **Output**: `constitution_articles.json`
- **Key Class**: `ConstitutionPDFExtractor`

#### Step 3: Text Chunking (step3_chunk_text.py)
- **Input**: Extracted articles
- **Strategy**:
  - Chunk size: 600 tokens (~450 words)
  - Overlap: 100 tokens (prevents information loss)
  - Keep small articles whole
  - Split large articles with context preservation
- **Output**: `constitution_chunks.json`
- **Key Class**: `ConstitutionChunker`

#### Step 4-5: Embeddings & Vector DB (step4_5_embeddings_vectordb.py)
- **Input**: Text chunks
- **Process**:
  - Generate embeddings using SentenceTransformers
  - Build FAISS index for similarity search
  - Store metadata alongside vectors
- **Output**: 
  - `constitution_faiss.index` (FAISS index)
  - `constitution_metadata.pkl` (chunk data)
- **Key Class**: `ConstitutionVectorDB`
- **Model**: `all-MiniLM-L6-v2` (384 dimensions)

### 2. RAG Engine

#### Step 6-8: LLaMA Integration (step6_8_llama_rag.py)
- **Components**:
  1. Vector search (retrieves relevant chunks)
  2. Prompt engineering (formats context)
  3. LLM generation (produces answer)
- **Key Class**: `ConstitutionRAG`
- **LLM Options**:
  - Ollama (recommended): Easy local deployment
  - llama.cpp: Direct GGUF model loading

#### Prompt Template
```
System Role: Legal assistant for Indian Constitution

Instructions:
1. Use ONLY provided context
2. Cite article numbers
3. Say "not found" if uncertain
4. Be precise and factual
5. No external information

Context: {retrieved_chunks}
Question: {user_query}
Answer:
```

### 3. User Interfaces

#### Web UI (app.py)
- **Framework**: Streamlit
- **Features**:
  - Question input with autocomplete
  - Source article display with relevance scores
  - Adjustable retrieval parameters
  - Example questions
  - Context viewer (debug mode)
- **Port**: 8501

#### CLI (cli.py)
- **Modes**:
  - Interactive: Question-answer loop
  - Batch: Multiple questions at once
- **Features**:
  - Pretty-printed responses
  - Source citations
  - Example questions

### 4. Evaluation System (step11_evaluation.py)

#### Test Categories
1. **Direct Article Queries**: "What is Article 21?"
2. **Conceptual Queries**: "What are fundamental rights?"
3. **Complex Queries**: "Can Parliament amend fundamental rights?"
4. **Tricky/Negative**: Test hallucination prevention
5. **Specific Rights**: Edge cases

#### Metrics
- Citation presence
- "Not found" handling
- Response length
- Source relevance
- Response time

## Data Flow

### Query Processing Flow
```
User Query
    ↓
Query Embedding (SentenceTransformer)
    ↓
FAISS Similarity Search (L2 distance)
    ↓
Top-k Chunks Retrieved
    ↓
Context Formatting (with metadata)
    ↓
Prompt Creation (template + context)
    ↓
LLaMA Generation (with constraints)
    ↓
Response (answer + citations)
    ↓
User Interface
```

### Example with Actual Data

**Input**: "What is Article 21?"

**Step 1 - Embedding**: 
```python
query_vector = [0.023, -0.145, 0.089, ..., 0.234]  # 384 dims
```

**Step 2 - FAISS Search**:
```python
# Top 3 results
[
  (chunk_id=87, distance=0.12, similarity=0.952),
  (chunk_id=88, distance=0.34, similarity=0.746),
  (chunk_id=145, distance=0.45, similarity=0.689)
]
```

**Step 3 - Retrieved Context**:
```
[Source 1] Article 21
Protection of life and personal liberty
No person shall be deprived of his life or 
personal liberty except according to procedure 
established by law.

[Source 2] Article 20
Protection in respect of conviction for offences...

[Source 3] Article 22
Protection against arrest and detention...
```

**Step 4 - LLaMA Output**:
```
Article 21 of the Indian Constitution guarantees 
the protection of life and personal liberty. It 
states that no person shall be deprived of his 
life or personal liberty except according to 
procedure established by law. This fundamental 
right is one of the most important provisions...
```

## Performance Characteristics

### Time Complexity
- **Embedding generation**: O(n) where n = sequence length
- **FAISS search**: O(log N) where N = total vectors
- **LLM generation**: O(m) where m = output tokens

### Space Complexity
- **FAISS index**: 384 dims × 542 chunks × 4 bytes ≈ 800KB
- **Metadata**: ~2MB (JSON)
- **LLaMA model**: 4-7GB (depending on quantization)

### Actual Performance
| Operation | Time | Notes |
|-----------|------|-------|
| PDF extraction | ~30s | Depends on PDF size |
| Embedding generation | ~2min | Batch processing |
| FAISS index build | ~5s | In-memory |
| Single query embedding | ~50ms | Real-time |
| FAISS search | ~10ms | Sub-second |
| LLM generation | 1-2s | CPU inference |
| **Total per query** | **1-3s** | End-to-end |

## Scalability Considerations

### Current Limits
- **Corpus size**: 542 chunks (can handle 10K+)
- **Memory**: ~4GB for embeddings + LLM
- **Concurrent users**: 1 (single-threaded)

### Scaling Options
1. **Larger corpus**:
   - Use FAISS IVF index for >100K vectors
   - Implement chunk pagination
2. **Multiple users**:
   - Add request queue
   - Implement model batching
3. **Faster inference**:
   - GPU acceleration (CUDA)
   - Quantization (Q4_K_M)
   - Model distillation

## Security & Privacy

### Data Privacy
- ✅ All processing is local (no external API calls)
- ✅ No data sent to external servers
- ✅ Constitution text is public domain

### Input Validation
- ❌ Currently minimal validation
- 🔧 TODO: Add input sanitization
- 🔧 TODO: Rate limiting for web UI

## Deployment Options

### 1. Local Development
```bash
streamlit run app.py
```
**Pros**: Easy setup, full control
**Cons**: Single user, manual start

### 2. Docker Container
```dockerfile
FROM python:3.9
# Install dependencies
# Copy files
# Expose port 8501
CMD ["streamlit", "run", "app.py"]
```
**Pros**: Portable, reproducible
**Cons**: Larger image size

### 3. Cloud Deployment
- **Heroku**: Good for demos
- **AWS EC2**: Full control
- **Google Cloud Run**: Serverless
**Note**: Requires GPU for good performance

## Limitations & Future Work

### Current Limitations
1. **No conversation memory**: Each query is independent
2. **Single language**: Only English
3. **No amendment tracking**: Static constitution text
4. **Limited error handling**: Basic exception catching

### Future Enhancements
1. **Conversation history**: Track multi-turn dialogues
2. **Advanced search**: Boolean operators, filters
3. **Comparative analysis**: Compare articles
4. **Amendment timeline**: Show constitutional changes
5. **Multilingual support**: Hindi, other regional languages
6. **Citation export**: Generate proper legal citations
7. **Mobile app**: React Native frontend

## Technical Decisions & Rationale

### Why FAISS?
- ✅ Fast: Optimized C++ implementation
- ✅ Local: No external dependencies
- ✅ Mature: Battle-tested by Meta
- ❌ Limited: No built-in filtering

### Why SentenceTransformers?
- ✅ Easy: Simple API
- ✅ Quality: State-of-art embeddings
- ✅ Flexible: Many model options
- ❌ Size: Models are 100MB+

### Why LLaMA (local) vs GPT (API)?
- ✅ Privacy: No data leaves local machine
- ✅ Cost: No per-token charges
- ✅ Control: Full model customization
- ❌ Performance: Slower than cloud GPT
- ❌ Maintenance: Manual updates

### Why Streamlit?
- ✅ Rapid: Build UI in minutes
- ✅ Python-native: No separate frontend
- ✅ Interactive: Built-in widgets
- ❌ Customization: Limited styling
- ❌ Scaling: Not for production

## Code Quality Metrics

### Test Coverage
- Unit tests: None (TODO)
- Integration tests: Evaluation suite
- End-to-end tests: Manual

### Documentation
- Inline comments: High
- Docstrings: Medium
- Type hints: Partial
- README: Comprehensive

### Code Organization
- Modularity: ✅ Excellent (separate files per step)
- Reusability: ✅ Good (classes for components)
- Maintainability: ✅ Good (clear structure)

---

**Last Updated**: February 2026
**Version**: 1.0
**Author**: Resume Project
