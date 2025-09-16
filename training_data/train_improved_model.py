#!/usr/bin/env python3
"""
Improved model training script for expense categorization
Uses the comprehensive dataset to train a more accurate model
"""

import json
import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
import numpy as np
from torch.utils.data import DataLoader

class ImprovedExpenseDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[idx], dtype=torch.long)
        }

def load_improved_dataset():
    """Load the comprehensive dataset"""
    
    # First generate the dataset if it doesn't exist
    if not os.path.exists('training_data/comprehensive_dataset.json'):
        print("🔄 Generating comprehensive dataset...")
        from improved_dataset import save_training_data
        save_training_data()
    
    # Load the dataset
    with open('training_data/comprehensive_dataset.json', 'r') as f:
        data = json.load(f)
    
    # Load label mapping
    with open('training_data/label_mapping.json', 'r') as f:
        label_mapping = json.load(f)
    
    return data, label_mapping

def train_improved_model():
    """Train an improved model with better accuracy"""
    
    print("🚀 Starting improved model training...")
    
    # Load dataset
    data, label_mapping = load_improved_dataset()
    
    # Prepare data
    texts = [item['description'] for item in data]
    categories = [item['category'] for item in data]
    labels = [label_mapping[category] for category in categories]
    
    print(f"📊 Dataset size: {len(texts)} examples")
    print(f"🏷️  Categories: {len(label_mapping)}")
    
    # Split data with stratification for balanced sets
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Further split training into train and validation
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
    )
    
    print(f"🔄 Train: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    # Load tokenizer and model
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=len(label_mapping)
    )
    
    # Create datasets
    train_dataset = ImprovedExpenseDataset(X_train, y_train, tokenizer)
    val_dataset = ImprovedExpenseDataset(X_val, y_val, tokenizer)
    test_dataset = ImprovedExpenseDataset(X_test, y_test, tokenizer)
    
    # Training arguments with improved settings
    training_args = TrainingArguments(
        output_dir='./improved_model_training',
        num_train_epochs=5,  # Increased epochs
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=50,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=500,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_accuracy",
        greater_is_better=True,
        learning_rate=2e-5,  # Optimized learning rate
        fp16=True,  # Use mixed precision for faster training
        dataloader_num_workers=4,
        remove_unused_columns=False,
    )
    
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        accuracy = accuracy_score(labels, predictions)
        return {"accuracy": accuracy}
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
    
    # Train the model
    print("🔥 Training model...")
    trainer.train()
    
    # Evaluate on test set
    print("📊 Evaluating model...")
    test_results = trainer.evaluate(test_dataset)
    
    # Make predictions for detailed analysis
    predictions = trainer.predict(test_dataset)
    y_pred = np.argmax(predictions.predictions, axis=1)
    
    # Calculate detailed metrics
    accuracy = accuracy_score(y_test, y_pred)
    
    # Create reverse label mapping for readable results
    reverse_label_mapping = {v: k for k, v in label_mapping.items()}
    category_names = [reverse_label_mapping[i] for i in range(len(label_mapping))]
    
    print(f"\n🎯 Final Results:")
    print(f"   Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Detailed classification report
    print(f"\n📈 Classification Report:")
    report = classification_report(
        y_test, y_pred, 
        target_names=category_names,
        output_dict=True
    )
    
    for category, metrics in report.items():
        if isinstance(metrics, dict) and 'precision' in metrics:
            print(f"   {category}:")
            print(f"     Precision: {metrics['precision']:.3f}")
            print(f"     Recall: {metrics['recall']:.3f}")
            print(f"     F1-score: {metrics['f1-score']:.3f}")
    
    # Save the improved model
    output_dir = "models/improved_expense_categorizer"
    os.makedirs(output_dir, exist_ok=True)
    
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Save updated label mapping and config
    config = {
        "model_name": "improved_expense_categorizer",
        "num_labels": len(label_mapping),
        "accuracy": accuracy,
        "categories": list(label_mapping.keys()),
        "label_mapping": label_mapping,
        "training_examples": len(texts),
        "model_type": "distilbert-base-uncased"
    }
    
    with open(f"{output_dir}/config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    with open(f"{output_dir}/label_mapping.json", 'w') as f:
        json.dump(label_mapping, f, indent=2)
    
    print(f"\n💾 Model saved to: {output_dir}")
    print(f"🎯 Model accuracy: {accuracy*100:.2f}%")
    
    # Test with some example predictions
    print(f"\n🧪 Testing with examples:")
    test_examples = [
        "Bought groceries at Walmart",
        "iPhone 15 Pro purchase", 
        "Uber ride to airport",
        "Netflix subscription",
        "Electricity bill payment",
        "Doctor consultation fee"
    ]
    
    model.eval()
    with torch.no_grad():
        for example in test_examples:
            inputs = tokenizer(example, return_tensors="pt", truncation=True, padding=True)
            outputs = model(**inputs)
            predicted_class = torch.argmax(outputs.logits, dim=-1).item()
            confidence = torch.softmax(outputs.logits, dim=-1).max().item()
            predicted_category = reverse_label_mapping[predicted_class]
            
            print(f"   '{example}' → {predicted_category} ({confidence:.3f})")
    
    return accuracy, output_dir

if __name__ == "__main__":
    try:
        accuracy, model_path = train_improved_model()
        print(f"\n✅ Training completed successfully!")
        print(f"📊 Final accuracy: {accuracy*100:.2f}%")
        print(f"📁 Model saved at: {model_path}")
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
