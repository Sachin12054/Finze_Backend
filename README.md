# Expense AI Categorization Server

A Flask-based REST API for intelligent expense categorization using a fine-tuned DistilBERT transformer model.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Copy Your Trained Model

Copy your trained model directory to `models/expense_distilbert/`:
- `config.json`
- `label_map.json`
- `model.safetensors` (or `pytorch_model.bin`)
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.txt`
- `special_tokens_map.json`

### 3. Run the Server

```bash
python app.py
```

The server will start at `http://localhost:8001`

## 📋 API Endpoints

### Health Check
```bash
GET /api/health
```

### Get Categories
```bash
GET /api/categories
```

### Single Categorization
```bash
POST /api/categorize
Content-Type: application/json

{
  "merchant_name": "Starbucks",
  "description": "Coffee purchase",
  "amount": 5.50
}
```

Response:
```json
{
  "category": "Food & Dining",
  "confidence": 0.95,
  "suggested": [
    ["Food & Dining", 0.95],
    ["Entertainment", 0.03],
    ["Other", 0.02]
  ]
}
```

### Batch Categorization
```bash
POST /api/categorize-batch
Content-Type: application/json

{
  "items": [
    {"merchant_name": "Uber", "description": "Ride", "amount": 15.20},
    {"merchant_name": "Amazon", "description": "Books", "amount": 25.99}
  ]
}
```

### Submit Correction
```bash
POST /api/correction
Content-Type: application/json

{
  "merchant_name": "Starbucks",
  "description": "Coffee",
  "amount": 5.50,
  "correct_category": "Food & Dining"
}
```

## 🔧 Configuration

Environment variables:
- `MODEL_PATH`: Path to the model directory (default: `models/expense_distilbert`)
- `PORT`: Server port (default: `8001`)
- `HOST`: Server host (default: `0.0.0.0`)

## 📱 Expo Integration

For React Native/Expo apps, use the provided client code in your project:

```javascript
const API_BASE_URL = 'http://YOUR_SERVER_IP:8001';

// Single categorization
const result = await fetch(`${API_BASE_URL}/api/categorize`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    merchant_name: 'Starbucks',
    description: 'Coffee',
    amount: 5.50
  })
});
```

## 🔄 Continuous Learning

Corrections are automatically saved to `data/corrections.csv`. To retrain the model:

1. Run the retraining script with the corrections
2. Replace the model files in `models/expense_distilbert/`
3. Restart the server

## 🐳 Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "app.py"]
```

## 📊 Model Performance

- **Accuracy**: 99.56% on validation set
- **Categories**: 9 expense categories
- **Response Time**: ~50ms per prediction
- **GPU Support**: Automatic CUDA detection
