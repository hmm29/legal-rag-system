# performance_metrics.py
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

class PerformanceTracker:
    def __init__(self):
        self.latencies = []
        self.throughput_data = []
        self.accuracy_data = []
    
    def measure_latency(self, func, *args, **kwargs):
        """Measure latency of a function call"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        latency = end_time - start_time
        self.latencies.append(latency)
        return result, latency
    
    def measure_throughput(self, batch_size, duration):
        """Record throughput data"""
        throughput = batch_size / duration
        self.throughput_data.append({
            'batch_size': batch_size,
            'duration': duration,
            'throughput': throughput
        })
        return throughput
    
    def measure_accuracy(self, expected, actual):
        """Measure accuracy metrics"""
        # This is simplified - in a real scenario, you'd use more sophisticated evaluation
        score = 1 if expected.lower() in actual.lower() else 0
        self.accuracy_data.append({
            'expected': expected,
            'actual': actual,
            'score': score
        })
        return score
    
    def generate_report(self, output_file="performance_report.json"):
        """Generate performance report"""
        report = {
            'latency': {
                'mean': np.mean(self.latencies),
                'median': np.median(self.latencies),
                'p95': np.percentile(self.latencies, 95),
                'p99': np.percentile(self.latencies, 99),
                'min': min(self.latencies),
                'max': max(self.latencies)
            },
            'throughput': {
                'data': self.throughput_data,
                'average': np.mean([d['throughput'] for d in self.throughput_data]) if self.throughput_data else 0
            },
            'accuracy': {
                'data': self.accuracy_data,
                'average': np.mean([d['score'] for d in self.accuracy_data]) if self.accuracy_data else 0
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def visualize_performance(self):
        """Generate performance visualizations"""
        # Latency histogram
        plt.figure(figsize=(12, 4))
        plt.subplot(131)
        plt.hist(self.latencies, bins=20)
        plt.title('Latency Distribution')
        plt.xlabel('Latency (s)')
        plt.ylabel('Frequency')
        
        # Throughput over time
        plt.subplot(132)
        if self.throughput_data:
            throughputs = [d['throughput'] for d in self.throughput_data]
            plt.plot(throughputs)
            plt.title('Throughput Over Time')
            plt.xlabel('Batch Number')
            plt.ylabel('Queries per Second')
        
        # Accuracy
        plt.subplot(133)
        if self.accuracy_data:
            scores = [d['score'] for d in self.accuracy_data]
            plt.bar(['Accuracy'], [np.mean(scores)])
            plt.title('Accuracy')
            plt.ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig('performance_metrics.png')
        plt.close()

# Initialize performance tracker
tracker = PerformanceTracker()

# Example usage
question = "What constitutes copyright infringement?"
result, latency = tracker.measure_latency(cached_query, question)
print(f"Query latency: {latency:.2f}s")

# Simulate throughput measurement
questions = ["What are the elements of a valid contract?"] * 10
start_time = time.time()
for q in questions:
    _ = cached_query(q)
end_time = time.time()
throughput = tracker.measure_throughput(len(questions), end_time - start_time)
print(f"Throughput: {throughput:.2f} queries per second")

# Generate report
report = tracker.generate_report()
tracker.visualize_performance()
