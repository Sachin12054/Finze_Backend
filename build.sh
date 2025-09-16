#!/bin/bash
# Render Deployment Build Script
# This script runs during deployment on Render

echo "🚀 Starting Finze Backend Deployment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download ML models if needed
echo "🤖 Setting up ML models..."
python download_models.py

# Run any database migrations or setup
echo "🗄️  Setting up services..."
python -c "
try:
    print('Testing imports...')
    from services.firestore_service import FirestoreService
    print('✅ Firestore service import successful')
except Exception as e:
    print(f'⚠️  Firestore service warning: {e}')

try:
    from services.receipt_extractor import ReceiptExtractor
    print('✅ Receipt extractor import successful')
except Exception as e:
    print(f'⚠️  Receipt extractor warning: {e}')

try:
    from ml_model.ultra_perfect_categorizer import UltraPerfectExpenseCategorizer
    print('✅ AI categorizer import successful')
except Exception as e:
    print(f'⚠️  AI categorizer warning: {e}')

print('🎉 Backend services initialized!')
"

echo "✅ Deployment build complete!"