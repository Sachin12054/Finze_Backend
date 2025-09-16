# Render.com Deployment Configuration
# Place this in your Render service settings

# Build Command:
pip install -r requirements.txt && python download_models.py

# Start Command:
python app.py

# Environment Variables to set in Render:
# PORT=5000
# GOOGLE_API_KEY=your_google_api_key_here
# MODEL_DOWNLOAD_URL=your_model_download_url (optional)
# FIREBASE_PROJECT_ID=your_firebase_project_id
# FIREBASE_PRIVATE_KEY=your_firebase_private_key
# FIREBASE_CLIENT_EMAIL=your_firebase_client_email

# Auto-Deploy: Yes
# Branch: main (or your preferred branch)

# Render will automatically:
# 1. Install dependencies from requirements.txt
# 2. Run download_models.py to handle ML models
# 3. Start the Flask app on the assigned PORT