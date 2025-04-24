# This file is needed for Render.com deployment
# Render.com expects the Flask app to be in a file named app.py
# with the Flask app instance named 'app'

# Import the Flask app instance from main.py
from main import app
from flask_cors import CORS
from flask import jsonify
import os

# Ensure CORS is properly configured for all routes
# This is a safety measure in case the CORS in main.py doesn't apply
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     expose_headers=["Content-Type", "Authorization"])

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Global OPTIONS route handler for CORS preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(_):  # Parameter not used but required by Flask routing
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Root route handler
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "API is running",
        "status": "ok",
        "version": "1.0.0",
        "endpoints": [
            "/login",
            "/logout",
            "/user",
            "/proxy/get-user-tasks",
            "/proxy/create",
            "/proxy/append",
            "/proxy/get-bounding-boxes"
        ]
    })

# This allows gunicorn to find the app instance
# No need to call app.run() here as gunicorn will handle that
if __name__ == "__main__":
    # For local testing only
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
