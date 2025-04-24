# Backend Service

This is a Flask-based backend service for the annotation application.

## Local Development

1. Create a `.env` file with the following variables:
   ```
   API_URL=http://192.168.1.98:5000
   PORT=5001
   FLASK_ENV=development
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Deployment on Render.com

1. Connect your GitHub repository to Render.com
2. Create a new Web Service
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment Variables:
     - API_URL: URL of your backend API service
     - FLASK_ENV: production

The application will automatically use the PORT environment variable provided by Render.com.
