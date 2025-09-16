"""
Enhanced Finze Backend - Production Ready
Combines AI categorization, receipt scanning, and expense management
This is the integrated version that replaces the original app.py
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing AI categorization logic
try:
    from ml_model.ultra_perfect_categorizer import UltraPerfectExpenseCategorizer
    USING_ULTRA_PERFECT_MODEL = True
    USING_PERFECT_MODEL = False
    USING_IMPROVED_MODEL = False
    print("🚀 Using ULTRA-PERFECT high-confidence categorizer")
except ImportError:
    try:
        from ml_model.perfect_categorizer import PerfectExpenseCategorizer
        USING_ULTRA_PERFECT_MODEL = False
        USING_PERFECT_MODEL = True
        USING_IMPROVED_MODEL = False
        print("🎯 Using perfect high-confidence categorizer")
    except ImportError:
        try:
            from ml_model.improved_transformer_categorizer import ImprovedTransformerCategorizer
            USING_ULTRA_PERFECT_MODEL = False
            USING_PERFECT_MODEL = False
            USING_IMPROVED_MODEL = True
            print("🚀 Using improved transformer categorizer")
        except ImportError:
            try:
                from ml_model.transformer_categorizer import TransformerCategorizer
                USING_ULTRA_PERFECT_MODEL = False
                USING_PERFECT_MODEL = False
                USING_IMPROVED_MODEL = False
                print("⚠️  Using original transformer categorizer")
            except ImportError:
                print("❌ No AI categorization models found")
                USING_ULTRA_PERFECT_MODEL = False
                USING_PERFECT_MODEL = False
                USING_IMPROVED_MODEL = False

# Import receipt scanning services
try:
    from services.receipt_extractor import GeminiReceiptExtractor
    from services.firestore_service import FirestoreService
    RECEIPT_SCANNING_AVAILABLE = True
    print("✅ Receipt scanning services loaded")
except ImportError as e:
    print(f"⚠️ Receipt scanning services not available: {str(e)}")
    RECEIPT_SCANNING_AVAILABLE = False

import csv
import io
import uuid
import mimetypes
import logging
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/expense_distilbert')
PORT = int(os.environ.get('PORT', 8001))
HOST = os.environ.get('HOST', '0.0.0.0')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# File upload configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic', 'heif'}

# Initialize services
categorizer = None
gemini_extractor = None
firestore_service = None

def init_ai_categorizer():
    """Initialize AI categorization model"""
    global categorizer
    print(f"🤖 Loading AI model from: {MODEL_PATH}")
    try:
        if USING_ULTRA_PERFECT_MODEL:
            categorizer = UltraPerfectExpenseCategorizer()
        elif USING_PERFECT_MODEL:
            categorizer = PerfectExpenseCategorizer()
        elif USING_IMPROVED_MODEL:
            categorizer = ImprovedTransformerCategorizer(model_path=MODEL_PATH)
        else:
            categorizer = TransformerCategorizer(model_path=MODEL_PATH)
        
        print(f"✅ AI Model loaded successfully!")
        if categorizer:
            print(f"📋 Available categories: {', '.join(categorizer.get_categories())}")
    except Exception as e:
        print(f"❌ Error loading AI model: {e}")
        categorizer = None

def init_receipt_services():
    """Initialize receipt scanning services"""
    global gemini_extractor, firestore_service
    
    if not RECEIPT_SCANNING_AVAILABLE:
        print("⚠️ Receipt scanning services not available")
        return
    
    try:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        firestore_service_account = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Initialize Gemini extractor
        if gemini_api_key:
            gemini_extractor = GeminiReceiptExtractor(api_key=gemini_api_key)
            print("✅ Gemini Receipt Extractor initialized")
        else:
            print("⚠️ GEMINI_API_KEY not found - receipt scanning disabled")
        
        # Initialize Firestore service
        firestore_service = FirestoreService(service_account_path=firestore_service_account)
        if firestore_service.is_connected():
            print("✅ Firestore Service connected")
        else:
            print("⚠️ Firestore Service not connected")
            
    except Exception as e:
        print(f"❌ Error initializing receipt services: {str(e)}")
        gemini_extractor = None
        firestore_service = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_format(filename):
    """Get image format from filename"""
    if '.' not in filename:
        return 'jpeg'
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    format_mapping = {
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
        'png': 'png',
        'gif': 'gif',
        'bmp': 'bmp',
        'webp': 'webp',
        'heic': 'heic',
        'heif': 'heif'
    }
    
    return format_mapping.get(extension, 'jpeg')

# === ROUTES ===

@app.route('/api/health', methods=['GET'])
def health():
    """Comprehensive health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'services': {
            'ai_categorization': categorizer is not None,
            'receipt_scanning': gemini_extractor is not None,
            'firestore': firestore_service is not None and firestore_service.is_connected() if firestore_service else False
        },
        'ai_model': {
            'loaded': categorizer is not None,
            'type': ('ultra-perfect' if USING_ULTRA_PERFECT_MODEL else 
                    ('perfect' if USING_PERFECT_MODEL else 
                     ('improved' if USING_IMPROVED_MODEL else 'original'))),
            'categories': categorizer.get_categories() if categorizer else []
        },
        'receipt_scanning': {
            'available': RECEIPT_SCANNING_AVAILABLE and gemini_extractor is not None,
            'supported_formats': list(ALLOWED_EXTENSIONS) if RECEIPT_SCANNING_AVAILABLE else []
        }
    })

# === AI CATEGORIZATION ENDPOINTS ===

@app.route('/api/categorize', methods=['POST'])
def categorize():
    """Single expense categorization"""
    if not categorizer:
        return jsonify({'error': 'AI categorization model not loaded'}), 500
    
    try:
        data = request.json
        description = data.get('description', '')
        amount = data.get('amount', None)
        
        # Use appropriate prediction method based on model type
        if USING_ULTRA_PERFECT_MODEL or USING_PERFECT_MODEL or USING_IMPROVED_MODEL:
            result = categorizer.predict(description, amount)
        else:
            # Fallback to original method
            merchant = data.get('merchant_name', '')
            result = categorizer.predict_category(merchant, description, amount or 0.0)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categorize-batch', methods=['POST'])
def categorize_batch():
    """Batch expense categorization"""
    if not categorizer:
        return jsonify({'error': 'AI categorization model not loaded'}), 500
    
    try:
        items = request.json.get('items', [])
        
        if USING_ULTRA_PERFECT_MODEL or USING_PERFECT_MODEL or USING_IMPROVED_MODEL:
            # Use enhanced batch prediction
            descriptions = [item.get('description', '') for item in items]
            amounts = [item.get('amount', None) for item in items]
            results = categorizer.predict_batch(descriptions, amounts)
        else:
            # Fallback to original method
            results = []
            for item in items:
                result = categorizer.predict_category(
                    item.get('merchant_name', ''), 
                    item.get('description', ''), 
                    item.get('amount', 0.0)
                )
                results.append(result)
        
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/correction', methods=['POST'])
def correction():
    """Collect user corrections for active learning"""
    try:
        correction_data = request.json
        
        # Add correction to enhanced models if available
        if (USING_ULTRA_PERFECT_MODEL or USING_PERFECT_MODEL or USING_IMPROVED_MODEL) and categorizer:
            categorizer.add_correction(
                correction_data.get('description', ''),
                correction_data.get('correct_category', ''),
                correction_data.get('amount', None)
            )
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Append correction to CSV file
        with open('data/corrections.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                correction_data.get('merchant_name', ''),
                correction_data.get('description', ''),
                correction_data.get('amount', 0.0),
                correction_data.get('correct_category', '')
            ])
        
        print(f"📝 Correction saved: {correction_data.get('description')} -> {correction_data.get('correct_category')}")
        return jsonify({'status': 'ok', 'message': 'Correction saved successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all available categories"""
    if not categorizer:
        return jsonify({'error': 'AI categorization model not loaded'}), 500
    
    return jsonify({'categories': categorizer.get_categories()})

# === RECEIPT SCANNING ENDPOINTS ===

@app.route('/api/upload-receipt', methods=['POST'])
def upload_receipt():
    """Upload and process receipt image"""
    try:
        # Check if Gemini service is available
        if not gemini_extractor:
            return jsonify({
                'error': 'Receipt extraction service not available',
                'status': 'service_unavailable'
            }), 503
        
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'status': 'missing_file'
            }), 400
        
        file = request.files['image']
        user_id = request.form.get('user_id', 'anonymous')
        
        # Validate file
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'no_file'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Unsupported file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
                'status': 'invalid_format'
            }), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB',
                'status': 'file_too_large'
            }), 400
        
        # Read image data
        image_data = file.read()
        if not image_data:
            return jsonify({
                'error': 'Empty file',
                'status': 'empty_file'
            }), 400
        
        # Determine image format
        image_format = get_image_format(file.filename)
        
        logger.info(f"Processing receipt image for user {user_id}, format: {image_format}, size: {file_size} bytes")
        
        # Extract data using Gemini AI
        extracted_data = gemini_extractor.extract_receipt_data(image_data, image_format)
        
        if extracted_data.get('extraction_status') == 'failed':
            return jsonify({
                'error': extracted_data.get('error', 'Failed to extract receipt data'),
                'status': 'extraction_failed',
                'data': extracted_data
            }), 422
        
        # Add processing metadata
        extracted_data['user_id'] = user_id
        extracted_data['file_size'] = file_size
        extracted_data['file_format'] = image_format
        extracted_data['processing_id'] = str(uuid.uuid4())
        
        logger.info(f"Successfully extracted receipt data: {extracted_data.get('merchant_name', 'Unknown')} - ${extracted_data.get('total_amount', 0)}")
        
        return jsonify({
            'status': 'success',
            'data': extracted_data,
            'message': 'Receipt processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        return jsonify({
            'error': f'Processing failed: {str(e)}',
            'status': 'processing_error'
        }), 500

@app.route('/api/save-expense', methods=['POST'])
def save_expense():
    """Save extracted expense data to Firestore"""
    try:
        # Check if Firestore service is available
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        data = request.json
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'missing_data'
            }), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'error': 'User ID is required',
                'status': 'missing_user_id'
            }), 400
        
        expense_data = data.get('expense_data', data)
        
        # Validate required expense fields
        if not expense_data.get('total_amount') and expense_data.get('total_amount') != 0:
            return jsonify({
                'error': 'Total amount is required',
                'status': 'missing_amount'
            }), 400
        
        logger.info(f"Saving expense for user {user_id}: {expense_data.get('merchant_name', 'Unknown')} - ${expense_data.get('total_amount', 0)}")
        
        # Save to Firestore
        saved_expense = firestore_service.save_expense(user_id, expense_data)
        
        return jsonify({
            'status': 'success',
            'data': saved_expense,
            'message': 'Expense saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving expense: {str(e)}")
        return jsonify({
            'error': f'Failed to save expense: {str(e)}',
            'status': 'save_error'
        }), 500

@app.route('/api/expenses/<user_id>', methods=['GET'])
def get_user_expenses(user_id):
    """Get user's expenses with optional filtering"""
    try:
        # Check if Firestore service is available
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 200)  # Max 200 expenses
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get expenses from Firestore
        expenses = firestore_service.get_user_expenses(
            user_id=user_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'status': 'success',
            'data': expenses,
            'count': len(expenses),
            'filters': {
                'limit': limit,
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user expenses: {str(e)}")
        return jsonify({
            'error': f'Failed to get expenses: {str(e)}',
            'status': 'fetch_error'
        }), 500

@app.route('/api/expense/<expense_id>', methods=['GET'])
def get_expense_details(expense_id):
    """Get specific expense details by ID"""
    try:
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        expense = firestore_service.get_expense_by_id(expense_id)
        
        if not expense:
            return jsonify({
                'error': 'Expense not found',
                'status': 'not_found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': expense
        })
        
    except Exception as e:
        logger.error(f"Error getting expense details: {str(e)}")
        return jsonify({
            'error': f'Failed to get expense: {str(e)}',
            'status': 'fetch_error'
        }), 500

@app.route('/api/user-summary/<user_id>', methods=['GET'])
def get_user_summary(user_id):
    """Get user's expense summary and analytics"""
    try:
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        period = request.args.get('period', 'month')
        if period not in ['week', 'month', 'year']:
            period = 'month'
        
        summary = firestore_service.get_user_summary(user_id, period)
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting user summary: {str(e)}")
        return jsonify({
            'error': f'Failed to get summary: {str(e)}',
            'status': 'fetch_error'
        }), 500

@app.route('/api/categories/<user_id>', methods=['GET'])
def get_category_stats(user_id):
    """Get user's category-wise expense statistics"""
    try:
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        stats = firestore_service.get_categories_stats(user_id)
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting category stats: {str(e)}")
        return jsonify({
            'error': f'Failed to get category stats: {str(e)}',
            'status': 'fetch_error'
        }), 500

@app.route('/api/expense/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update existing expense"""
    try:
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        data = request.json
        if not data:
            return jsonify({
                'error': 'No update data provided',
                'status': 'missing_data'
            }), 400
        
        success = firestore_service.update_expense(expense_id, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Expense updated successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to update expense',
                'status': 'update_failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating expense: {str(e)}")
        return jsonify({
            'error': f'Failed to update expense: {str(e)}',
            'status': 'update_error'
        }), 500

@app.route('/api/expense/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete (soft delete) expense"""
    try:
        if not firestore_service or not firestore_service.is_connected():
            return jsonify({
                'error': 'Database service not available',
                'status': 'service_unavailable'
            }), 503
        
        data = request.json or {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'error': 'User ID is required for deletion',
                'status': 'missing_user_id'
            }), 400
        
        success = firestore_service.delete_expense(expense_id, user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Expense deleted successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to delete expense or access denied',
                'status': 'delete_failed'
            }), 400
            
    except Exception as e:
        logger.error(f"Error deleting expense: {str(e)}")
        return jsonify({
            'error': f'Failed to delete expense: {str(e)}',
            'status': 'delete_error'
        }), 500

# Initialize services
print("🚀 Initializing Finze Enhanced Backend...")
init_ai_categorizer()
init_receipt_services()

if __name__ == '__main__':
    print(f"🚀 Starting Enhanced Finze Backend Server...")
    print(f"📍 Server will be available at: http://{HOST}:{PORT}")
    print(f"🔧 Services Status:")
    print(f"   ✅ AI Categorization: {'Available' if categorizer else 'Not Available'}")
    print(f"   ✅ Receipt Scanning: {'Available' if RECEIPT_SCANNING_AVAILABLE and gemini_extractor else 'Not Available'}")
    print(f"   ✅ Firestore Database: {'Connected' if firestore_service and firestore_service.is_connected() else 'Not Connected'}")
    print(f"📋 Available Endpoints:")
    print(f"   GET  /api/health - Comprehensive health check")
    print(f"   🧠 AI Categorization:")
    print(f"       GET  /api/categories")
    print(f"       POST /api/categorize")
    print(f"       POST /api/categorize-batch")
    print(f"       POST /api/correction")
    if RECEIPT_SCANNING_AVAILABLE and gemini_extractor:
        print(f"   📷 Receipt Scanning:")
        print(f"       POST /api/upload-receipt")
        print(f"       POST /api/save-expense")
        print(f"       GET  /api/expenses/<user_id>")
        print(f"       GET  /api/expense/<expense_id>")
        print(f"       PUT  /api/expense/<expense_id>")
        print(f"       DELETE /api/expense/<expense_id>")
        print(f"       GET  /api/user-summary/<user_id>")
        print(f"       GET  /api/categories/<user_id>")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
