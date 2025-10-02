"""
Google Gemini AI Receipt Extraction Service
Extracts detailed expense information from receipt/bill images
"""

import os
import base64
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from PIL import Image
import io
import time
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiReceiptExtractor:
    """
    Advanced receipt extraction using Google Gemini AI
    Extracts structured expense data from receipt/bill images
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini Receipt Extractor
        
        Args:
            api_key: Google Gemini API key (can also be set via environment variable)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Try different models in order of preference
        # Using v1beta API for better compatibility
        self.models = [
            "gemini-1.5-flash",  # Faster, uses fewer tokens
            "gemini-1.5-pro",   # More accurate but uses more quota
            "gemini-pro",        # Fallback for older API keys
        ]
        self.current_model = self.models[0]  # Start with flash model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif']
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # seconds
        
        # Enhanced categorization mapping for better accuracy
        self.category_mapping = {
            'restaurant': 'Food & Dining',
            'cafe': 'Food & Dining',
            'coffee': 'Food & Dining',
            'bar': 'Food & Dining',
            'fast food': 'Food & Dining',
            'grocery': 'Groceries',
            'supermarket': 'Groceries',
            'market': 'Groceries',
            'gas': 'Transportation',
            'fuel': 'Transportation',
            'petrol': 'Transportation',
            'taxi': 'Transportation',
            'uber': 'Transportation',
            'parking': 'Transportation',
            'pharmacy': 'Healthcare',
            'hospital': 'Healthcare',
            'clinic': 'Healthcare',
            'doctor': 'Healthcare',
            'medical': 'Healthcare',
            'shopping': 'Shopping',
            'mall': 'Shopping',
            'store': 'Shopping',
            'retail': 'Shopping',
            'movie': 'Entertainment',
            'cinema': 'Entertainment',
            'theater': 'Entertainment',
            'game': 'Entertainment',
            'hotel': 'Travel',
            'airline': 'Travel',
            'flight': 'Travel',
            'booking': 'Travel',
            'utilities': 'Bills & Utilities',
            'electric': 'Bills & Utilities',
            'water': 'Bills & Utilities',
            'internet': 'Bills & Utilities',
            'phone': 'Bills & Utilities',
        }
        
    def _prepare_image(self, image_data: bytes) -> str:
        """
        Prepare image for Gemini API by converting to base64
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Optimize image if too large
            image = Image.open(io.BytesIO(image_data))
            
            # Resize if image is too large (max 4MB for Gemini)
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
                
            # Save optimized image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=85, optimize=True)
            optimized_image_data = img_buffer.getvalue()
            
            return base64.b64encode(optimized_image_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error preparing image: {str(e)}")
            # Fallback to original image
            return base64.b64encode(image_data).decode('utf-8')
    
    def _create_extraction_prompt(self) -> str:
        """
        Create a comprehensive prompt for receipt extraction
        
        Returns:
            Detailed extraction prompt for Gemini
        """
        return """
Analyze this receipt/bill image and extract expense details. Return ONLY a JSON object with this EXACT structure (keep it concise):

{
  "extraction_status": "success",
  "confidence_score": 0.9,
  "total_amount": 150.00,
  "subtotal_amount": 127.12,
  "currency": "INR",
  "merchant_name": "Store Name",
  "merchant_address": "Address if visible",
  "date": "2024-01-15",
  "time": "14:30",
  "category": "Food & Dining",
  "subcategory": "Restaurant",
  "payment_method": "Card",
  "items": [
    {
      "name": "Item name",
      "quantity": 1,
      "unit_price": 50.00,
      "total_price": 50.00,
      "category": "Food"
    }
  ],
  "tax_details": {
    "tax_amount": 22.88,
    "tax_rate": 18.0,
    "tax_type": "GST",
    "subtotal_before_tax": 127.12
  },
  "discounts": [],
  "additional_charges": [],
  "receipt_number": "INV123",
  "notes": ""
}
}

IMPORTANT EXTRACTION RULES:
1. Extract ALL numerical values accurately (amounts, quantities, dates)
2. Calculate subtotal as sum of all item prices BEFORE tax
3. Extract GST/tax amount separately from the receipt
4. Ensure: subtotal_amount + tax_amount = total_amount (mathematical accuracy)
5. If GST rate is visible, extract it (commonly 5%, 12%, 18%, 28% in India)
6. Identify the merchant name from logos, headers, or business details
7. Parse itemized lists carefully - each item should have name, price, quantity
8. Determine the most appropriate expense category based on merchant type and items
9. If any field is not visible or unclear, use null or appropriate default
10. For amounts, use only numbers (no currency symbols in the number fields)
11. Extract date in YYYY-MM-DD format, time in HH:MM format
12. Be very precise with decimal places for monetary values
13. CRITICAL: Verify that subtotal + GST = total amount before responding
14. FOR LONG RECEIPTS: If there are more than 10 items, include only the first 5 items with prices and summarize the rest

LONG RECEIPT HANDLING:
- Prioritize total_amount, subtotal_amount, tax_details, merchant_name, date
- For receipts with many items (>10), limit items array to 5 most expensive items
- Always include items that have visible prices
- Keep response concise to avoid truncation

CATEGORY SUGGESTIONS:
- Food & Dining: restaurants, cafes, food delivery
- Groceries: supermarkets, grocery stores
- Transportation: gas stations, parking, taxi, public transport
- Healthcare: pharmacy, medical, dental, hospital
- Shopping: retail stores, online shopping, clothing
- Entertainment: movies, games, events, subscriptions
- Travel: hotels, flights, travel bookings
- Bills & Utilities: electricity, water, internet, phone
- Education: books, courses, school fees
- Other: miscellaneous expenses

Analyze the image thoroughly and provide accurate, structured data.
"""

    def _categorize_expense(self, merchant_name: str, items: List[Dict], total_amount: float) -> str:
        """
        Intelligently categorize expense based on merchant and items
        
        Args:
            merchant_name: Name of the merchant/business
            items: List of purchased items
            total_amount: Total expense amount
            
        Returns:
            Best matching category
        """
        merchant_lower = merchant_name.lower() if merchant_name else ""
        
        # Check merchant name against category mapping
        for keyword, category in self.category_mapping.items():
            if keyword in merchant_lower:
                return category
        
        # Analyze items for additional context
        item_keywords = []
        if items:
            for item in items:
                item_name = item.get('name', '').lower()
                item_keywords.extend(item_name.split())
        
        # Check item keywords
        for keyword in item_keywords:
            if keyword in self.category_mapping:
                return self.category_mapping[keyword]
        
        # Default categorization based on amount ranges
        if total_amount > 500:
            return 'Shopping'
        elif total_amount < 20:
            return 'Food & Dining'
        else:
            return 'Other'
    
    def _make_api_request_with_retry(self, payload: Dict, retry_count: int = 0) -> Optional[Dict]:
        """
        Make API request with retry logic and quota handling
        
        Args:
            payload: API request payload
            retry_count: Current retry attempt
            
        Returns:
            API response or None if failed
        """
        if retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) exceeded")
            return None
            
        try:
            # Switch to flash model after first quota error for better quota management
            if retry_count > 0 and self.current_model == "gemini-1.5-pro":
                self.current_model = "gemini-1.5-flash"
                logger.info(f"Switched to {self.current_model} model due to quota issues")
            elif retry_count > 1 and self.current_model == "gemini-1.5-flash":
                self.current_model = "gemini-pro"
                logger.info(f"Switched to fallback model {self.current_model}")
            
            headers = {'Content-Type': 'application/json'}
            url = f"{self.base_url}/{self.current_model}:generateContent?key={self.api_key}"
            
            logger.info(f"Making API request to {self.current_model} (attempt {retry_count + 1})")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Handle quota exceeded error (429)
            if response.status_code == 429:
                logger.warning(f"Quota exceeded for {self.current_model}, implementing backoff strategy...")
                
                # Exponential backoff with jitter
                delay = self.base_delay * (2 ** retry_count) + random.uniform(0, 2)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
                
                return self._make_api_request_with_retry(payload, retry_count + 1)
            
            # Handle success
            if response.status_code == 200:
                logger.info(f"API request successful with {self.current_model}")
                return response.json()
            
            # Handle other errors
            logger.error(f"API Error {response.status_code}: {response.text}")
            if retry_count < self.max_retries - 1:
                delay = self.base_delay * (2 ** retry_count)
                logger.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
                return self._make_api_request_with_retry(payload, retry_count + 1)
            
            return None
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            if retry_count < self.max_retries - 1:
                delay = self.base_delay * (2 ** retry_count)
                time.sleep(delay)
                return self._make_api_request_with_retry(payload, retry_count + 1)
            return None
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            if retry_count < self.max_retries - 1:
                delay = self.base_delay * (2 ** retry_count)
                time.sleep(delay)
                return self._make_api_request_with_retry(payload, retry_count + 1)
            return None
    def extract_receipt_data(self, image_data: bytes, image_format: str = 'jpeg') -> Dict[str, Any]:
        """
        Extract structured expense data from receipt image using Gemini AI with retry logic
        
        Args:
            image_data: Raw image bytes
            image_format: Image format (jpeg, png, etc.)
            
        Returns:
            Structured expense data dictionary
        """
        try:
            logger.info("Starting receipt extraction with Gemini AI (with quota handling)...")
            
            # Prepare image for API
            base64_image = self._prepare_image(image_data)
            
            # Create API request payload with optimized settings for quota management
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": self._create_extraction_prompt()
                            },
                            {
                                "inline_data": {
                                    "mime_type": f"image/{image_format}",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "topK": 1,
                    "topP": 0.8,
                    "maxOutputTokens": 1024,  # Reduced from 2048 to save quota
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Make API request with retry logic
            result = self._make_api_request_with_retry(payload)
            
            if not result:
                logger.error("All API retry attempts failed")
                return self._create_error_response("Failed to connect to AI service after multiple attempts")
            
            if 'candidates' not in result or not result['candidates']:
                logger.error("No candidates in Gemini response")
                return self._create_error_response("No response from AI model")
            
            # Extract generated text
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            
            logger.info("Successfully received response from Gemini")
            
            # Parse JSON from response
            try:
                # Extract JSON from the response (handle potential markdown formatting)
                # Remove markdown code blocks if present
                if '```json' in generated_text:
                    json_start = generated_text.find('```json') + 7
                    json_end = generated_text.find('```', json_start)
                    if json_end == -1:
                        # If no closing ```, take the rest of the text
                        json_text = generated_text[json_start:].strip()
                    else:
                        json_text = generated_text[json_start:json_end].strip()
                else:
                    # Find JSON object bounds
                    json_start = generated_text.find('{')
                    if json_start == -1:
                        logger.error("No JSON object found in Gemini response")
                        return self._create_error_response("Invalid response format")
                    
                    # Find the matching closing brace by counting braces
                    brace_count = 0
                    json_end = -1
                    for i in range(json_start, len(generated_text)):
                        if generated_text[i] == '{':
                            brace_count += 1
                        elif generated_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end == -1:
                        logger.error("No matching closing brace found in JSON")
                        return self._create_error_response("Incomplete JSON response")
                    
                    json_text = generated_text[json_start:json_end]
                
                # Clean up the JSON text
                json_text = json_text.strip()
                
                # Try to parse the JSON
                extracted_data = json.loads(json_text)
                
                # Validate and enhance the extracted data
                validated_data = self._validate_and_enhance_data(extracted_data)
                
                logger.info(f"Successfully extracted receipt data for {validated_data.get('merchant_name', 'Unknown merchant')}")
                return validated_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {str(e)}")
                logger.error(f"JSON text was: {json_text[:500]}...")
                
                # Try to fix common JSON issues and retry
                fixed_json = self._attempt_json_fix(json_text)
                if fixed_json:
                    try:
                        extracted_data = json.loads(fixed_json)
                        logger.info("Successfully parsed JSON after fix")
                        # Continue with validation
                        validated_data = self._validate_and_enhance_data(extracted_data)
                        logger.info(f"Successfully extracted receipt data for {validated_data.get('merchant_name', 'Unknown merchant')}")
                        return validated_data
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON even after fix attempt")
                        # Try simplified extraction as last resort
                        logger.info("Attempting simplified extraction for complex receipt...")
                        simplified_result = self._simplified_extraction_fallback(generated_text)
                        if simplified_result:
                            return simplified_result
                        return self._create_error_response("Failed to parse response data")
                else:
                    logger.error(f"Raw response: {generated_text}")
                    return self._create_error_response("Failed to parse AI response")
                
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {str(e)}")
            return self._create_error_response(f"Extraction failed: {str(e)}")
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """
        Safely convert value to float with fallback
        
        Args:
            value: Value to convert to float
            default: Default value if conversion fails
            
        Returns:
            Float value or default
        """
        if value is None:
            return default
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove currency symbols and whitespace
                cleaned = re.sub(r'[^\d.-]', '', value.strip())
                if cleaned:
                    return float(cleaned)
            
            return default
        except (ValueError, TypeError, AttributeError):
            return default

    def _validate_and_enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance extracted data
        
        Args:
            data: Raw extracted data from Gemini
            
        Returns:
            Validated and enhanced data
        """
        try:
            # Ensure required fields exist
            validated = {
                'extraction_status': data.get('extraction_status', 'success'),
                'confidence_score': min(max(self._safe_float(data.get('confidence_score'), 0.8), 0.0), 1.0),
                'total_amount': self._safe_float(data.get('total_amount'), 0.0),
                'subtotal_amount': self._safe_float(data.get('subtotal_amount'), 0.0),
                'currency': data.get('currency', 'INR'),
                'merchant_name': data.get('merchant_name', 'Unknown Merchant'),
                'merchant_address': data.get('merchant_address'),
                'date': self._validate_date(data.get('date')),
                'time': data.get('time'),
                'category': data.get('category', 'Other'),
                'subcategory': data.get('subcategory'),
                'payment_method': data.get('payment_method'),
                'items': self._validate_items(data.get('items', [])),
                'tax_details': self._validate_tax_details(data.get('tax_details', {})),
                'discounts': data.get('discounts', []),
                'additional_charges': data.get('additional_charges', []),
                'receipt_number': data.get('receipt_number'),
                'notes': data.get('notes'),
                'processed_at': datetime.now().isoformat(),
            }
            
            # Calculate and validate subtotal, GST, and total relationships
            validated = self._validate_gst_calculations(validated)
            
            # Auto-categorize if category is generic
            if validated['category'] in ['Other', 'Unknown', None]:
                validated['category'] = self._categorize_expense(
                    validated['merchant_name'],
                    validated['items'],
                    validated['total_amount']
                )
            
            # Calculate totals if items exist but total is 0
            if validated['total_amount'] == 0.0 and validated['items']:
                calculated_total = sum(self._safe_float(item.get('total_price'), 0.0) for item in validated['items'])
                if calculated_total > 0:
                    validated['total_amount'] = calculated_total
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return data  # Return original data if validation fails
    
    def _validate_date(self, date_str: str) -> str:
        """
        Validate and format date string
        
        Args:
            date_str: Raw date string
            
        Returns:
            Validated date in YYYY-MM-DD format
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Try various date formats
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d']
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # If all formats fail, return current date
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _validate_items(self, items: List[Dict]) -> List[Dict]:
        """
        Validate and clean items list
        
        Args:
            items: Raw items list
            
        Returns:
            Validated items list
        """
        validated_items = []
        
        for item in items:
            if isinstance(item, dict) and item.get('name'):
                try:
                    validated_item = {
                        'name': str(item.get('name', '')).strip(),
                        'quantity': max(int(item.get('quantity', 1) or 1), 1),
                        'unit_price': self._safe_float(item.get('unit_price'), 0.0),
                        'total_price': self._safe_float(item.get('total_price'), 0.0),
                        'category': item.get('category', 'Other')
                    }
                    
                    # Calculate total_price if missing
                    if validated_item['total_price'] == 0.0 and validated_item['unit_price'] > 0:
                        validated_item['total_price'] = validated_item['unit_price'] * validated_item['quantity']
                    
                    # Add 'price' field for frontend compatibility (use total_price or unit_price)
                    validated_item['price'] = validated_item['total_price'] if validated_item['total_price'] > 0 else validated_item['unit_price']
                    
                    validated_items.append(validated_item)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Skipping invalid item: {item}, error: {e}")
                    continue
        
        return validated_items
    
    def _validate_tax_details(self, tax_details: Dict) -> Dict[str, Any]:
        """
        Validate and clean tax details
        
        Args:
            tax_details: Raw tax details dictionary
            
        Returns:
            Validated tax details
        """
        if not isinstance(tax_details, dict):
            return {}
        
        return {
            'tax_amount': self._safe_float(tax_details.get('tax_amount'), 0.0),
            'tax_rate': self._safe_float(tax_details.get('tax_rate'), 0.0),
            'tax_type': tax_details.get('tax_type', 'GST'),
            'subtotal_before_tax': self._safe_float(tax_details.get('subtotal_before_tax'), 0.0)
        }
    
    def _validate_gst_calculations(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix GST calculation relationships
        Ensures subtotal + GST = total amount
        """
        total_amount = validated_data['total_amount']
        subtotal_amount = validated_data['subtotal_amount']
        tax_details = validated_data['tax_details']
        items = validated_data['items']
        
        # Calculate subtotal from items if not provided or if zero
        if subtotal_amount == 0.0 and items:
            calculated_subtotal = sum(self._safe_float(item.get('total_price'), 0.0) for item in items)
            validated_data['subtotal_amount'] = calculated_subtotal
            subtotal_amount = calculated_subtotal
        
        # Get tax amount from tax_details
        tax_amount = tax_details.get('tax_amount', 0.0)
        tax_rate = tax_details.get('tax_rate', 0.0)
        
        # Validate the mathematical relationship: subtotal + GST = total
        if total_amount > 0:
            if subtotal_amount > 0 and tax_amount > 0:
                # Check if subtotal + tax = total (with small tolerance for rounding)
                calculated_total = subtotal_amount + tax_amount
                if abs(calculated_total - total_amount) > 0.01:  # 1 paisa tolerance
                    logger.warning(f"GST calculation mismatch: {subtotal_amount} + {tax_amount} = {calculated_total} != {total_amount}")
                    # Recalculate based on total and subtotal
                    if subtotal_amount > 0:
                        tax_amount = total_amount - subtotal_amount
                        validated_data['tax_details']['tax_amount'] = max(0.0, tax_amount)
            
            elif subtotal_amount > 0 and tax_amount == 0:
                # Calculate GST from total - subtotal
                tax_amount = total_amount - subtotal_amount
                validated_data['tax_details']['tax_amount'] = max(0.0, tax_amount)
                
                # Calculate tax rate if possible
                if subtotal_amount > 0:
                    calculated_rate = (tax_amount / subtotal_amount) * 100
                    # Round to common GST rates (5, 12, 18, 28)
                    common_rates = [5.0, 12.0, 18.0, 28.0]
                    closest_rate = min(common_rates, key=lambda x: abs(x - calculated_rate))
                    if abs(closest_rate - calculated_rate) < 2:  # Within 2% tolerance
                        validated_data['tax_details']['tax_rate'] = closest_rate
            
            elif tax_amount > 0 and subtotal_amount == 0:
                # Calculate subtotal from total - tax
                subtotal_amount = total_amount - tax_amount
                validated_data['subtotal_amount'] = max(0.0, subtotal_amount)
            
            elif subtotal_amount == 0 and tax_amount == 0:
                # Assume 18% GST if no breakdown available
                if tax_rate > 0:
                    subtotal_amount = total_amount / (1 + tax_rate / 100)
                    tax_amount = total_amount - subtotal_amount
                else:
                    # Default to 18% GST
                    subtotal_amount = total_amount / 1.18
                    tax_amount = total_amount - subtotal_amount
                    validated_data['tax_details']['tax_rate'] = 18.0
                
                validated_data['subtotal_amount'] = round(subtotal_amount, 2)
                validated_data['tax_details']['tax_amount'] = round(tax_amount, 2)
        
        return validated_data
    
    def _attempt_json_fix(self, json_text: str) -> str:
        """
        Attempt to fix common JSON issues in incomplete responses
        
        Args:
            json_text: The potentially malformed JSON string
            
        Returns:
            Fixed JSON string or None if unfixable
        """
        try:
            # Remove any trailing incomplete strings or objects
            json_text = json_text.strip()
            
            # Special handling for incomplete items array (common with long receipts)
            if '"items": [' in json_text and not json_text.rstrip().endswith(']'):
                logger.info("Detected incomplete items array, attempting to fix...")
                
                # Find the last complete item in the array
                items_start = json_text.find('"items": [') + 10
                items_section = json_text[items_start:]
                
                # Remove any incomplete item at the end
                # Look for incomplete items (missing closing brace)
                items_section = re.sub(r',\s*\{[^}]*$', '', items_section)
                
                # Close the items array
                if not items_section.rstrip().endswith(']'):
                    if items_section.rstrip().endswith('}'):
                        items_section = items_section.rstrip() + ']'
                    else:
                        items_section = items_section.rstrip().rstrip(',') + ']'
                
                # Reconstruct the JSON
                json_before_items = json_text[:items_start]
                json_text = json_before_items + items_section
                
                # Add missing required fields if they're absent
                if '"subtotal_amount":' not in json_text:
                    json_text = json_text.rstrip('}') + ',\n  "subtotal_amount": 0.0'
                if '"tax_details":' not in json_text:
                    json_text = json_text.rstrip('}') + ',\n  "tax_details": {"tax_amount": 0.0, "tax_rate": 0.0, "subtotal_before_tax": 0.0}'
                
                # Ensure proper closing
                if not json_text.rstrip().endswith('}'):
                    json_text += '\n}'
            
            # Remove any trailing incomplete strings or objects
            json_text = re.sub(r',\s*"[^"]*":\s*"[^"]*$', '', json_text)
            json_text = re.sub(r',\s*"[^"]*":\s*[^,}\]]*$', '', json_text)
            
            # Count braces to see if we're missing closing braces
            open_braces = json_text.count('{')
            close_braces = json_text.count('}')
            
            if open_braces > close_braces:
                # Add missing closing braces
                missing_braces = open_braces - close_braces
                json_text += '}' * missing_braces
                logger.info(f"Added {missing_braces} missing closing braces")
            
            # Count brackets for arrays
            open_brackets = json_text.count('[')
            close_brackets = json_text.count(']')
            
            if open_brackets > close_brackets:
                # Add missing closing brackets
                missing_brackets = open_brackets - close_brackets
                json_text += ']' * missing_brackets
                logger.info(f"Added {missing_brackets} missing closing brackets")
            
            # Remove trailing commas before closing braces/brackets
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
            
            # Test if the fixed JSON is valid
            json.loads(json_text)
            logger.info("Successfully fixed incomplete JSON response")
            return json_text
            
        except Exception as e:
            logger.error(f"JSON fix attempt failed: {e}")
            return None
    
    def _create_error_response(self, error_message: str, fallback_data: Dict = None) -> Dict[str, Any]:
        """
        Create standardized error response with optional fallback data
        
        Args:
            error_message: Error description
            fallback_data: Optional fallback data to include
            
        Returns:
            Error response dictionary
        """
        error_response = {
            'extraction_status': 'failed',
            'error': error_message,
            'confidence_score': 0.0,
            'total_amount': fallback_data.get('total_amount', 0.0) if fallback_data else 0.0,
            'currency': 'INR',
            'merchant_name': fallback_data.get('merchant_name', 'Unknown Merchant') if fallback_data else 'Unknown Merchant',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'category': 'Other',
            'items': fallback_data.get('items', []) if fallback_data else [],
            'processed_at': datetime.now().isoformat(),
            'payment_method': 'Unknown',
            'receipt_number': None,
            'notes': f"Extraction failed: {error_message}. Please verify the data manually.",
            'requires_manual_review': True
        }
        
        # If we have fallback data, mark as partially successful
        if fallback_data and fallback_data.get('total_amount', 0) > 0:
            error_response['extraction_status'] = 'partial'
            error_response['confidence_score'] = 0.3
            error_response['notes'] = f"Partial extraction only. {error_message}. Please review and correct the data."
        
        return error_response
    
    def _simplified_extraction_fallback(self, response_text: str) -> Dict[str, Any]:
        """
        Fallback method to extract basic information using regex when JSON parsing fails
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Basic extracted data or None if extraction fails
        """
        try:
            logger.info("Attempting simplified regex-based extraction...")
            
            # Try to extract basic fields using regex patterns
            total_match = re.search(r'"total_amount":\s*([0-9]+(?:\.[0-9]+)?)', response_text)
            merchant_match = re.search(r'"merchant_name":\s*"([^"]+)"', response_text)
            date_match = re.search(r'"date":\s*"([^"]+)"', response_text)
            category_match = re.search(r'"category":\s*"([^"]+)"', response_text)
            
            if total_match:
                total_amount = float(total_match.group(1))
                merchant_name = merchant_match.group(1) if merchant_match else "Unknown Merchant"
                date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
                category = category_match.group(1) if category_match else "Other"
                
                # Create a basic valid response
                simplified_data = {
                    "extraction_status": "success",
                    "confidence_score": 0.7,  # Lower confidence for simplified extraction
                    "total_amount": total_amount,
                    "subtotal_amount": total_amount * 0.85,  # Estimate subtotal (85% of total)
                    "currency": "INR",
                    "merchant_name": merchant_name,
                    "merchant_address": None,
                    "date": date,
                    "time": None,
                    "category": category,
                    "subcategory": None,
                    "payment_method": None,
                    "items": [
                        {
                            "name": "Items from receipt",
                            "quantity": 1,
                            "unit_price": total_amount * 0.85,
                            "total_price": total_amount * 0.85,
                            "category": "Other"
                        }
                    ],
                    "tax_details": {
                        "tax_amount": total_amount * 0.15,  # Estimate 15% tax
                        "tax_rate": 15.0,
                        "tax_type": "GST",
                        "subtotal_before_tax": total_amount * 0.85
                    },
                    "discounts": [],
                    "additional_charges": [],
                    "receipt_number": None,
                    "notes": "Simplified extraction due to parsing issues"
                }
                
                logger.info(f"Simplified extraction successful for {merchant_name}: ₹{total_amount}")
                return self._validate_and_enhance_data(simplified_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Simplified extraction failed: {e}")
            return None

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported image formats
        
        Returns:
            List of supported formats
        """
        return self.supported_formats.copy()


# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the service
    print("Gemini Receipt Extractor Service")
    print("Supported formats:", GeminiReceiptExtractor.get_supported_formats(None))
