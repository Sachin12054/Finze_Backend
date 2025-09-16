#!/usr/bin/env python3
"""
Updated transformer categorizer that works with your app's categories
Uses improved pattern matching and confidence scoring
"""

import json
import os
import pickle
import re
from typing import Dict, List, Tuple, Optional
import numpy as np

class ImprovedTransformerCategorizer:
    def __init__(self, model_path: str = "models/improved_expense_categorizer"):
        self.model_path = model_path
        self.categories = [
            'Food & Dining',
            'Transportation', 
            'Shopping',
            'Entertainment',
            'Technology',
            'Bills & Utilities',
            'Healthcare',
            'Travel',
            'Education',
            'Business',
            'Other'
        ]
        
        # Load comprehensive pattern mappings for high confidence predictions
        self.category_patterns = self._load_category_patterns()
        
        # Load training data for similarity matching
        self.training_examples = self._load_training_examples()
        
        print(f"✅ Improved categorizer loaded with {len(self.categories)} categories")
        print(f"📚 Using {len(self.training_examples)} training examples for matching")

    def _load_category_patterns(self) -> Dict[str, List[str]]:
        """Load comprehensive patterns for each category"""
        return {
            'Food & Dining': [
                r'\b(food|eat|lunch|dinner|breakfast|snack|meal|restaurant|cafe|coffee|pizza|burger|sandwich|grocery|groceries|supermarket|walmart|target|starbucks|mcdonalds|kfc|subway|dominos|bakery|kitchen|cooking|recipe|chef|dining|takeout|delivery|catering|tiffin|mess|canteen)\b',
                r'\b(drink|beverage|juice|soda|beer|wine|alcohol|water|milk|tea)\b',
                r'\b(fresh|organic|meat|vegetable|fruit|dairy|bread|rice|pasta|spice|ingredient)\b'
            ],
            'Transportation': [
                r'\b(uber|taxi|cab|bus|train|metro|flight|car|bike|auto|rickshaw|transport|travel|ride|fuel|petrol|diesel|gas|parking|toll|fare|ticket)\b',
                r'\b(rental|hire|service|maintenance|repair|insurance|registration|license|permit)\b',
                r'\b(airport|station|highway|bridge|vehicle|motorcycle|scooter|bicycle)\b'
            ],
            'Shopping': [
                r'\b(amazon|flipkart|shopping|purchase|buy|bought|order|delivery|clothes|clothing|shoes|dress|shirt|pants|jacket|fashion|style)\b',
                r'\b(electronics|appliance|furniture|decoration|home|kitchen|bedroom|living|garden|cleaning|personal|care|cosmetic|beauty|perfume)\b',
                r'\b(jewelry|watch|bag|wallet|accessories|sunglasses|gift|present|toy|game|sport|equipment|supplies)\b'
            ],
            'Entertainment': [
                r'\b(movie|cinema|theatre|theater|show|concert|music|festival|comedy|sports|game|ticket|entertainment|fun|leisure|hobby)\b',
                r'\b(netflix|spotify|amazon|prime|disney|youtube|subscription|streaming|video|audio|gaming|console|xbox|playstation)\b',
                r'\b(book|novel|magazine|newspaper|art|gallery|museum|exhibition|class|lesson|workshop|club|gym|fitness|yoga|swimming)\b'
            ],
            'Technology': [
                r'\b(iphone|android|phone|mobile|smartphone|laptop|computer|desktop|tablet|ipad|watch|smartwatch|tech|technology|electronic|digital)\b',
                r'\b(software|app|subscription|license|antivirus|cloud|storage|backup|upgrade|update|repair|service|fix)\b',
                r'\b(camera|headphone|speaker|bluetooth|wireless|charger|cable|accessory|device|gadget|smart|ai|iot)\b'
            ],
            'Bills & Utilities': [
                r'\b(bill|utility|electricity|water|gas|internet|wifi|phone|cable|tv|rent|mortgage|loan|emi|insurance|tax|fee|charge|payment)\b',
                r'\b(service|maintenance|society|security|deposit|connection|installation|renewal|registration|government|legal|professional)\b',
                r'\b(bank|credit|card|fine|penalty|admin|administrative|processing|handling|delivery|shipping)\b'
            ],
            'Healthcare': [
                r'\b(doctor|medical|hospital|clinic|health|medicine|drug|prescription|vitamin|supplement|treatment|surgery|operation|therapy)\b',
                r'\b(dental|dentist|eye|vision|glasses|contact|physiotherapy|massage|wellness|checkup|test|scan|xray|mri|ultrasound)\b',
                r'\b(pharmacy|medical|equipment|first|aid|emergency|ambulance|icu|lab|diagnostic|vaccination|mental|counseling)\b'
            ],
            'Travel': [
                r'\b(travel|trip|vacation|holiday|tour|flight|hotel|resort|cruise|package|booking|reservation|visa|passport|foreign|exchange)\b',
                r'\b(sightseeing|adventure|cultural|heritage|pilgrimage|conference|seminar|training|study|abroad|international|domestic)\b',
                r'\b(luggage|baggage|gear|accommodation|transport|local|guide|excursion|safari)\b'
            ],
            'Education': [
                r'\b(school|college|university|education|course|class|training|workshop|skill|development|certification|degree|diploma)\b',
                r'\b(fees|tuition|admission|registration|exam|test|book|study|material|stationery|uniform|laboratory|library)\b',
                r'\b(scholarship|loan|tutoring|coaching|entrance|competitive|online|learning|student|academic|research)\b'
            ],
            'Business': [
                r'\b(business|office|work|professional|company|corporate|commercial|enterprise|startup|entrepreneur|meeting|conference)\b',
                r'\b(supplies|equipment|furniture|software|license|marketing|advertising|promotion|legal|accounting|consulting)\b',
                r'\b(registration|permit|insurance|employee|staff|team|client|customer|networking|membership|subscription)\b'
            ],
            'Other': [
                r'\b(misc|miscellaneous|other|unknown|unategorized|cash|withdrawal|atm|transfer|investment|stock|mutual|fund|gold|charity|donation|gift|emergency|urgent|temporary|personal|random)\b'
            ]
        }

    def _load_training_examples(self) -> Dict[str, List[str]]:
        """Load training examples for similarity matching"""
        try:
            with open('training_data/comprehensive_dataset.json', 'r') as f:
                data = json.load(f)
            
            examples_by_category = {}
            for item in data:
                category = item['category']
                if category not in examples_by_category:
                    examples_by_category[category] = []
                examples_by_category[category].append(item['description'].lower())
            
            return examples_by_category
        except FileNotFoundError:
            print("⚠️  Training data not found, using pattern matching only")
            return {}

    def _calculate_pattern_confidence(self, description: str, category: str) -> float:
        """Calculate confidence based on pattern matching"""
        patterns = self.category_patterns.get(category, [])
        description_lower = description.lower()
        
        matches = 0
        total_patterns = len(patterns)
        
        if total_patterns == 0:
            return 0.1
        
        for pattern in patterns:
            if re.search(pattern, description_lower):
                matches += 1
        
        # Base confidence from pattern matching
        pattern_confidence = matches / total_patterns
        
        # Boost confidence for exact keyword matches
        keywords = self._extract_keywords(description_lower)
        category_keywords = self._get_category_keywords(category)
        
        keyword_matches = len(set(keywords) & set(category_keywords))
        keyword_boost = min(keyword_matches * 0.1, 0.3)
        
        return min(pattern_confidence + keyword_boost, 0.95)

    def _calculate_similarity_confidence(self, description: str, category: str) -> float:
        """Calculate confidence based on similarity to training examples"""
        if category not in self.training_examples:
            return 0.0
        
        description_lower = description.lower()
        examples = self.training_examples[category]
        
        max_similarity = 0.0
        for example in examples[:20]:  # Check top 20 examples for performance
            similarity = self._simple_similarity(description_lower, example)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words and extract keywords
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]

    def _get_category_keywords(self, category: str) -> List[str]:
        """Get key terms for each category"""
        category_keywords = {
            'Food & Dining': ['food', 'eat', 'lunch', 'dinner', 'breakfast', 'restaurant', 'cafe', 'coffee', 'grocery', 'meal', 'snack', 'drink', 'beverage'],
            'Transportation': ['uber', 'taxi', 'bus', 'train', 'flight', 'car', 'bike', 'fuel', 'petrol', 'ride', 'transport', 'travel', 'parking'],
            'Shopping': ['amazon', 'shopping', 'buy', 'purchase', 'clothes', 'shoes', 'electronics', 'home', 'appliance', 'order', 'delivery'],
            'Entertainment': ['movie', 'cinema', 'music', 'concert', 'show', 'game', 'netflix', 'spotify', 'entertainment', 'fun', 'hobby', 'gym'],
            'Technology': ['phone', 'laptop', 'computer', 'software', 'app', 'tech', 'device', 'gadget', 'electronic', 'digital', 'camera', 'headphone'],
            'Bills & Utilities': ['bill', 'electricity', 'water', 'gas', 'internet', 'rent', 'insurance', 'tax', 'payment', 'utility', 'service'],
            'Healthcare': ['doctor', 'medical', 'hospital', 'medicine', 'health', 'treatment', 'pharmacy', 'dental', 'checkup', 'therapy'],
            'Travel': ['travel', 'trip', 'vacation', 'hotel', 'flight', 'tour', 'holiday', 'booking', 'visa', 'luggage', 'resort'],
            'Education': ['school', 'college', 'education', 'course', 'class', 'training', 'book', 'study', 'fees', 'tuition', 'exam'],
            'Business': ['business', 'office', 'work', 'professional', 'meeting', 'supplies', 'equipment', 'marketing', 'client', 'company'],
            'Other': ['misc', 'other', 'cash', 'atm', 'investment', 'charity', 'gift', 'emergency', 'personal', 'random']
        }
        return category_keywords.get(category, [])

    def predict(self, description: str, amount: Optional[float] = None) -> Dict:
        """Predict category with improved confidence scoring"""
        if not description or not description.strip():
            return {
                'category': 'Other',
                'confidence': 0.5,
                'all_probabilities': {cat: 0.1 for cat in self.categories},
                'suggested': [('Other', 0.5)]
            }
        
        # Calculate confidence for each category
        category_scores = {}
        
        for category in self.categories:
            # Pattern-based confidence
            pattern_conf = self._calculate_pattern_confidence(description, category)
            
            # Similarity-based confidence
            similarity_conf = self._calculate_similarity_confidence(description, category)
            
            # Combine confidences with weights
            combined_confidence = (pattern_conf * 0.7) + (similarity_conf * 0.3)
            
            # Amount-based adjustments
            if amount is not None:
                combined_confidence = self._adjust_confidence_by_amount(combined_confidence, category, amount)
            
            category_scores[category] = max(combined_confidence, 0.05)  # Minimum confidence
        
        # Normalize scores to sum to 1.0
        total_score = sum(category_scores.values())
        if total_score > 0:
            normalized_scores = {cat: score/total_score for cat, score in category_scores.items()}
        else:
            normalized_scores = {cat: 1.0/len(self.categories) for cat in self.categories}
        
        # Get top prediction
        top_category = max(normalized_scores, key=normalized_scores.get)
        top_confidence = normalized_scores[top_category]
        
        # Create suggested categories (top 3)
        sorted_categories = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        suggested = sorted_categories[:3]
        
        # Boost confidence if it's a clear match
        if top_confidence > 0.6:
            top_confidence = min(top_confidence * 1.2, 0.95)
        
        return {
            'category': top_category,
            'confidence': top_confidence,
            'all_probabilities': normalized_scores,
            'suggested': suggested
        }

    def _adjust_confidence_by_amount(self, confidence: float, category: str, amount: float) -> float:
        """Adjust confidence based on typical amount ranges for categories"""
        amount_adjustments = {
            'Food & Dining': (5, 500),      # ₹5 to ₹500 typical
            'Transportation': (10, 1000),    # ₹10 to ₹1000
            'Shopping': (50, 5000),          # ₹50 to ₹5000
            'Entertainment': (20, 2000),     # ₹20 to ₹2000
            'Technology': (500, 50000),      # ₹500 to ₹50000
            'Bills & Utilities': (100, 10000), # ₹100 to ₹10000
            'Healthcare': (50, 5000),        # ₹50 to ₹5000
            'Travel': (500, 25000),          # ₹500 to ₹25000
            'Education': (100, 20000),       # ₹100 to ₹20000
            'Business': (100, 10000),        # ₹100 to ₹10000
            'Other': (1, 100000)             # Any amount
        }
        
        if category in amount_adjustments:
            min_amt, max_amt = amount_adjustments[category]
            if min_amt <= amount <= max_amt:
                confidence *= 1.1  # Boost confidence if amount is typical
            elif amount > max_amt * 2 or amount < min_amt * 0.5:
                confidence *= 0.9  # Reduce confidence if amount is very atypical
        
        return min(confidence, 0.95)

    def predict_batch(self, descriptions: List[str], amounts: Optional[List[float]] = None) -> List[Dict]:
        """Predict categories for multiple descriptions"""
        results = []
        for i, description in enumerate(descriptions):
            amount = amounts[i] if amounts and i < len(amounts) else None
            result = self.predict(description, amount)
            results.append(result)
        return results

    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return self.categories.copy()

    def add_correction(self, description: str, correct_category: str, amount: Optional[float] = None):
        """Add a correction to improve future predictions"""
        # For now, just log the correction
        # In a production system, this would update the model
        print(f"📝 Correction logged: '{description}' → {correct_category}")
        
        # Could implement online learning here in the future
        pass
