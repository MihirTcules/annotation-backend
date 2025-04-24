# This file is needed for Render.com deployment
# Render.com expects the Flask app to be in a file named app.py
# with the Flask app instance named 'app'

# Import the Flask app instance from main.py
from main import app

# This allows gunicorn to find the app instance
# No need to call app.run() here as gunicorn will handle that
if __name__ == "__main__":
    # For local testing only
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
