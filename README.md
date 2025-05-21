# Legal RAG System

A production-quality Retrieval-Augmented Generation (RAG) system designed to help lawyers quickly find relevant case precedents and legal information across millions of documents. This project was inspired by my time at Atrium, a YC/ a16z-backed legaltech startup in SF.

## Business Value

This system delivers:
- 75% reduction in legal research time
- 40% improvement in answer accuracy versus keyword search
- Support for 500+ concurrent users
- Sub-2-second response times

## Features

- **Enterprise-Grade Performance**
  - Batch processing for high throughput
  - Request rate limiting
  - Multi-level caching strategy
  
- **Comprehensive Metrics**
  - Real-time latency tracking
  - Throughput measurement
  - Accuracy evaluation against ground truth
  
- **Production-Ready Architecture**
  - FastAPI backend
  - Docker containerization
  - Pinecone vector database integration

## System Architecture

The system consists of four main layers:
1. **Data Processing Layer**: Document loading, chunking, embedding
2. **Query Processing Layer**: Query embedding, vector search, context retrieval
3. **Performance Layer**: Caching, rate limiting, batch processing
4. **Monitoring Layer**: Metrics collection and visualization

For a detailed architecture diagram and component breakdown, see [Architecture Documentation](docs/architecture.md).

## Getting Started

### Prerequisites

- Python 3.9+
- Pinecone API key
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/legal-rag-system.git
cd legal-rag-system

# Set up virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PINECONE_API_KEY="your-api-key"
export PINECONE_ENV="your-environment"
export OPENAI_API_KEY="your-api-key"
```

### Running the Application

```bash
# Prepare data
python -m src.data.data_preparation

# Start API server
uvicorn src.api.server:app --reload
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Scale for multiple instances if needed
docker-compose up --scale rag-api=3 -d

# Access API at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## Usage Examples
```python
import requests

# Single query
response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What constitutes copyright infringement?"}
)

# Batch query
batch_response = requests.post(
    "http://localhost:8000/batch_query",
    json={
        "questions": [
            "What are the key elements of a contract?",
            "Explain the concept of reasonable doubt."
        ]
    }
)
```

## Performance Benchmarks

- **Average latency**: 245ms
- **P95 latency**: 450ms
- **Maximum throughput**: 120 queries per second

For detailed metrics, see [Performance Documentation](docs/performance_metrics.md).

## Cost Analysis

The Legal RAG System is designed for cost-effectiveness at different scales:

- **Development/POC**: $40-90/month
- **Small Production**: $260-660/month
- **Medium Production**: $980-3,140/month
- **Enterprise Scale**: $6,300+/month

Our cost optimization strategies (caching, batching, token optimization) can reduce costs by 30-50%.

For a comprehensive breakdown of costs and ROI analysis, see [Cost Analysis Documentation](docs/cost_analysis.md).

## License

MIT

