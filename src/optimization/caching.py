# caching.py
import hashlib
import pickle
import os

class ResultCache:
    def __init__(self, cache_dir="./cache"):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_dir = cache_dir
    
    def get_cache_key(self, query):
        return hashlib.md5(query.encode()).hexdigest()
    
    def get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def get(self, query):
        key = self.get_cache_key(query)
        path = self.get_cache_path(key)
        
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, query, result):
        key = self.get_cache_key(query)
        path = self.get_cache_path(key)
        
        with open(path, 'wb') as f:
            pickle.dump(result, f)

# Initialize cache
result_cache = ResultCache()

def cached_query(question):
    """Get result from cache or query the RAG system"""
    cached_result = result_cache.get(question)
    if cached_result:
        print("Cache hit!")
        return cached_result
    
    print("Cache miss. Querying RAG system...")
    result = qa(question)
    result_cache.set(question, result)
    return result
