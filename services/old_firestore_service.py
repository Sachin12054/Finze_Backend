"""
Firebase Firestore Integration Service
Handles saving and retrieving expense data from Firestore
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    firestore = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirestoreService:
    """
    Firebase Firestore service for expense management
    Handles all database operations for expenses, users, and analytics
    """
    
    def __init__(self, service_account_path: str = None):
        """
        Initialize Firestore service
        
        Args:
            service_account_path: Path to Firebase service account JSON file
        """
        self.db = None
        self.app = None
        
        if not firebase_admin:
            logger.error("Firebase Admin SDK not installed. Run: pip install firebase-admin")
            return
        
        try:
            # Initialize Firebase if not already done
            if not firebase_admin._apps:
                if service_account_path and os.path.exists(service_account_path):
                    # Use service account file
                    cred = credentials.Certificate(service_account_path)
                    self.app = firebase_admin.initialize_app(cred)
                else:
                    # Try to use default credentials or environment variables
                    try:
                        self.app = firebase_admin.initialize_app()
                    except Exception as e:
                        logger.error(f"Failed to initialize Firebase: {str(e)}")
                        logger.info("Make sure to set GOOGLE_APPLICATION_CREDENTIALS or provide service_account_path")
                        return
            else:
                self.app = firebase_admin.get_app()
            
            self.db = firestore.client()
            logger.info("Successfully connected to Firestore")
            
        except Exception as e:
            logger.error(f"Error initializing Firestore: {str(e)}")
            self.db = None
    
    def is_connected(self) -> bool:
        """
        Check if Firestore is properly connected
        
        Returns:
            True if connected, False otherwise
        """
        return self.db is not None
    
    def save_expense(self, user_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save extracted expense data to Firestore
        
        Args:
            user_id: User identifier
            expense_data: Extracted expense data from receipt
            
        Returns:
            Saved expense document with ID
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            # Prepare expense document
            expense_doc = {
                'user_id': user_id,
                'total_amount': float(expense_data.get('total_amount', 0.0)),
                'currency': expense_data.get('currency', 'USD'),
                'merchant_name': expense_data.get('merchant_name', 'Unknown'),
                'merchant_address': expense_data.get('merchant_address'),
                'date': expense_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'time': expense_data.get('time'),
                'category': expense_data.get('category', 'Other'),
                'subcategory': expense_data.get('subcategory'),
                'payment_method': expense_data.get('payment_method'),
                'receipt_number': expense_data.get('receipt_number'),
                'notes': expense_data.get('notes'),
                'extraction_status': expense_data.get('extraction_status', 'success'),
                'confidence_score': float(expense_data.get('confidence_score', 0.8)),
                'processed_at': expense_data.get('processed_at', datetime.now().isoformat()),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
            }
            
            # Add items as subcollection data
            items = expense_data.get('items', [])
            if items:
                expense_doc['items'] = [
                    {
                        'name': item.get('name', ''),
                        'quantity': int(item.get('quantity', 1)),
                        'unit_price': float(item.get('unit_price', 0.0)),
                        'total_price': float(item.get('total_price', 0.0)),
                        'category': item.get('category', 'Other')
                    }
                    for item in items
                ]
                expense_doc['items_count'] = len(items)
            else:
                expense_doc['items'] = []
                expense_doc['items_count'] = 0
            
            # Add tax details
            tax_details = expense_data.get('tax_details', {})
            if tax_details:
                expense_doc['tax_amount'] = float(tax_details.get('tax_amount', 0.0))
                expense_doc['tax_rate'] = float(tax_details.get('tax_rate', 0.0))
                expense_doc['tax_type'] = tax_details.get('tax_type', '')
            
            # Add discounts
            discounts = expense_data.get('discounts', [])
            if discounts:
                expense_doc['discounts'] = [
                    {
                        'description': discount.get('description', ''),
                        'amount': float(discount.get('amount', 0.0)),
                        'type': discount.get('type', 'fixed')
                    }
                    for discount in discounts
                ]
                expense_doc['total_discount'] = sum(d.get('amount', 0) for d in discounts)
            
            # Add additional charges
            additional_charges = expense_data.get('additional_charges', [])
            if additional_charges:
                expense_doc['additional_charges'] = [
                    {
                        'description': charge.get('description', ''),
                        'amount': float(charge.get('amount', 0.0))
                    }
                    for charge in additional_charges
                ]
                expense_doc['total_additional_charges'] = sum(c.get('amount', 0) for c in additional_charges)
            
            # Save to Firestore
            doc_ref = self.db.collection('expenses').add(expense_doc)
            expense_id = doc_ref[1].id
            
            # Update user's expense summary
            self._update_user_summary(user_id, expense_doc)
            
            logger.info(f"Saved expense {expense_id} for user {user_id}")
            
            # Return saved document with ID (replace SERVER_TIMESTAMP for JSON serialization)
            expense_doc['id'] = expense_id
            expense_doc['created_at'] = datetime.now().isoformat()
            expense_doc['updated_at'] = datetime.now().isoformat()
            return expense_doc
            
        except Exception as e:
            logger.error(f"Error saving expense: {str(e)}")
            raise Exception(f"Failed to save expense: {str(e)}")
    
    def get_user_expenses(self, user_id: str, limit: int = 50, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get user's expenses with optional date filtering
        
        Args:
            user_id: User identifier
            limit: Maximum number of expenses to return
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            List of expense documents
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            query = self.db.collection('expenses').where('user_id', '==', user_id)
            
            # Add date filters if provided
            if start_date:
                query = query.where('date', '>=', start_date)
            if end_date:
                query = query.where('date', '<=', end_date)
            
            # Order by date (newest first) and limit
            query = query.order_by('date', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            
            expenses = []
            for doc in docs:
                expense_data = doc.to_dict()
                expense_data['id'] = doc.id
                expenses.append(expense_data)
            
            logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}")
            return expenses
            
        except Exception as e:
            logger.error(f"Error getting user expenses: {str(e)}")
            raise Exception(f"Failed to get expenses: {str(e)}")
    
    def get_expense_by_id(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific expense by ID
        
        Args:
            expense_id: Expense document ID
            
        Returns:
            Expense document or None if not found
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            doc_ref = self.db.collection('expenses').document(expense_id)
            doc = doc_ref.get()
            
            if doc.exists:
                expense_data = doc.to_dict()
                expense_data['id'] = doc.id
                return expense_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting expense {expense_id}: {str(e)}")
            raise Exception(f"Failed to get expense: {str(e)}")
    
    def update_expense(self, expense_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update existing expense
        
        Args:
            expense_id: Expense document ID
            update_data: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.db.collection('expenses').document(expense_id)
            doc_ref.update(update_data)
            
            logger.info(f"Updated expense {expense_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating expense {expense_id}: {str(e)}")
            return False
    
    def delete_expense(self, expense_id: str, user_id: str) -> bool:
        """
        Delete expense (soft delete by marking as deleted)
        
        Args:
            expense_id: Expense document ID
            user_id: User identifier for verification
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            doc_ref = self.db.collection('expenses').document(expense_id)
            doc = doc_ref.get()
            
            if doc.exists and doc.to_dict().get('user_id') == user_id:
                # Soft delete
                doc_ref.update({
                    'deleted': True,
                    'deleted_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                
                logger.info(f"Deleted expense {expense_id}")
                return True
            else:
                logger.warning(f"Expense {expense_id} not found or access denied")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id}: {str(e)}")
            return False
    
    def get_user_summary(self, user_id: str, period: str = 'month') -> Dict[str, Any]:
        """
        Get user's expense summary and analytics
        
        Args:
            user_id: User identifier
            period: Summary period ('week', 'month', 'year')
            
        Returns:
            Summary data including totals, categories, trends
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            # Calculate date range based on period
            now = datetime.now()
            if period == 'week':
                start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            elif period == 'month':
                start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            elif period == 'year':
                start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Get expenses for the period
            expenses = self.get_user_expenses(user_id, limit=1000, start_date=start_date)
            
            # Calculate summary
            total_amount = sum(expense.get('total_amount', 0) for expense in expenses)
            total_transactions = len(expenses)
            
            # Category breakdown
            category_totals = {}
            for expense in expenses:
                category = expense.get('category', 'Other')
                category_totals[category] = category_totals.get(category, 0) + expense.get('total_amount', 0)
            
            # Top merchants
            merchant_totals = {}
            for expense in expenses:
                merchant = expense.get('merchant_name', 'Unknown')
                merchant_totals[merchant] = merchant_totals.get(merchant, 0) + expense.get('total_amount', 0)
            
            top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Average transaction amount
            avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
            
            summary = {
                'user_id': user_id,
                'period': period,
                'start_date': start_date,
                'end_date': now.strftime('%Y-%m-%d'),
                'total_amount': round(total_amount, 2),
                'total_transactions': total_transactions,
                'average_transaction': round(avg_transaction, 2),
                'category_breakdown': {k: round(v, 2) for k, v in category_totals.items()},
                'top_merchants': [{'name': name, 'amount': round(amount, 2)} for name, amount in top_merchants],
                'generated_at': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating user summary: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    def _update_user_summary(self, user_id: str, expense_data: Dict[str, Any]):
        """
        Update user's overall expense summary (cached data for quick access)
        
        Args:
            user_id: User identifier
            expense_data: New expense data
        """
        try:
            user_ref = self.db.collection('user_summaries').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                current_data = user_doc.to_dict()
            else:
                current_data = {
                    'total_expenses': 0.0,
                    'total_transactions': 0,
                    'categories': {},
                    'first_expense_date': expense_data.get('date'),
                    'created_at': firestore.SERVER_TIMESTAMP
                }
            
            # Update totals
            current_data['total_expenses'] += float(expense_data.get('total_amount', 0))
            current_data['total_transactions'] += 1
            current_data['last_expense_date'] = expense_data.get('date')
            current_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Update category totals
            category = expense_data.get('category', 'Other')
            if 'categories' not in current_data:
                current_data['categories'] = {}
            current_data['categories'][category] = current_data['categories'].get(category, 0) + float(expense_data.get('total_amount', 0))
            
            # Save updated summary
            user_ref.set(current_data)
            
        except Exception as e:
            logger.error(f"Error updating user summary: {str(e)}")
            # Don't raise exception here as it's not critical for the main operation
    
    def get_categories_stats(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get category-wise expense statistics
        
        Args:
            user_id: User identifier
            
        Returns:
            List of category statistics
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            # Get user's expense summary
            user_ref = self.db.collection('user_summaries').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return []
            
            user_data = user_doc.to_dict()
            categories = user_data.get('categories', {})
            total_amount = user_data.get('total_expenses', 0)
            
            # Convert to list with percentages
            category_stats = []
            for category, amount in categories.items():
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                category_stats.append({
                    'category': category,
                    'amount': round(amount, 2),
                    'percentage': round(percentage, 2)
                })
            
            # Sort by amount (highest first)
            category_stats.sort(key=lambda x: x['amount'], reverse=True)
            
            return category_stats
            
        except Exception as e:
            logger.error(f"Error getting category stats: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    # This would be used for testing the service
    firestore_service = FirestoreService()
    if firestore_service.is_connected():
        print("Successfully connected to Firestore")
    else:
        print("Failed to connect to Firestore")