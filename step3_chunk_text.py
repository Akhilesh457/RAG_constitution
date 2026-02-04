"""
Step 3: Intelligent Text Chunking
Creates overlapping chunks optimized for retrieval
"""

from typing import List, Dict
import json

class ConstitutionChunker:
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        """
        Args:
            chunk_size: Target tokens per chunk (approx 600 tokens = ~450 words)
            overlap: Overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def chunk_by_article(self, articles: List[Dict]) -> List[Dict]:
        """
        Chunk articles - keeps small articles whole, splits large ones
        """
        print(f"✂️  Chunking articles (size: {self.chunk_size}, overlap: {self.overlap})...")
        
        chunks = []
        chunk_id = 0
        
        for article in articles:
            article_text = article['full_text']
            article_num = article['article_number']
            title = article['title']
            
            tokens = self.count_tokens(article_text)
            
            # If article is small enough, keep it whole
            if tokens <= self.chunk_size:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': article_text,
                    'metadata': {
                        'article_number': article_num,
                        'title': title,
                        'chunk_type': 'full_article'
                    }
                })
                chunk_id += 1
            
            # Otherwise, split into overlapping chunks
            else:
                words = article_text.split()
                words_per_chunk = self.chunk_size // 4  # approx
                overlap_words = self.overlap // 4
                
                start = 0
                part_num = 1
                
                while start < len(words):
                    end = start + words_per_chunk
                    chunk_text = ' '.join(words[start:end])
                    
                    # Add article header to each chunk for context
                    chunk_with_header = f"{article_num} - {title} (Part {part_num})\n\n{chunk_text}"
                    
                    chunks.append({
                        'chunk_id': chunk_id,
                        'text': chunk_with_header,
                        'metadata': {
                            'article_number': article_num,
                            'title': title,
                            'chunk_type': 'partial',
                            'part': part_num
                        }
                    })
                    
                    chunk_id += 1
                    part_num += 1
                    start = end - overlap_words  # Create overlap
        
        print(f"✅ Created {len(chunks)} chunks from {len(articles)} articles")
        return chunks
    
    def add_special_sections(self, chunks: List[Dict]) -> List[Dict]:
        """Add Preamble and important sections as separate chunks"""
        
        preamble = {
            'chunk_id': -1,
            'text': """PREAMBLE
            
WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC and to secure to all its citizens:

JUSTICE, social, economic and political;
LIBERTY of thought, expression, belief, faith and worship;
EQUALITY of status and of opportunity;
and to promote among them all
FRATERNITY assuring the dignity of the individual and the unity and integrity of the Nation;

IN OUR CONSTITUENT ASSEMBLY this twenty-sixth day of November, 1949, do HEREBY ADOPT, ENACT AND GIVE TO OURSELVES THIS CONSTITUTION.""",
            'metadata': {
                'article_number': 'PREAMBLE',
                'title': 'Preamble to the Constitution',
                'chunk_type': 'preamble'
            }
        }
        
        # Add preamble at the beginning
        all_chunks = [preamble] + chunks
        
        # Re-index
        for idx, chunk in enumerate(all_chunks):
            chunk['chunk_id'] = idx
        
        return all_chunks
    
    def save_chunks(self, chunks: List[Dict], output_path: str = 'constitution_chunks.json'):
        """Save chunks to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(chunks)} chunks to {output_path}")
    
    def get_chunk_stats(self, chunks: List[Dict]):
        """Print statistics about chunks"""
        print("\n📊 Chunk Statistics:")
        print(f"   Total chunks: {len(chunks)}")
        
        token_counts = [self.count_tokens(c['text']) for c in chunks]
        print(f"   Avg tokens/chunk: {sum(token_counts) / len(token_counts):.0f}")
        print(f"   Min tokens: {min(token_counts)}")
        print(f"   Max tokens: {max(token_counts)}")
        
        types = {}
        for chunk in chunks:
            ctype = chunk['metadata']['chunk_type']
            types[ctype] = types.get(ctype, 0) + 1
        print(f"   Chunk types: {types}")

# Usage Example
if __name__ == "__main__":
    # Load articles from step 2
    with open('constitution_articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Create chunker
    chunker = ConstitutionChunker(chunk_size=600, overlap=100)
    
    # Chunk articles
    chunks = chunker.chunk_by_article(articles)
    
    # Add special sections
    chunks = chunker.add_special_sections(chunks)
    
    # Save chunks
    chunker.save_chunks(chunks)
    
    # Show stats
    chunker.get_chunk_stats(chunks)
    
    # Preview
    print("\n📖 Sample Chunk:")
    print(chunks[0]['text'][:300])
