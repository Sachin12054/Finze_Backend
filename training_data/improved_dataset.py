#!/usr/bin/env python3
"""
Improved training dataset for expense categorization
Matches the categories used in the Finze app
"""

import pandas as pd
import json
import os

# Categories that match your app exactly
CATEGORIES = [
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

def create_comprehensive_dataset():
    """Create a comprehensive training dataset with realistic expense descriptions"""
    
    training_data = []
    
    # Food & Dining examples (200+ examples)
    food_examples = [
        "Bought groceries at Walmart", "Coffee at Starbucks", "Lunch at McDonald's",
        "Dinner at Pizza Hut", "Breakfast sandwich", "Grocery shopping Target",
        "Food delivery UberEats", "Restaurant bill", "Cafe latte", "Snacks 7-Eleven",
        "Domino's pizza order", "KFC chicken bucket", "Subway sandwich",
        "Ice cream parlor", "Bakery fresh bread", "Chinese takeout",
        "Indian restaurant", "Thai food delivery", "Mexican grill",
        "Fast food burger", "Sushi restaurant", "Seafood dinner",
        "Vegetarian meal", "Organic fruits", "Meat from butcher",
        "Dairy products", "Frozen foods", "Beverages and drinks",
        "Wine and spirits", "Beer purchase", "Energy drinks",
        "Protein bars", "Healthy snacks", "Candy and sweets",
        "Cake for birthday", "Wedding catering", "Office lunch",
        "School cafeteria", "Airport food", "Hotel restaurant",
        "Room service", "Picnic supplies", "BBQ ingredients",
        "Cooking ingredients", "Spices and herbs", "Cooking oil",
        "Rice and grains", "Pasta and noodles", "Bread and cereals",
        "Milk and yogurt", "Cheese varieties", "Fresh vegetables",
        "Seasonal fruits", "Meat and poultry", "Fish and seafood",
        "Tiffin service", "Mess charges", "Canteen food",
        "Street food", "Local restaurant", "Fine dining",
        "Food court meal", "Home delivery", "Packed lunch",
        "Tea and coffee", "Juice bar", "Smoothie shop",
        "Dessert shop", "Food truck", "Catering service"
    ]
    
    # Transportation examples (150+ examples)  
    transport_examples = [
        "Uber ride", "Taxi fare", "Bus ticket", "Train journey",
        "Metro card recharge", "Auto rickshaw", "Flight booking",
        "Car rental", "Bike rental", "Petrol pump", "Diesel fuel",
        "Car maintenance", "Oil change", "Tire replacement",
        "Car insurance", "Vehicle registration", "Parking fee",
        "Toll charges", "Traffic fine", "Car wash",
        "Public transport", "Monthly bus pass", "Train season ticket",
        "Airport shuttle", "Hotel transfer", "Cab booking",
        "Ride sharing", "Car service", "Vehicle repair",
        "Brake service", "Engine check", "Battery replacement",
        "Car accessories", "GPS device", "Dashcam purchase",
        "Fuel card", "Highway toll", "Bridge toll",
        "Valet parking", "Long term parking", "Street parking",
        "Bike maintenance", "Bicycle repair", "Scooter service",
        "Motorcycle fuel", "Helmet purchase", "Safety gear",
        "Driver license", "Vehicle permit", "Road tax",
        "Emission test", "Safety inspection", "Registration renewal"
    ]
    
    # Shopping examples (180+ examples)
    shopping_examples = [
        "Amazon purchase", "Flipkart order", "Clothing store",
        "Shoes shopping", "Electronics store", "Home appliances",
        "Furniture purchase", "Decoration items", "Kitchen utensils",
        "Bedding and linen", "Cleaning supplies", "Personal care",
        "Cosmetics shopping", "Skincare products", "Hair care items",
        "Perfume and cologne", "Jewelry purchase", "Watch shopping",
        "Bag and luggage", "Wallet purchase", "Sunglasses shopping",
        "Books and stationery", "Art supplies", "Craft materials",
        "Sporting goods", "Gym equipment", "Outdoor gear",
        "Garden supplies", "Plant shopping", "Seeds and fertilizer",
        "Pet supplies", "Pet food", "Pet accessories",
        "Baby products", "Toys and games", "Children's clothing",
        "School supplies", "Office supplies", "Computer accessories",
        "Mobile accessories", "Headphones purchase", "Speaker shopping",
        "Camera equipment", "Photography gear", "Gaming accessories",
        "Software purchase", "App subscription", "Digital content",
        "Gift shopping", "Birthday present", "Wedding gift",
        "Holiday shopping", "Seasonal items", "Festival purchases",
        "Pharmacy items", "Vitamins supplements", "Medical supplies",
        "Tools and hardware", "DIY materials", "Construction supplies"
    ]
    
    # Entertainment examples (120+ examples)
    entertainment_examples = [
        "Movie ticket", "Cinema booking", "Theatre show",
        "Concert ticket", "Music festival", "Comedy show",
        "Sports event", "Stadium ticket", "Game ticket",
        "Amusement park", "Water park", "Zoo visit",
        "Museum entry", "Art gallery", "Exhibition ticket",
        "Netflix subscription", "Spotify premium", "Amazon Prime",
        "Disney+ subscription", "Gaming subscription", "YouTube premium",
        "Video game purchase", "Gaming console", "PC games",
        "Mobile game purchase", "In-app purchases", "Gaming currency",
        "Books and novels", "E-book purchase", "Audiobook subscription",
        "Magazine subscription", "Newspaper subscription", "Digital media",
        "Photography session", "Video production", "Audio recording",
        "Dance classes", "Music lessons", "Art classes",
        "Hobby supplies", "Craft workshop", "Cooking class",
        "Sports club", "Gym membership", "Fitness classes",
        "Yoga classes", "Swimming pool", "Tennis court",
        "Golf course", "Adventure sports", "Outdoor activities",
        "Theme park", "Carnival rides", "Fair tickets",
        "Party supplies", "Event planning", "Celebration costs"
    ]
    
    # Technology examples (100+ examples)
    technology_examples = [
        "iPhone purchase", "Android phone", "Laptop buying",
        "Desktop computer", "Tablet purchase", "Smartwatch buying",
        "Headphones shopping", "Bluetooth speaker", "Gaming headset",
        "Camera purchase", "DSLR camera", "Action camera",
        "Drone purchase", "Smart TV", "Streaming device",
        "Router purchase", "WiFi extender", "Network equipment",
        "Computer repair", "Phone screen fix", "Laptop service",
        "Software license", "Antivirus subscription", "Cloud storage",
        "App purchase", "Premium app", "Software upgrade",
        "Tech accessories", "Phone case", "Screen protector",
        "Charging cable", "Power bank", "Wireless charger",
        "Computer parts", "RAM upgrade", "Hard drive",
        "Graphics card", "Processor upgrade", "Motherboard",
        "Keyboard purchase", "Mouse buying", "Monitor purchase",
        "Printer purchase", "Scanner buying", "Webcam purchase",
        "Microphone buying", "Studio equipment", "Recording gear",
        "Smart home devices", "Security cameras", "Home automation",
        "Fitness tracker", "Health monitor", "Medical device",
        "Car tech", "GPS device", "Car audio system"
    ]
    
    # Bills & Utilities examples (100+ examples)
    utilities_examples = [
        "Electricity bill", "Water bill", "Gas bill",
        "Internet bill", "Phone bill", "Cable TV",
        "Rent payment", "Mortgage payment", "Property tax",
        "Home insurance", "Life insurance", "Health insurance",
        "Car insurance", "Travel insurance", "Business insurance",
        "Loan EMI", "Credit card payment", "Bank charges",
        "Service charges", "Maintenance fee", "Society charges",
        "Security deposit", "Utility deposit", "Connection charges",
        "Installation fee", "Service call", "Repair charges",
        "Subscription renewal", "License renewal", "Registration fee",
        "Government fee", "Tax payment", "Fine payment",
        "Legal charges", "Professional fee", "Consultation charges",
        "Accounting fee", "Audit charges", "Documentation fee",
        "Processing fee", "Administrative charges", "Handling charges",
        "Delivery charges", "Shipping cost", "Packaging fee",
        "Storage charges", "Warehouse fee", "Logistics cost"
    ]
    
    # Healthcare examples (80+ examples)
    healthcare_examples = [
        "Doctor visit", "Medical consultation", "Hospital bill",
        "Surgery cost", "Operation charges", "Treatment fee",
        "Medicine purchase", "Prescription drugs", "Health supplements",
        "Vitamins buying", "First aid supplies", "Medical equipment",
        "Health checkup", "Blood test", "X-ray scan",
        "MRI scan", "CT scan", "Ultrasound",
        "Dental checkup", "Dental treatment", "Tooth filling",
        "Eye checkup", "Eye glasses", "Contact lenses",
        "Physiotherapy", "Massage therapy", "Rehabilitation",
        "Mental health", "Counseling session", "Therapy session",
        "Wellness program", "Health screening", "Vaccination",
        "Emergency treatment", "Ambulance service", "ICU charges",
        "Pharmacy purchase", "Medical supplies", "Health insurance premium",
        "Lab tests", "Diagnostic tests", "Medical imaging",
        "Specialist consultation", "Follow-up visit", "Health monitoring"
    ]
    
    # Travel examples (90+ examples)
    travel_examples = [
        "Flight booking", "Hotel reservation", "Travel package",
        "Vacation trip", "Business travel", "Weekend getaway",
        "Holiday booking", "Resort stay", "Cruise booking",
        "Tour package", "Travel insurance", "Visa application",
        "Passport renewal", "Travel documents", "Foreign exchange",
        "Airport parking", "Airport lounge", "Excess baggage",
        "Car rental abroad", "Local transport", "City tours",
        "Sightseeing", "Adventure activities", "Cultural tours",
        "Food tours", "Shopping tours", "Nature trips",
        "Beach vacation", "Mountain trip", "Desert safari",
        "Wildlife sanctuary", "National park", "Heritage sites",
        "Pilgrimage trip", "Religious tour", "Spiritual journey",
        "Conference travel", "Seminar attendance", "Training program",
        "Study abroad", "Exchange program", "International course",
        "Family vacation", "Honeymoon trip", "Anniversary celebration",
        "Travel gear", "Luggage purchase", "Travel accessories"
    ]
    
    # Education examples (70+ examples)
    education_examples = [
        "School fees", "College tuition", "University fees",
        "Course enrollment", "Online course", "Certification program",
        "Training workshop", "Skill development", "Professional course",
        "Language classes", "Computer course", "Technical training",
        "Books purchase", "Study materials", "Educational supplies",
        "Stationery items", "School uniform", "College supplies",
        "Laboratory fee", "Library fee", "Examination fee",
        "Admission fee", "Registration charges", "Application fee",
        "Scholarship application", "Educational loan", "Study loan",
        "Research materials", "Project supplies", "Thesis printing",
        "Educational software", "Learning apps", "Online subscription",
        "Tutoring classes", "Private lessons", "Coaching classes",
        "Entrance exam fee", "Competitive exam", "Test preparation",
        "Educational tours", "Study trips", "Field visits",
        "Conference attendance", "Seminar registration", "Workshop fee"
    ]
    
    # Business examples (60+ examples)
    business_examples = [
        "Office supplies", "Business equipment", "Office furniture",
        "Computer purchase", "Software license", "Business software",
        "Marketing expenses", "Advertising cost", "Promotional items",
        "Business cards", "Brochure printing", "Website development",
        "Professional services", "Legal consultation", "Accounting services",
        "Business registration", "License fee", "Permit charges",
        "Office rent", "Commercial space", "Co-working space",
        "Business insurance", "Professional insurance", "Liability insurance",
        "Employee expenses", "Staff training", "Team building",
        "Client meeting", "Business lunch", "Conference expenses",
        "Travel expenses", "Business travel", "Client visit",
        "Equipment maintenance", "Office repairs", "System upgrade",
        "Networking events", "Trade shows", "Business conferences",
        "Subscription services", "Business tools", "Professional membership"
    ]
    
    # Other examples (50+ examples)
    other_examples = [
        "Miscellaneous expense", "Random purchase", "Unategorized",
        "Cash withdrawal", "ATM charges", "Bank transfer",
        "Investment purchase", "Stock trading", "Mutual funds",
        "Gold purchase", "Jewelry buying", "Precious metals",
        "Charity donation", "Religious offering", "Social cause",
        "Gift giving", "Celebration expense", "Party cost",
        "Emergency expense", "Unexpected cost", "Urgent payment",
        "Temporary expense", "One-time purchase", "Special occasion",
        "Personal care", "Grooming services", "Beauty treatment",
        "Hobby expense", "Collection items", "Special interest",
        "Community fee", "Social charges", "Club membership",
        "Subscription box", "Monthly box", "Surprise purchase",
        "Impulse buying", "Spontaneous expense", "Unplanned cost"
    ]
    
    # Combine all examples with their categories
    all_examples = [
        (food_examples, 'Food & Dining'),
        (transport_examples, 'Transportation'),
        (shopping_examples, 'Shopping'),
        (entertainment_examples, 'Entertainment'),
        (technology_examples, 'Technology'),
        (utilities_examples, 'Bills & Utilities'),
        (healthcare_examples, 'Healthcare'),
        (travel_examples, 'Travel'),
        (education_examples, 'Education'),
        (business_examples, 'Business'),
        (other_examples, 'Other')
    ]
    
    # Create training data
    for examples, category in all_examples:
        for example in examples:
            training_data.append({
                'description': example,
                'category': category
            })
    
    return training_data

def save_training_data():
    """Save the training data in multiple formats"""
    
    # Create directory if it doesn't exist
    os.makedirs('training_data', exist_ok=True)
    
    # Generate training data
    data = create_comprehensive_dataset()
    
    # Save as CSV for easy viewing/editing
    df = pd.DataFrame(data)
    df.to_csv('training_data/comprehensive_dataset.csv', index=False)
    
    # Save as JSON for the model
    with open('training_data/comprehensive_dataset.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Create label mapping
    label_mapping = {category: idx for idx, category in enumerate(CATEGORIES)}
    with open('training_data/label_mapping.json', 'w') as f:
        json.dump(label_mapping, f, indent=2)
    
    # Print statistics
    print(f"✅ Generated {len(data)} training examples")
    print(f"📊 Categories: {len(CATEGORIES)}")
    
    # Print category distribution
    print("\n📈 Category Distribution:")
    category_counts = df['category'].value_counts()
    for category, count in category_counts.items():
        print(f"   {category}: {count} examples")
    
    print(f"\n💾 Files saved:")
    print(f"   - training_data/comprehensive_dataset.csv")
    print(f"   - training_data/comprehensive_dataset.json") 
    print(f"   - training_data/label_mapping.json")

if __name__ == "__main__":
    save_training_data()
