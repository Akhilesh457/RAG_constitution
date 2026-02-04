"""
Step 11: Evaluation and Testing
Test the RAG system with various question types
"""

import json
from step6_8_llama_rag import ConstitutionRAG
from step4_5_embeddings_vectordb import ConstitutionVectorDB
from typing import List, Dict
import time

class RAGEvaluator:
    def __init__(self, rag_system):
        self.rag = rag_system
        self.results = []
    
    def create_test_suite(self) -> List[Dict]:
        """Create comprehensive test cases"""
        
        test_cases = [
            {
                'category': 'Direct Article Query',
                'questions': [
                    "What is Article 21?",
                    "Explain Article 14",
                    "What does Article 19 say?",
                    "What is Article 32?"
                ],
                'expected_behavior': 'Should cite specific article and provide content'
            },
            {
                'category': 'Conceptual Query',
                'questions': [
                    "What are fundamental rights?",
                    "What are directive principles?",
                    "Explain right to equality",
                    "What is freedom of speech in India?"
                ],
                'expected_behavior': 'Should retrieve and synthesize multiple articles'
            },
            {
                'category': 'Complex Query',
                'questions': [
                    "Can Parliament amend fundamental rights?",
                    "How can the Constitution be amended?",
                    "What is the relationship between fundamental rights and directive principles?",
                    "Can states make laws on matters in the Union List?"
                ],
                'expected_behavior': 'Should combine information from multiple sources'
            },
            {
                'category': 'Preamble/Special',
                'questions': [
                    "What does the Preamble say?",
                    "What are the objectives in the Preamble?",
                    "Is India a secular state according to the Constitution?"
                ],
                'expected_behavior': 'Should retrieve Preamble or relevant articles'
            },
            {
                'category': 'Tricky/Negative',
                'questions': [
                    "What is Article 1000?",  # Doesn't exist
                    "Is there a right to free pizza?",  # Absurd
                    "What does the Constitution say about cryptocurrency?",  # Modern topic
                    "Can the President dissolve Parliament?"  # Partially true
                ],
                'expected_behavior': 'Should say "not found" or provide limited info'
            },
            {
                'category': 'Specific Rights',
                'questions': [
                    "Is right to privacy a fundamental right?",
                    "What is right to education?",
                    "Can I be arrested without a warrant?",
                    "Do I have freedom of religion?"
                ],
                'expected_behavior': 'Should cite relevant articles with specifics'
            }
        ]
        
        return test_cases
    
    def evaluate_answer(self, question: str, response: Dict) -> Dict:
        """Evaluate quality of a single answer"""
        
        answer = response['answer'].lower()
        sources = response['sources']
        
        # Check for hallucination indicators
        has_citation = any(s['article'] in response['answer'] for s in sources)
        says_not_found = any(phrase in answer for phrase in [
            'not found', 'not present', 'not mentioned', 
            'not in the', 'cannot find', 'no information'
        ])
        
        # Check if answer is too short (might indicate failure)
        is_too_short = len(answer.split()) < 10
        
        # Check if answer is relevant to sources
        source_articles = [s['article'].lower() for s in sources]
        mentions_sources = any(art.replace('article ', '') in answer for art in source_articles)
        
        evaluation = {
            'has_citation': has_citation,
            'says_not_found': says_not_found,
            'is_too_short': is_too_short,
            'mentions_sources': mentions_sources,
            'num_sources': len(sources),
            'avg_similarity': sum(s['similarity'] for s in sources) / len(sources) if sources else 0
        }
        
        return evaluation
    
    def run_test_suite(self):
        """Run all tests and collect results"""
        
        test_suite = self.create_test_suite()
        
        print("🧪 RUNNING EVALUATION TEST SUITE")
        print("=" * 80)
        
        all_results = []
        
        for category_data in test_suite:
            category = category_data['category']
            questions = category_data['questions']
            expected = category_data['expected_behavior']
            
            print(f"\n📋 Category: {category}")
            print(f"Expected: {expected}")
            print("-" * 80)
            
            for i, question in enumerate(questions, 1):
                print(f"\n[{i}/{len(questions)}] {question}")
                
                start_time = time.time()
                response = self.rag.query(question, k=3, verbose=False)
                elapsed = time.time() - start_time
                
                evaluation = self.evaluate_answer(question, response)
                
                # Print answer
                print(f"\n💡 Answer: {response['answer'][:200]}...")
                print(f"\n📊 Evaluation:")
                print(f"   • Has citation: {evaluation['has_citation']}")
                print(f"   • Says 'not found': {evaluation['says_not_found']}")
                print(f"   • Mentions sources: {evaluation['mentions_sources']}")
                print(f"   • Avg similarity: {evaluation['avg_similarity']:.1%}")
                print(f"   • Response time: {elapsed:.2f}s")
                
                # Store result
                result = {
                    'category': category,
                    'question': question,
                    'answer': response['answer'],
                    'sources': response['sources'],
                    'evaluation': evaluation,
                    'response_time': elapsed
                }
                all_results.append(result)
        
        self.results = all_results
        return all_results
    
    def generate_report(self):
        """Generate evaluation report"""
        
        if not self.results:
            print("No results to report. Run test suite first.")
            return
        
        print("\n" + "=" * 80)
        print("📊 EVALUATION REPORT")
        print("=" * 80)
        
        # Overall stats
        total_tests = len(self.results)
        avg_time = sum(r['response_time'] for r in self.results) / total_tests
        
        # Quality metrics
        with_citations = sum(1 for r in self.results if r['evaluation']['has_citation'])
        with_not_found = sum(1 for r in self.results if r['evaluation']['says_not_found'])
        too_short = sum(1 for r in self.results if r['evaluation']['is_too_short'])
        
        avg_similarity = sum(r['evaluation']['avg_similarity'] for r in self.results) / total_tests
        
        print(f"\n📈 Overall Statistics:")
        print(f"   • Total questions tested: {total_tests}")
        print(f"   • Avg response time: {avg_time:.2f}s")
        print(f"   • Avg retrieval similarity: {avg_similarity:.1%}")
        
        print(f"\n✅ Quality Metrics:")
        print(f"   • Answers with citations: {with_citations}/{total_tests} ({with_citations/total_tests:.1%})")
        print(f"   • Properly says 'not found': {with_not_found}/{total_tests}")
        print(f"   • Too short responses: {too_short}/{total_tests}")
        
        # Category breakdown
        print(f"\n📊 Performance by Category:")
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for cat, results in categories.items():
            avg_sim = sum(r['evaluation']['avg_similarity'] for r in results) / len(results)
            citations = sum(1 for r in results if r['evaluation']['has_citation'])
            print(f"\n   {cat}:")
            print(f"      • Questions: {len(results)}")
            print(f"      • Avg similarity: {avg_sim:.1%}")
            print(f"      • With citations: {citations}/{len(results)}")
        
        # Identify issues
        print(f"\n⚠️  Potential Issues:")
        issues = []
        
        for result in self.results:
            if result['evaluation']['is_too_short'] and not result['evaluation']['says_not_found']:
                issues.append(f"Short answer: '{result['question']}'")
            
            if result['evaluation']['avg_similarity'] < 0.3:
                issues.append(f"Low similarity: '{result['question']}'")
        
        if issues:
            for issue in issues[:5]:  # Show top 5
                print(f"   • {issue}")
        else:
            print("   ✅ No significant issues detected!")
        
        print("\n" + "=" * 80)
    
    def save_results(self, filepath: str = 'evaluation_results.json'):
        """Save results to JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {filepath}")

# Usage
if __name__ == "__main__":
    print("Loading RAG system...")
    
    # Load vector database
    vector_db = ConstitutionVectorDB()
    vector_db.load_index()
    
    # Load RAG
    rag = ConstitutionRAG(vector_db, llm_type='ollama', model_path='llama2')
    
    # Create evaluator
    evaluator = RAGEvaluator(rag)
    
    # Run tests
    evaluator.run_test_suite()
    
    # Generate report
    evaluator.generate_report()
    
    # Save results
    evaluator.save_results()
