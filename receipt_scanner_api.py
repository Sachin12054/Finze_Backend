"""
Flask Endpoints for Receipt Scanning and Expense Management
Handles image uploads, Gemini AI processing, and Firestore operations
"""

import os
import io
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import our custom services
from services.receipt_extractor import GeminiReceiptExtractor
from services.firestore_service import FirestoreService

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReceiptScannerAPI:
    """
    Flask API for receipt scanning and expense management
    """
    
    def __init__(self, gemini_api_key: str = None, firestore_service_account: str = None):
        """
        Initialize the Receipt Scanner API
        
        Args:
            gemini_api_key: Google Gemini API key
            firestore_service_account: Path to Firebase service account JSON
        """
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize services
        try:
            self.gemini_extractor = GeminiReceiptExtractor(api_key=gemini_api_key)
            logger.info("✅ Gemini Receipt Extractor initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.gemini_extractor = None
        
        try:
            self.firestore_service = FirestoreService(service_account_path=firestore_service_account)
            if self.firestore_service.is_connected():
                logger.info("✅ Firestore Service connected")
            else:
                logger.warning("⚠️ Firestore Service not connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {str(e)}")
            self.firestore_service = None
        
        # Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic', 'heif'}
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'gemini_ai': self.gemini_extractor is not None,
                    'firestore': self.firestore_service is not None and self.firestore_service.is_connected()
                },
                'supported_formats': list(self.allowed_extensions) if self.gemini_extractor else []
            })
        
        @self.app.route('/api/upload-receipt', methods=['POST'])
        def upload_receipt():
            """
            Upload and process receipt image
            
            Expected: multipart/form-data with 'image' file and optional 'user_id'
            Returns: Extracted expense data
            """
            try:
                # Check if Gemini service is available
                if not self.gemini_extractor:
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
                if not self._allowed_file(file.filename):
                    return jsonify({
                        'error': f'Unsupported file format. Allowed: {", ".join(self.allowed_extensions)}',
                        'status': 'invalid_format'
                    }), 400
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > self.max_file_size:
                    return jsonify({
                        'error': f'File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB',
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
                image_format = self._get_image_format(file.filename)
                
                logger.info(f"Processing receipt image for user {user_id}, format: {image_format}, size: {file_size} bytes")
                
                # Extract data using Gemini AI
                extracted_data = self.gemini_extractor.extract_receipt_data(image_data, image_format)
                
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
        
        @self.app.route('/api/save-expense', methods=['POST'])
        def save_expense():
            """
            Save extracted expense data to Firestore
            
            Expected: JSON with expense data and user_id
            Returns: Saved expense document
            """
            try:
                # Check if Firestore service is available
                if not self.firestore_service or not self.firestore_service.is_connected():
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
                saved_expense = self.firestore_service.save_expense(user_id, expense_data)
                
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
        
        @self.app.route('/api/expenses/<user_id>', methods=['GET'])
        def get_user_expenses(user_id):
            """
            Get user's expenses with optional filtering
            
            Query parameters:
            - limit: Number of expenses to return (default: 50)
            - start_date: Start date filter (YYYY-MM-DD)
            - end_date: End date filter (YYYY-MM-DD)
            """
            try:
                # Check if Firestore service is available
                if not self.firestore_service or not self.firestore_service.is_connected():
                    return jsonify({
                        'error': 'Database service not available',
                        'status': 'service_unavailable'
                    }), 503
                
                # Get query parameters
                limit = min(int(request.args.get('limit', 50)), 200)  # Max 200 expenses
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                # Get expenses from Firestore
                expenses = self.firestore_service.get_user_expenses(
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
        
        @self.app.route('/api/expense/<expense_id>', methods=['GET'])
        def get_expense_details(expense_id):
            """Get specific expense details by ID"""
            try:
                if not self.firestore_service or not self.firestore_service.is_connected():
                    return jsonify({
                        'error': 'Database service not available',
                        'status': 'service_unavailable'
                    }), 503
                
                expense = self.firestore_service.get_expense_by_id(expense_id)
                
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
        
        @self.app.route('/api/user-summary/<user_id>', methods=['GET'])
        def get_user_summary(user_id):
            """
            Get user's expense summary and analytics
            
            Query parameters:
            - period: Summary period ('week', 'month', 'year')
            """
            try:
                if not self.firestore_service or not self.firestore_service.is_connected():
                    return jsonify({
                        'error': 'Database service not available',
                        'status': 'service_unavailable'
                    }), 503
                
                period = request.args.get('period', 'month')
                if period not in ['week', 'month', 'year']:
                    period = 'month'
                
                summary = self.firestore_service.get_user_summary(user_id, period)
                
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
        
        @self.app.route('/api/categories/<user_id>', methods=['GET'])
        def get_category_stats(user_id):
            """Get user's category-wise expense statistics"""
            try:
                if not self.firestore_service or not self.firestore_service.is_connected():
                    return jsonify({
                        'error': 'Database service not available',
                        'status': 'service_unavailable'
                    }), 503
                
                stats = self.firestore_service.get_categories_stats(user_id)
                
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
        
        @self.app.route('/api/expense/<expense_id>', methods=['PUT'])
        def update_expense(expense_id):
            """Update existing expense"""
            try:
                if not self.firestore_service or not self.firestore_service.is_connected():
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
                
                success = self.firestore_service.update_expense(expense_id, data)
                
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
        
        @self.app.route('/api/expense/<expense_id>', methods=['DELETE'])
        def delete_expense(expense_id):
            """Delete (soft delete) expense"""
            try:
                if not self.firestore_service or not self.firestore_service.is_connected():
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
                
                success = self.firestore_service.delete_expense(expense_id, user_id)
                
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
    
    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _get_image_format(self, filename: str) -> str:
        """Get image format from filename"""
        if '.' not in filename:
            return 'jpeg'
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        # Map extensions to MIME types
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
    
    def run(self, host: str = '0.0.0.0', port: int = 8002, debug: bool = False):
        """Run the Flask application"""
        logger.info(f"🚀 Starting Receipt Scanner API Server...")
        logger.info(f"📍 Server will be available at: http://{host}:{port}")
        logger.info(f"📋 Available Endpoints:")
        logger.info(f"   GET  /api/health")
        logger.info(f"   POST /api/upload-receipt")
        logger.info(f"   POST /api/save-expense")
        logger.info(f"   GET  /api/expenses/<user_id>")
        logger.info(f"   GET  /api/expense/<expense_id>")
        logger.info(f"   PUT  /api/expense/<expense_id>")
        logger.info(f"   DELETE /api/expense/<expense_id>")
        logger.info(f"   GET  /api/user-summary/<user_id>")
        logger.info(f"   GET  /api/categories/<user_id>")
        
        self.app.run(host=host, port=port, debug=debug)


# Create and run the application
if __name__ == "__main__":
    # Get configuration from environment variables
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    firestore_service_account = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Create API instance
    api = ReceiptScannerAPI(
        gemini_api_key=gemini_api_key,
        firestore_service_account=firestore_service_account
    )
    
    # Run the server
    port = int(os.getenv('PORT', 8002))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    api.run(host=host, port=port, debug=debug)