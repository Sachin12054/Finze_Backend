#!/usr/bin/env python3
"""
Model Download Script for Render Deployment
Downloads the large DistilBERT model from cloud storage during deployment
"""

import os
import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_model():
    """Download and extract the expense categorization model"""
    
    model_dir = Path("models/expense_distilbert")
    
    # Check if model already exists
    if model_dir.exists() and (model_dir / "pytorch_model.bin").exists():
        print("✅ Model already exists, skipping download")
        return True
    
    print("📥 Downloading expense categorization model...")
    
    # Create models directory
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # You'll need to upload your model to a cloud service (Google Drive, Dropbox, etc.)
    # and replace this URL with the actual download link
    
    # Option 1: If you have the model hosted somewhere
    model_url = os.environ.get('MODEL_DOWNLOAD_URL')
    
    if not model_url:
        print("⚠️  No MODEL_DOWNLOAD_URL found, creating minimal model files...")
        create_minimal_model(model_dir)
        return True
    
    try:
        # Download the model zip file
        zip_path = "temp_model.zip"
        print(f"Downloading from: {model_url}")
        urllib.request.urlretrieve(model_url, zip_path)
        
        # Extract the model
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("models/")
        
        # Clean up
        os.remove(zip_path)
        
        print("✅ Model downloaded and extracted successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("📝 Creating minimal model files as fallback...")
        create_minimal_model(model_dir)
        return False

def create_minimal_model(model_dir):
    """Create minimal model files for fallback"""
    
    # Create basic config.json
    config = {
        "architectures": ["DistilBertForSequenceClassification"],
        "model_type": "distilbert",
        "num_labels": 11,
        "id2label": {
            "0": "Food & Dining",
            "1": "Transportation",
            "2": "Shopping", 
            "3": "Entertainment",
            "4": "Technology",
            "5": "Bills & Utilities",
            "6": "Healthcare",
            "7": "Travel",
            "8": "Education",
            "9": "Business",
            "10": "Other"
        },
        "label2id": {
            "Food & Dining": 0,
            "Transportation": 1,
            "Shopping": 2,
            "Entertainment": 3,
            "Technology": 4,
            "Bills & Utilities": 5,
            "Healthcare": 6,
            "Travel": 7,
            "Education": 8,
            "Business": 9,
            "Other": 10
        }
    }
    
    import json
    with open(model_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Create label map
    label_map = {
        "Food & Dining": 0,
        "Transportation": 1,
        "Shopping": 2,
        "Entertainment": 3,
        "Technology": 4,
        "Bills & Utilities": 5,
        "Healthcare": 6,
        "Travel": 7,
        "Education": 8,
        "Business": 9,
        "Other": 10
    }
    
    with open(model_dir / "label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)
    
    print("✅ Minimal model files created")

if __name__ == "__main__":
    success = download_model()
    if success:
        print("🎉 Model setup complete!")
    else:
        print("⚠️  Using fallback model configuration")