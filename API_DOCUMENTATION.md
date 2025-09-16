# Finze Backend API Documentation

## Overview

The Finze Backend provides comprehensive expense management capabilities including:
- **AI-powered expense categorization** using advanced machine learning models
- **Receipt scanning and data extraction** using Google Gemini AI
- **Firebase Firestore integration** for data persistence
- **User analytics and reporting** for expense insights

## Quick Start

### 1. Environment Setup

```bash
# Navigate to Backend directory
cd Backend

# Run setup script (Windows)
setup_and_run.bat

# Or manual setup
python setup_environment.py
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with the following variables:

```env
# Required for receipt scanning
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/firebase-service-account.json

# Optional configurations
MODEL_PATH=models/expense_distilbert
PORT=8001
HOST=0.0.0.0
DEBUG=False
```

### 3. Start the Server

```bash
python combined_server.py
```

The server will be available at `http://localhost:8001`

## API Endpoints

### Health & Status

#### `GET /api/health`
Get comprehensive health status and service availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-12T10:30:00Z",
  "services": {
    "ai_categorization": true,
    "receipt_scanning": true,
    "firestore": true
  },
  "ai_model": {
    "loaded": true,
    "type": "ultra-perfect",
    "categories": ["Food & Dining", "Transportation", ...]
  }
}
```

---

### AI Categorization

#### `POST /api/categorize`
Categorize a single expense using AI.

**Request:**
```json
{
  "description": "Starbucks coffee and pastry",
  "amount": 12.50,
  "merchant_name": "Starbucks"
}
```

**Response:**
```json
{
  "category": "Food & Dining",
  "confidence": 0.92,
  "subcategory": "Coffee & Cafe",
  "reasoning": "Coffee shop expense"
}
```

#### `POST /api/categorize-batch`
Categorize multiple expenses in a single request.

**Request:**
```json
{
  "items": [
    {
      "description": "McDonald's lunch",
      "amount": 8.99
    },
    {
      "description": "Gas station fuel", 
      "amount": 45.00
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "category": "Food & Dining",
      "confidence": 0.89
    },
    {
      "category": "Transportation",
      "confidence": 0.95
    }
  ]
}
```

#### `GET /api/categories`
Get all available expense categories.

**Response:**
```json
{
  "categories": [
    "Food & Dining",
    "Transportation",
    "Healthcare",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Travel",
    "Education",
    "Other"
  ]
}
```

#### `POST /api/correction`
Submit user corrections for model improvement.

**Request:**
```json
{
  "description": "Netflix subscription",
  "merchant_name": "Netflix",
  "amount": 15.99,
  "correct_category": "Entertainment"
}
```

---

### Receipt Scanning

#### `POST /api/upload-receipt`
Upload and process a receipt image using Gemini AI.

**Request:** `multipart/form-data`
- `image`: Image file (PNG, JPG, JPEG, GIF, BMP, WEBP, HEIC, HEIF)
- `user_id`: User identifier (optional)

**Response:**
```json
{
  "status": "success",
  "data": {
    "extraction_status": "success",
    "confidence_score": 0.92,
    "total_amount": 14.53,
    "currency": "USD",
    "merchant_name": "Test Restaurant",
    "merchant_address": "123 Main Street",
    "date": "2025-09-12",
    "time": "14:30",
    "category": "Food & Dining",
    "payment_method": "card",
    "items": [
      {
        "name": "Coffee",
        "quantity": 1,
        "unit_price": 4.50,
        "total_price": 4.50,
        "category": "Beverages"
      },
      {
        "name": "Sandwich",
        "quantity": 1,
        "unit_price": 8.95,
        "total_price": 8.95,
        "category": "Food"
      }
    ],
    "tax_details": {
      "tax_amount": 1.08,
      "tax_rate": 8.0,
      "tax_type": "Sales Tax"
    },
    "receipt_number": "REC-001",
    "processed_at": "2025-09-12T14:35:00Z"
  }
}
```

---

### Expense Management

#### `POST /api/save-expense`
Save extracted expense data to Firestore.

**Request:**
```json
{
  "user_id": "user123",
  "expense_data": {
    "total_amount": 14.53,
    "merchant_name": "Test Restaurant",
    "category": "Food & Dining",
    "date": "2025-09-12",
    "items": [...],
    // ... other expense fields
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "expense_doc_id",
    // ... saved expense data
  }
}
```

#### `GET /api/expenses/{user_id}`
Get user's expenses with optional filtering.

**Query Parameters:**
- `limit`: Number of expenses (default: 50, max: 200)
- `start_date`: Start date filter (YYYY-MM-DD)
- `end_date`: End date filter (YYYY-MM-DD)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "expense_id",
      "total_amount": 14.53,
      "merchant_name": "Test Restaurant",
      "category": "Food & Dining",
      "date": "2025-09-12",
      "created_at": "2025-09-12T14:35:00Z"
    }
  ],
  "count": 1
}
```

#### `GET /api/expense/{expense_id}`
Get specific expense details.

#### `PUT /api/expense/{expense_id}`
Update existing expense.

#### `DELETE /api/expense/{expense_id}`
Soft delete an expense (requires user_id in request body).

---

### Analytics & Reporting

#### `GET /api/user-summary/{user_id}`
Get user's expense summary and analytics.

**Query Parameters:**
- `period`: Summary period (`week`, `month`, `year`)

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "user123",
    "period": "month",
    "total_amount": 1250.75,
    "total_transactions": 45,
    "average_transaction": 27.79,
    "category_breakdown": {
      "Food & Dining": 450.25,
      "Transportation": 300.00,
      "Shopping": 500.50
    },
    "top_merchants": [
      {
        "name": "Starbucks",
        "amount": 89.50
      }
    ]
  }
}
```

#### `GET /api/categories/{user_id}`
Get user's category-wise expense statistics.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "category": "Food & Dining",
      "amount": 450.25,
      "percentage": 36.0
    },
    {
      "category": "Transportation", 
      "amount": 300.00,
      "percentage": 24.0
    }
  ]
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "status": "error_type"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `422`: Unprocessable Entity (extraction failed)
- `500`: Internal Server Error
- `503`: Service Unavailable

## Authentication

Currently, the API uses simple user_id based identification. For production use, implement proper authentication:

1. Add JWT token validation
2. Implement user authentication endpoints
3. Add rate limiting
4. Set up CORS policies

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Firebase service account JSON path | Yes |
| `MODEL_PATH` | AI model path | No |
| `PORT` | Server port | No |
| `HOST` | Server host | No |
| `DEBUG` | Debug mode | No |

### Firebase Setup

1. Create a Firebase project
2. Enable Firestore Database
3. Generate service account credentials
4. Download the JSON file and set `GOOGLE_APPLICATION_CREDENTIALS`

### Gemini AI Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set `GEMINI_API_KEY` environment variable

## Testing

Run the comprehensive test suite:

```bash
# Start the server first
python combined_server.py

# In another terminal, run tests
python test_backend.py
```

The test script will verify:
- Health endpoints
- AI categorization
- Receipt scanning and processing
- Expense saving and retrieval
- User analytics

## Deployment

### Local Development
```bash
python combined_server.py
```

### Production Deployment

1. **Docker**: Create a Dockerfile for containerization
2. **Cloud Platforms**: Deploy to Heroku, Google Cloud Run, or AWS
3. **Environment**: Set production environment variables
4. **Security**: Add authentication and rate limiting
5. **Monitoring**: Set up logging and health checks

## Troubleshooting

### Common Issues

1. **Import Errors**: Install missing dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. **Firebase Connection**: Check service account credentials
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   ```

3. **Gemini API**: Verify API key and quota limits

4. **Model Loading**: Ensure AI model files are in correct location

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export DEBUG=True
python combined_server.py
```

## Support

For issues and questions:
1. Check the test results: `python test_backend.py`
2. Review logs for error details
3. Verify environment configuration
4. Ensure all dependencies are installed

---

*This documentation covers the complete Finze backend API. For frontend integration examples, see the ScannerDialog component updates.*