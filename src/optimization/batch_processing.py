# batch_processing.py
from concurrent.futures import ThreadPoolExecutor
import time

def process_batch(questions):
    """Process a batch of questions in parallel"""
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(qa, question) for question in questions]
        for future in futures:
            results.append(future.result())
    
    end_time = time.time()
    return results, end_time - start_time

# Example batch usage
questions = [
    "What are the key elements of a contract?",
    "Explain the concept of reasonable doubt.",
    "What constitutes copyright infringement?",
    "How does habeas corpus work?",
    "What is the difference between a civil and criminal case?"
]

results, duration = process_batch(questions)
print(f"Processed {len(questions)} queries in {duration:.2f} seconds")
