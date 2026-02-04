"""
Step 2: Extract and Clean Constitution Text from PDF
Removes headers, footers, page numbers while preserving structure
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
        Extract individual articles with metadata
        Returns list of dicts with article_num, title, content
        """
        print("📑 Extracting articles...")
        
        # Pattern to match articles: "Article 123" or "Article 123.—Title"
        article_pattern = r'Article\s+(\d+[A-Z]?)\.?\s*[—–-]?\s*([^\n]*)\n(.*?)(?=Article\s+\d+|PART\s+[IVX]+|SCHEDULE|$)'
        
        articles = []
        matches = re.finditer(article_pattern, self.cleaned_text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            article_num = match.group(1).strip()
            title = match.group(2).strip()
            content = match.group(3).strip()
            
            # Clean content
            content = re.sub(r'\n+', ' ', content)
            content = re.sub(r' {2,}', ' ', content)
            
            articles.append({
                'article_number': f"Article {article_num}",
                'title': title,
                'content': content,
                'full_text': f"Article {article_num} - {title}\n\n{content}"
            })
        
        print(f"✅ Extracted {len(articles)} articles")
        return articles
    
    def save_articles(self, articles: List[Dict], output_path: str = 'constitution_articles.json'):
        """Save extracted articles to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved articles to {output_path}")

# Usage Example
if __name__ == "__main__":
    # Replace with your PDF path
    PDF_PATH = "IndianConstitution.pdf"  # <-- UPDATE THIS
    
    extractor = ConstitutionPDFExtractor(PDF_PATH)
    
    # Step 1: Extract raw text
    extractor.extract_text()
    
    # Step 2: Clean text
    extractor.clean_text()
    
    # Step 3: Extract articles
    articles = extractor.extract_articles()
    
    # Step 4: Save to JSON
    extractor.save_articles(articles)
    
    # Preview
    if articles:
        print("\n📖 Sample Article:")
        print(articles[0]['full_text'][:500])
