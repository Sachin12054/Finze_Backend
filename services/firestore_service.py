"""
Updated Firebase Firestore Integration Service for new database structure
Handles saving and retrieving expense data with the new user-based collection structure
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
    Firebase Firestore service for expense management with new user-centric structure
    Handles all database operations for expenses, budgets, goals, and analytics
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
    
    def save_scanner_expense(self, user_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save scanned receipt expense data to the new user-based structure
        
        Args:
            user_id: User identifier
            expense_data: Extracted expense data from receipt
            
        Returns:
            Saved expense document with ID
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            # Generate expense ID
            expense_id = self._generate_id()
            
            # Prepare scanner expense document
            scanner_expense = {
                'expenseId': expense_id,
                'image_url': expense_data.get('image_url', ''),
                'extracted_text': expense_data.get('extracted_text', ''),
                'amount': float(expense_data.get('total_amount', 0.0)),
                'date': expense_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'category': expense_data.get('category', 'Other'),
                'merchant_name': expense_data.get('merchant_name', 'Unknown'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to users/{userId}/expenses/scanner/{expenseId}
            scanner_ref = self.db.collection('users').document(user_id)\
                .collection('expenses').document('scanner')\
                .collection('scanner').document(expense_id)
            scanner_ref.set(scanner_expense)
            
            # Add transaction history
            transaction_data = {
                'transactionId': self._generate_id(),
                'source': 'scanner',
                'reference_id': expense_id,
                'amount': scanner_expense['amount'],
                'date': scanner_expense['date'],
                'type': 'expense',
                'category': scanner_expense['category'],
                'description': f"Receipt scan: {scanner_expense['merchant_name']}",
                'created_at': datetime.now().isoformat()
            }
            
            transaction_ref = self.db.collection('users').document(user_id)\
                .collection('transaction_history').document(transaction_data['transactionId'])
            transaction_ref.set(transaction_data)
            
            logger.info(f"Saved scanner expense {expense_id} for user {user_id}")
            
            scanner_expense['id'] = expense_id
            return scanner_expense
            
        except Exception as e:
            logger.error(f"Error saving scanner expense: {str(e)}")
            raise Exception(f"Failed to save scanner expense: {str(e)}")
    
    def save_ai_categorized_expense(self, user_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save AI categorized expense data
        
        Args:
            user_id: User identifier
            expense_data: AI categorized expense data
            
        Returns:
            Saved expense document with ID
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            expense_id = self._generate_id()
            
            ai_expense = {
                'expenseId': expense_id,
                'raw_description': expense_data.get('description', ''),
                'predicted_category': expense_data.get('category', 'Other'),
                'amount': float(expense_data.get('amount', 0.0)),
                'confidence': float(expense_data.get('confidence', 0.8)),
                'date': expense_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to users/{userId}/expenses/ai_categorise/{expenseId}
            ai_ref = self.db.collection('users').document(user_id)\
                .collection('expenses').document('ai_categorise')\
                .collection('ai_categorise').document(expense_id)
            ai_ref.set(ai_expense)
            
            # Add transaction history
            transaction_data = {
                'transactionId': self._generate_id(),
                'source': 'ai_categorise',
                'reference_id': expense_id,
                'amount': ai_expense['amount'],
                'date': ai_expense['date'],
                'type': 'expense',
                'category': ai_expense['predicted_category'],
                'description': ai_expense['raw_description'],
                'created_at': datetime.now().isoformat()
            }
            
            transaction_ref = self.db.collection('users').document(user_id)\
                .collection('transaction_history').document(transaction_data['transactionId'])
            transaction_ref.set(transaction_data)
            
            logger.info(f"Saved AI categorized expense {expense_id} for user {user_id}")
            
            ai_expense['id'] = expense_id
            return ai_expense
            
        except Exception as e:
            logger.error(f"Error saving AI categorized expense: {str(e)}")
            raise Exception(f"Failed to save AI categorized expense: {str(e)}")
    
    def save_manual_expense(self, user_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save manual expense data
        
        Args:
            user_id: User identifier
            expense_data: Manual expense data
            
        Returns:
            Saved expense document with ID
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            expense_id = self._generate_id()
            
            manual_expense = {
                'expenseId': expense_id,
                'title': expense_data.get('title', ''),
                'amount': float(expense_data.get('amount', 0.0)),
                'category': expense_data.get('category', 'Other'),
                'date': expense_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'notes': expense_data.get('notes', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to users/{userId}/expenses/manual/{expenseId}
            manual_ref = self.db.collection('users').document(user_id)\
                .collection('expenses').document('manual')\
                .collection('manual').document(expense_id)
            manual_ref.set(manual_expense)
            
            # Add transaction history
            transaction_data = {
                'transactionId': self._generate_id(),
                'source': 'manual',
                'reference_id': expense_id,
                'amount': manual_expense['amount'],
                'date': manual_expense['date'],
                'type': 'expense',
                'category': manual_expense['category'],
                'description': manual_expense['title'],
                'created_at': datetime.now().isoformat()
            }
            
            transaction_ref = self.db.collection('users').document(user_id)\
                .collection('transaction_history').document(transaction_data['transactionId'])
            transaction_ref.set(transaction_data)
            
            logger.info(f"Saved manual expense {expense_id} for user {user_id}")
            
            manual_expense['id'] = expense_id
            return manual_expense
            
        except Exception as e:
            logger.error(f"Error saving manual expense: {str(e)}")
            raise Exception(f"Failed to save manual expense: {str(e)}")
    
    def get_user_expenses(self, user_id: str, expense_type: str = 'all', limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's expenses from the new structure
        
        Args:
            user_id: User identifier
            expense_type: Type of expenses ('manual', 'ai_categorise', 'scanner', 'all')
            limit: Maximum number of expenses to return
            
        Returns:
            List of expense documents
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            all_expenses = []
            
            if expense_type in ['manual', 'all']:
                manual_ref = self.db.collection('users').document(user_id)\
                    .collection('expenses').document('manual').collection('manual')\
                    .order_by('date', direction=firestore.Query.DESCENDING).limit(limit)
                manual_docs = manual_ref.stream()
                for doc in manual_docs:
                    expense_data = doc.to_dict()
                    expense_data['id'] = doc.id
                    expense_data['type'] = 'manual'
                    all_expenses.append(expense_data)
            
            if expense_type in ['ai_categorise', 'all']:
                ai_ref = self.db.collection('users').document(user_id)\
                    .collection('expenses').document('ai_categorise').collection('ai_categorise')\
                    .order_by('date', direction=firestore.Query.DESCENDING).limit(limit)
                ai_docs = ai_ref.stream()
                for doc in ai_docs:
                    expense_data = doc.to_dict()
                    expense_data['id'] = doc.id
                    expense_data['type'] = 'ai_categorise'
                    all_expenses.append(expense_data)
            
            if expense_type in ['scanner', 'all']:
                scanner_ref = self.db.collection('users').document(user_id)\
                    .collection('expenses').document('scanner').collection('scanner')\
                    .order_by('date', direction=firestore.Query.DESCENDING).limit(limit)
                scanner_docs = scanner_ref.stream()
                for doc in scanner_docs:
                    expense_data = doc.to_dict()
                    expense_data['id'] = doc.id
                    expense_data['type'] = 'scanner'
                    all_expenses.append(expense_data)
            
            # Sort all expenses by date
            all_expenses.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            logger.info(f"Retrieved {len(all_expenses)} expenses for user {user_id}")
            return all_expenses[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user expenses: {str(e)}")
            return []
    
    def get_user_analytics(self, user_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Get user's expense analytics
        
        Args:
            user_id: User identifier
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            Analytics data
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Get all expenses
            all_expenses = self.get_user_expenses(user_id, 'all', 1000)
            
            # Filter by date range
            filtered_expenses = [
                expense for expense in all_expenses
                if start_date <= expense.get('date', '') <= end_date
            ]
            
            total_amount = sum(expense.get('amount', 0) for expense in filtered_expenses)
            total_transactions = len(filtered_expenses)
            
            # Category breakdown
            category_totals = {}
            for expense in filtered_expenses:
                category = expense.get('category', 'Other')
                category_totals[category] = category_totals.get(category, 0) + expense.get('amount', 0)
            
            # Source breakdown
            source_totals = {}
            for expense in filtered_expenses:
                source = expense.get('type', 'unknown')
                source_totals[source] = source_totals.get(source, 0) + expense.get('amount', 0)
            
            # Average transaction amount
            avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
            
            analytics = {
                'user_id': user_id,
                'period': {'start_date': start_date, 'end_date': end_date},
                'total_amount': round(total_amount, 2),
                'total_transactions': total_transactions,
                'average_transaction': round(avg_transaction, 2),
                'category_breakdown': {k: round(v, 2) for k, v in category_totals.items()},
                'source_breakdown': {k: round(v, 2) for k, v in source_totals.items()},
                'generated_at': datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics: {str(e)}")
            return {}
    
    def create_or_update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Create or update user profile in the new structure
        
        Args:
            user_id: User identifier
            profile_data: Profile data to save
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            user_doc = {
                'uid': user_id,
                'email': profile_data.get('email', ''),
                'displayName': profile_data.get('displayName', ''),
                'profile': {
                    'avatar_url': profile_data.get('avatar_url', ''),
                    'phone': profile_data.get('phone', ''),
                    'currency': profile_data.get('currency', 'INR'),
                    'preferences': profile_data.get('preferences', {
                        'notifications': True,
                        'theme': 'auto',
                        'language': 'en',
                        'auto_categorize': True,
                        'budget_alerts': True
                    })
                },
                'created_at': profile_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            user_ref = self.db.collection('users').document(user_id)
            user_ref.set(user_doc, merge=True)
            
            logger.info(f"Created/updated user profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating user profile: {str(e)}")
            return False
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    def get_transaction_history(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get user's transaction history
        
        Args:
            user_id: User identifier
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction documents
        """
        if not self.db:
            raise Exception("Firestore not connected")
        
        try:
            transaction_ref = self.db.collection('users').document(user_id)\
                .collection('transaction_history')\
                .order_by('date', direction=firestore.Query.DESCENDING).limit(limit)
            
            transactions = []
            for doc in transaction_ref.stream():
                transaction_data = doc.to_dict()
                transaction_data['id'] = doc.id
                transactions.append(transaction_data)
            
            logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    # This would be used for testing the service
    firestore_service = FirestoreService()
    if firestore_service.is_connected():
        print("Successfully connected to Firestore with new structure")
        
        # Test creating a user profile
        test_user_id = "test_user_123"
        profile_data = {
            'email': 'test@example.com',
            'displayName': 'Test User',
            'currency': 'INR'
        }
        
        success = firestore_service.create_or_update_user_profile(test_user_id, profile_data)
        if success:
            print("✅ User profile created successfully")
        else:
            print("❌ Failed to create user profile")
    else:
        print("Failed to connect to Firestore")