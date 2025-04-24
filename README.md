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
   python app.py
   ```

## Deployment on Render.com

### Option 1: Manual Deployment

1. Connect your GitHub repository to Render.com
2. Create a new Web Service
3. Use the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment Variables:
     - `API_URL`: URL of your backend API service
     - `FLASK_ENV`: production

### Option 2: Using render.yaml (Blueprint)

1. Make sure the `render.yaml` file is in your repository
2. Update the `API_URL` value in `render.yaml` to point to your actual API service
3. In Render.com, click on "Blueprint" and select your repository
4. Render will automatically configure the service based on the YAML file

### Troubleshooting Deployment Issues

If you encounter deployment issues:

1. Check the logs in Render.com dashboard
2. Ensure all dependencies are correctly specified in `requirements.txt`
3. Verify that the `app.py` file correctly imports the Flask app instance
4. Make sure your MongoDB connection string is correctly set up in environment variables

The application will automatically use the PORT environment variable provided by Render.com.
