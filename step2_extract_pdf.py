"""
Step 2: Extract and Clean Constitution Text from PDF - FIXED VERSION
Improved article detection for Article 371, 371A, etc.
"""

import re
import pdfplumber
from typing import List, Dict
import json

class ConstitutionPDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.cleaned_text = ""
        
    def extract_text(self) -> str:
        """Extract raw text from PDF"""
        print("📄 Extracting text from PDF...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            all_text = []
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    all_text.append(text)
                if page_num % 50 == 0:
                    print(f"   Processed {page_num} pages...")
        
        self.raw_text = "\n".join(all_text)
        print(f"✅ Extracted {len(self.raw_text)} characters")
        return self.raw_text
    
    def clean_text(self) -> str:
        """Remove page numbers, headers, footers"""
        print("🧹 Cleaning text...")
        
        text = self.raw_text
        
        # Remove page numbers (common patterns)
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'Page \d+', '', text, flags=re.IGNORECASE)
        
        # Remove common headers/footers
        text = re.sub(r'THE CONSTITUTION OF INDIA', '', text, flags=re.IGNORECASE)
        text = re.sub(r'GOVERNMENT OF INDIA', '', text, flags=re.IGNORECASE)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        self.cleaned_text = text.strip()
        print(f"✅ Cleaned text: {len(self.cleaned_text)} characters")
        return self.cleaned_text
    
    def extract_articles(self) -> List[Dict[str, str]]:
        """
        Extract individual articles with IMPROVED metadata detection
        Handles: Article 21, Article 21A, Article 371, Article 371A-371J, etc.
        """
        print("📑 Extracting articles...")
        
        # IMPROVED PATTERN - Handles all article number variations:
        # - Article 1, Article 21, Article 370, Article 371
        # - Article 21A, Article 51A 
        # - Article 371A, 371B, 371C through 371J
        # - With various title separators: .— – - etc.
        
        article_pattern = r'Article\s+(\d+[A-Za-z]*?)\.?\s*[—–\-]?\s*([^\n]*?)\n(.*?)(?=\n\s*Article\s+\d+|PART\s+[IVX]+|SCHEDULE|THE\s+SCHEDULES|APPENDIX|$)'
        
        articles = []
        matches = re.finditer(article_pattern, self.cleaned_text, re.DOTALL | re.IGNORECASE)
        
        article_numbers_found = set()
        
        for match in matches:
            article_num = match.group(1).strip()
            title = match.group(2).strip()
            content = match.group(3).strip()
            
            # Skip if we already found this article (avoid duplicates)
            if article_num in article_numbers_found:
                continue
            
            article_numbers_found.add(article_num)
            
            # Clean content
            content = re.sub(r'\n+', ' ', content)
            content = re.sub(r' {2,}', ' ', content)
            
            # Only add if there's actual content
            if len(content) > 10:  # Minimum content length
                articles.append({
                    'article_number': f"Article {article_num}",
                    'title': title,
                    'content': content,
                    'full_text': f"Article {article_num} - {title}\n\n{content}"
                })
        
        print(f"✅ Extracted {len(articles)} articles")
        
        # Debug: Show sample of article numbers found
        sample_articles = sorted([a['article_number'] for a in articles[:10]])
        print(f"   Sample articles: {', '.join(sample_articles)}")
        
        # Check for specific articles
        critical_articles = ['Article 21', 'Article 370', 'Article 371', 'Article 371A']
        found_critical = [a for a in critical_articles if f"{a}" in [art['article_number'] for art in articles]]
        missing_critical = [a for a in critical_articles if a not in found_critical]
        
        if found_critical:
            print(f"   ✅ Found critical articles: {', '.join(found_critical)}")
        if missing_critical:
            print(f"   ⚠️  Missing critical articles: {', '.join(missing_critical)}")
            print(f"   This may be normal if they don't exist in your PDF version")
        
        return articles
    
    def extract_articles_fallback(self) -> List[Dict[str, str]]:
        """
        FALLBACK METHOD: More aggressive extraction
        Use this if the main method doesn't find Article 371, etc.
        """
        print("🔧 Using fallback extraction method...")
        
        articles = []
        
        # Split by "Article" keyword
        article_splits = re.split(r'\n\s*(Article\s+\d+[A-Za-z]*)', self.cleaned_text, flags=re.IGNORECASE)
        
        for i in range(1, len(article_splits), 2):
            if i + 1 < len(article_splits):
                article_header = article_splits[i].strip()
                article_body = article_splits[i + 1].strip()
                
                # Extract article number
                num_match = re.search(r'Article\s+(\d+[A-Za-z]*)', article_header, re.IGNORECASE)
                if num_match:
                    article_num = num_match.group(1)
                    
                    # Try to find title (usually after .— or .- or just .)
                    title_match = re.search(r'[.—–\-]\s*(.+?)(?:\n|$)', article_body[:200])
                    title = title_match.group(1).strip() if title_match else ""
                    
                    # Get content (first 500 words to avoid grabbing next article)
                    content = article_body[:2000].strip()
                    content = re.sub(r'\n+', ' ', content)
                    content = re.sub(r' {2,}', ' ', content)
                    
                    if len(content) > 10:
                        articles.append({
                            'article_number': f"Article {article_num}",
                            'title': title,
                            'content': content,
                            'full_text': f"Article {article_num} - {title}\n\n{content}"
                        })
        
        print(f"✅ Fallback extracted {len(articles)} articles")
        return articles
    
    def save_articles(self, articles: List[Dict], output_path: str = 'constitution_articles.json'):
        """Save extracted articles to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved articles to {output_path}")
        
        # Save a summary for debugging
        summary_path = output_path.replace('.json', '_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"Total Articles: {len(articles)}\n\n")
            f.write("All Article Numbers:\n")
            for article in sorted(articles, key=lambda x: self._sort_article_key(x['article_number'])):
                f.write(f"  - {article['article_number']}: {article['title'][:60]}\n")
        print(f"💾 Saved summary to {summary_path}")
    
    def _sort_article_key(self, article_num: str):
        """Helper to sort article numbers properly"""
        # Extract number and letter parts
        match = re.search(r'Article\s+(\d+)([A-Za-z]*)', article_num)
        if match:
            num = int(match.group(1))
            letter = match.group(2) if match.group(2) else ''
            return (num, letter)
        return (0, '')

# Usage Example
if __name__ == "__main__":
    import sys
    
    # Get PDF path from command line or prompt
    if len(sys.argv) > 1:
        PDF_PATH = sys.argv[1]
    else:
        PDF_PATH = input("Enter path to Constitution PDF: ").strip()
    
    extractor = ConstitutionPDFExtractor(PDF_PATH)
    
    # Step 1: Extract raw text
    extractor.extract_text()
    
    # Step 2: Clean text
    extractor.clean_text()
    
    # Step 3: Extract articles (try main method first)
    articles = extractor.extract_articles()
    
    # If we got very few articles, try fallback
    if len(articles) < 50:
        print("\n⚠️  Low article count detected. Trying fallback method...")
        articles_fallback = extractor.extract_articles_fallback()
        if len(articles_fallback) > len(articles):
            print("✅ Fallback method found more articles!")
            articles = articles_fallback
    
    # Step 4: Save to JSON
    extractor.save_articles(articles)
    
    # Preview
    if articles:
        print("\n📖 Sample Articles:")
        for i, article in enumerate(articles[:3]):
            print(f"\n{i+1}. {article['article_number']} - {article['title']}")
            print(f"   {article['content'][:150]}...")
        
        # Check for Article 371 specifically
        article_371 = next((a for a in articles if a['article_number'] == 'Article 371'), None)
        if article_371:
            print("\n✅ Found Article 371:")
            print(f"   Title: {article_371['title']}")
            print(f"   Content: {article_371['content'][:200]}...")
        else:
            print("\n⚠️  Article 371 NOT found in extraction!")
