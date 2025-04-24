# Flask Backend Application

This is a Flask backend application that provides API endpoints for user authentication, data storage, and proxy functionality.

## Deployment on Render.com with GitHub Integration

### Prerequisites

- A GitHub account
- A Render.com account
- Your code pushed to a GitHub repository

### Project Structure

```
.
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore file
├── Procfile               # Render deployment configuration
├── README.md              # This file
├── db.py                  # Database connection module
├── flask_session/         # Session storage directory
├── label.html             # Template for label page
├── main.py                # Main application file
├── public/                # Static files directory
│   ├── index.html         # Main landing page
│   └── label.html         # Public label page
├── requirements.txt       # Python dependencies
└── runtime.txt            # Python version specification
```

### Steps to Deploy

1. **Push your code to GitHub**
   - Make sure your repository includes all the files listed above
   - Ensure `.env` is in your `.gitignore` file to avoid exposing sensitive information

2. **Create a new Web Service on Render.com**
   - Log in to your Render.com account
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: Choose a name for your service
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn main:app`

3. **Set Environment Variables**
   - In the Render dashboard, go to your web service
   - Click on "Environment" tab
   - Add the following environment variables:
     - `SECRET_KEY`: A secure random string
     - `ENVIRONMENT`: Set to `production`
     - `API_DOMAIN`: Your Render service URL (e.g., https://your-app-name.onrender.com)
     - `SOCKET_DOMAIN`: Same as API_DOMAIN
     - `TASKS_API_DOMAIN`: URL of your tasks API

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - Your application will be available at the URL provided by Render

### Continuous Deployment

Render automatically deploys your application when you push changes to your GitHub repository. No additional configuration is needed.

## Local Development

1. Create a `.env` file based on `.env.example`:
   ```
   SECRET_KEY=your_local_secret_key
   ENVIRONMENT=development
   API_DOMAIN=http://localhost:5001
   SOCKET_DOMAIN=http://localhost:5001
   TASKS_API_DOMAIN=http://localhost:5000
   PORT=5001
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

4. Access the application at http://localhost:5001

## API Documentation

The application provides the following API endpoints:

- `GET /api/elements` - Get elements
- `GET /api/get-labels` - Get labels
- `POST /api/save-labels` - Save labels
- `GET/POST /api/save-annotation` - Save annotation data
- `POST /api/append` - Append annotation data
- `POST /api/register` - Register a new user
- `POST /api/login` - Login a user
- `POST /api/logout` - Logout a user
- `GET /api/user` - Get user information
