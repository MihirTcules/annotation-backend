import json
import os
import datetime
import hashlib
import secrets
import requests
from flask import Flask, jsonify, request, send_from_directory, session
from bson.objectid import ObjectId
from flask_cors import CORS
from flask_session import Session
from db import get_db
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file in development
if os.path.exists('.env'):
    load_dotenv()

# Get API URL from environment variable or use default
API_URL = os.environ.get('API_URL', 'http://localhost:5000')

# Initialize Flask app
app = Flask(__name__, static_folder='public')

# Simple CORS configuration that works with credentials
CORS(app, supports_credentials=True)

# Configure session with settings that work for cross-origin requests
app.secret_key = secrets.token_hex(16)  # Generate a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = None  # None is required for cross-origin requests
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow the browser to set the cookie domain
app.config['SESSION_PERMANENT'] = True  # Make session permanent
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)  # Session lasts for 7 days
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')

# Initialize Flask-Session
Session(app)

# Path for storing labels
LABELS_FILE = 'labels.json'
DETAILED_LABELS_FILE = 'detailed_labels.json'

# Sort elements by area (smallest to largest)
def sort_elements_by_area(elements, reverse=False):
    # Add area to each element
    for element in elements:
        element["area"] = element["width"] * element["height"]

    # Sort elements by area
    return sorted(elements, key=lambda el: el["area"], reverse=reverse)

# API Routes
@app.route('/api/elements', methods=['GET'])
def get_elements():
    try:
        # Check if sorted_elements.json exists, if not create it
        if not os.path.exists('sorted_elements.json'):
            if os.path.exists('elements.json'):
                with open('elements.json', 'r') as f:
                    elements = json.load(f)

                # Sort elements by area (largest to smallest by default)
                sorted_elements = sort_elements_by_area(elements, reverse=True)

                with open('sorted_elements.json', 'w') as f:
                    json.dump(sorted_elements, f, indent=2)
            else:
                return jsonify({'error': 'No elements found'}), 404

        # Read sorted elements
        with open('sorted_elements.json', 'r') as f:
            elements = json.load(f)

        return jsonify(elements)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-labels', methods=['GET'])
def get_labels():
    try:
        print('GET /api/get-labels - Request received')
        # Prefer detailed labels file if it exists
        if os.path.exists(DETAILED_LABELS_FILE):
            try:
                with open(DETAILED_LABELS_FILE, 'r') as f:
                    labels = json.load(f)
                print(f'Returning {len(labels)} labels from detailed_labels.json')
                return jsonify(labels)
            except json.JSONDecodeError:
                # If file is empty or invalid JSON
                print('Error: detailed_labels.json exists but contains invalid JSON')
                pass

        # Fall back to original labels file
        if os.path.exists(LABELS_FILE):
            with open(LABELS_FILE, 'r') as f:
                labels = json.load(f)
            print(f'Returning {len(labels)} labels from labels.json')
            return jsonify(labels)

        # Return empty array if no files exist
        print('No label files found, returning empty array')
        return jsonify([])
    except Exception as e:
        print(f'Error in get_labels: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-labels', methods=['POST'])
def save_labels():
    try:
        labels = request.json
        print(f'POST /api/save-labels - Received {len(labels)} labels')

        # Load sorted_elements.json to get complete element data
        elements_data = {}
        if os.path.exists('sorted_elements.json'):
            try:
                with open('sorted_elements.json', 'r') as f:
                    elements = json.load(f)
                    # Create a map of selectors to element data
                    for element in elements:
                        elements_data[element.get('selector')] = element
                print(f'Loaded {len(elements_data)} elements from sorted_elements.json')
            except json.JSONDecodeError:
                print('Error: sorted_elements.json exists but contains invalid JSON')

        # Save to labels file
        # If file exists, read it first and append/update
        existing_labels = []
        if os.path.exists(LABELS_FILE):
            try:
                with open(LABELS_FILE, 'r') as f:
                    existing_labels = json.load(f)
                print(f'Loaded {len(existing_labels)} existing labels from labels.json')
            except json.JSONDecodeError:
                print('Error: labels.json exists but contains invalid JSON')
                existing_labels = []

        # Create a map of selectors to existing labels for faster lookup
        selector_to_label = {}
        for label in existing_labels:
            selector_to_label[label.get('selector')] = label

        # Process each new label
        updated_count = 0
        added_count = 0
        for new_label in labels:
            selector = new_label.get('selector')

            # Create a complete label object with all element data
            complete_label = {}

            # If we have element data for this selector, use it as a base
            if selector in elements_data:
                # Start with all element data
                complete_label = elements_data[selector].copy()
                # Add the label property
                complete_label['label'] = new_label.get('label')
                # Add timestamp
                complete_label['timestamp'] = new_label.get('timestamp', datetime.datetime.now().isoformat())
            else:
                # If no element data, just use the label data
                complete_label = new_label.copy()

            # Check if this element is already labeled
            if selector in selector_to_label:
                # Update existing label
                selector_to_label[selector]['label'] = complete_label['label']
                selector_to_label[selector]['timestamp'] = complete_label['timestamp']
                updated_count += 1
            else:
                # Add new label
                existing_labels.append(complete_label)
                selector_to_label[selector] = complete_label
                added_count += 1

        print(f'Updated {updated_count} labels, added {added_count} new labels')

        # Save updated labels
        with open(LABELS_FILE, 'w') as f:
            json.dump(existing_labels, f, indent=2)

        # Also save to detailed_labels.json for backward compatibility
        with open(DETAILED_LABELS_FILE, 'w') as f:
            json.dump(existing_labels, f, indent=2)

        print(f'Saved {len(existing_labels)} total labels to disk')
        return jsonify({
            'success': True,
            'message': 'Labels saved successfully',
            'count': len(existing_labels),
            'updated': updated_count,
            'added': added_count
        })
    except Exception as e:
        print(f'Error in save_labels: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# Non-prefixed route handlers that redirect to the API routes
@app.route('/login', methods=['POST', 'OPTIONS'])
def login_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # Forward the request to the API route
    return login()

@app.route('/logout', methods=['POST', 'OPTIONS'])
def logout_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # Forward the request to the API route
    return logout()

@app.route('/user', methods=['GET', 'OPTIONS'])
def user_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response

    # Forward the request to the API route
    return get_user()

@app.route('/proxy/get-user-tasks', methods=['POST', 'OPTIONS'])
def proxy_tasks_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # Forward the request to the API route
    return proxy_get_user_tasks()

@app.route('/proxy/create', methods=['POST', 'OPTIONS'])
def proxy_create_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # Forward the request to the API route
    return proxy_create_annotation()

@app.route('/proxy/get-bounding-boxes', methods=['GET', 'OPTIONS'])
def proxy_get_bounding_boxes_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response

    # Forward the request to the API route
    return proxy_get_bounding_boxes()

@app.route('/proxy/append', methods=['POST', 'OPTIONS'])
def proxy_append_redirect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    # Forward the request to the API route
    return proxy_append_annotation()

@app.route("/api/save-annotation", methods=["POST", "GET"])
def save_json():
    filename = request.args.get("file")
    if not filename or not filename.endswith(".json"):
        return jsonify({"error": "Invalid file name"}), 400

    path = os.path.join(filename)

    # GET method to retrieve the annotation data
    if request.method == "GET":
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify(data)
            else:
                return jsonify([])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # POST method to save the annotation data
    data = request.get_json()

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/append", methods=["POST"])
def append_annotation():
    try:
        data = request.get_json()
        filename = data.get("filename")
        parsed_url = urlparse(filename)
        path = parsed_url.path
        # Extract the filename
        filename = os.path.basename(path)
        annotation_data = data.get("data")

        if not filename or not filename.endswith(".json"):
            return jsonify({"error": "Invalid file name"}), 400

        if not annotation_data or not isinstance(annotation_data, list):
            return jsonify({"error": "Invalid annotation data"}), 400

        path = os.path.join(filename)

        # Read the current annotations
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                annotations = json.load(f)
        else:
            annotations = []

        # Process each annotation
        for new_annotation in annotation_data:
            selector = new_annotation.get("selector")
            labels = new_annotation.get("label")

            if not selector or not labels:
                continue

            # Add timestamp if not present
            if not new_annotation.get("timestamp"):
                new_annotation["timestamp"] = datetime.datetime.now().isoformat()

            # Add color if not present
            if not new_annotation.get("color"):
                new_annotation["color"] = "#F44336"  # Use the standard red color

            # Ensure tag and class are present and not empty
            if not new_annotation.get("tag") or new_annotation.get("tag") == "":
                # Try to extract tag from selector
                selector_parts = selector.split('.')
                if len(selector_parts) > 0 and selector_parts[0]:
                    new_annotation["tag"] = selector_parts[0]
                else:
                    new_annotation["tag"] = "div"  # Default tag

            if not new_annotation.get("class") or new_annotation.get("class") == "":
                # Try to extract class from selector
                class_parts = [part for part in selector.split('.') if part and part != selector_parts[0]]
                if class_parts:
                    new_annotation["class"] = " ".join(class_parts)

            # Ensure id is present
            if not new_annotation.get("id"):
                new_annotation["id"] = ""

            # Handle labels format - only store in label property
            if not isinstance(labels, list):
                new_annotation["label"] = [labels] if labels else []  # Convert to array if not already
            else:
                new_annotation["label"] = labels  # Keep as array

            # Remove labels property if it exists
            if "labels" in new_annotation:
                del new_annotation["labels"]

            # Remove the existing annotation with the same selector
            annotations = [a for a in annotations if a.get("selector") != selector]

            # Add the new annotation
            annotations.append(new_annotation)
            print(f"Added/updated annotation for selector: {selector}")

        # Save the updated annotations
        with open(path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, indent=2)

        return jsonify({"status": "success", "message": f"Updated annotations for {len(annotation_data)} elements"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/remove-annotation", methods=["POST"])
def remove_annotation():
    filename = request.args.get("file")
    if not filename or not filename.endswith(".json"):
        return jsonify({"error": "Invalid file name"}), 400

    # Get selector and label from request
    data = request.get_json()
    selector = data.get("selector")
    label_to_remove = data.get("label")

    if not selector or not label_to_remove:
        return jsonify({"error": "Selector and label are required"}), 400

    path = os.path.join(filename)

    try:
        # Read the current annotations
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                annotations = json.load(f)
        else:
            return jsonify({"error": "Annotation file not found"}), 404

        # Find the annotation with the matching selector
        found = False
        for i, annotation in enumerate(annotations):
            if annotation.get("selector") == selector:
                found = True
                # If there's a labels array
                if "labels" in annotation:
                    # If there's only one label and it matches, remove the entire entry
                    if len(annotation["labels"]) == 1 and annotation["labels"][0] == label_to_remove:
                        annotations.pop(i)
                    # Otherwise, remove just the specific label
                    elif label_to_remove in annotation["labels"]:
                        annotation["labels"].remove(label_to_remove)
                        # Update the primary label if needed
                        if annotation.get("label") == label_to_remove and annotation["labels"]:
                            annotation["label"] = annotation["labels"][-1]
                # If there's only a single label property
                elif annotation.get("label") == label_to_remove:
                    annotations.pop(i)
                break

        if not found:
            return jsonify({"error": "Annotation not found"}), 404

        # Save the updated annotations
        with open(path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, indent=2)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Proxy route for user tasks
@app.route('/api/proxy/get-user-tasks', methods=['POST'])
def proxy_get_user_tasks():
    try:
        data = request.json
        contact_number = str(data.get('contact_number'))


        if not contact_number:
            return jsonify({'error': 'Contact number is required'}), 400

        # Forward the request to the actual API
        response = requests.post(
            f'{API_URL}/get-user-tasks',
            json={'contact_number': contact_number},
            headers={'Content-Type': 'application/json'}
        )

        # Log the response for debugging
        print(f'Proxy API response status: {response.status_code}')
        print(f'Proxy API response content: {response.text}')

        # Return the response from the API
        # Wrap the response.json() in jsonify() to ensure proper Flask response format
        try:
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except ValueError:
            # Handle case where response is not valid JSON
            return jsonify({'error': 'Invalid JSON response from API', 'content': response.text}), 500
    except Exception as e:
        print(f'Error in proxy_get_user_tasks: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Proxy route for create annotation
@app.route('/api/proxy/create', methods=['POST'])
def proxy_create_annotation():
    try:
        data = request.json
        filename = data.get('filename')

        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        # Forward the request to the actual API
        response = requests.post(
            f'{API_URL}/create',
            json={'filename': filename},
            headers={'Content-Type': 'application/json'}
        )

        # Log the response for debugging
        print(f'Create API response status: {response.status_code}')
        print(f'Create API response content: {response.text}')

        # Return the response from the API
        # Wrap the response.json() in jsonify() to ensure proper Flask response format
        try:
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except ValueError:
            # Handle case where response is not valid JSON
            return jsonify({'error': 'Invalid JSON response from API', 'content': response.text}), 500
    except Exception as e:
        print(f'Error in proxy_create_annotation: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Proxy route for appending annotations
@app.route('/api/proxy/append', methods=['POST'])
def proxy_append_annotation():
    try:
        data = request.json
        filename = data.get('filename')
        parsed_url = urlparse(filename)
        path = parsed_url.path
        # Extract the filename
        filename = os.path.basename(path)
        # Remove .json extension if present
        if filename.endswith('.json'):
            filename = filename[:-5]
        annotation_data = data.get('data')

        if not filename or not annotation_data:
            return jsonify({'error': 'Filename and data are required'}), 400

        # The client now sends complete data objects with all properties
        # Validate and ensure all required properties are present
        for annotation in annotation_data:
            selector = annotation.get("selector")
            labels = annotation.get("label")

            if not selector or not labels:
                return jsonify({"error": "Selector and label are required in each annotation"}), 400

            # Add timestamp if not present
            if not annotation.get("timestamp"):
                annotation["timestamp"] = datetime.datetime.now().isoformat()

            # Add color if not present
            # if not annotation.get("color"):
            #     annotation["color"] = "#F44336"

            # Ensure label is an array
            if not isinstance(labels, list):
                annotation["label"] = [labels] if labels else []

            # Remove labels property if it exists
            if "labels" in annotation:
                del annotation["labels"]

            # Ensure tag and class are present and not empty
            if not annotation.get("tag") or annotation.get("tag") == "":
                # Try to extract tag from selector
                selector_parts = selector.split('.')
                if len(selector_parts) > 0 and selector_parts[0]:
                    annotation["tag"] = selector_parts[0]
                else:
                    annotation["tag"] = "div"  # Default tag

            if not annotation.get("class") or annotation.get("class") == "":
                # Try to extract class from selector
                selector_parts = selector.split('.')
                class_parts = [part for part in selector_parts if part and part != selector_parts[0]]
                if class_parts:
                    annotation["class"] = " ".join(class_parts)

            # Ensure id is present
            if not annotation.get("id"):
                annotation["id"] = ""

        # Forward the request to the actual API
        response = requests.post(
            f'{API_URL}/append',
            json={
                'filename': filename,
                'data': annotation_data
            },
            headers={'Content-Type': 'application/json'}
        )

        # Log the response for debugging
        print(f'Proxy append API response status: {response.status_code}')
        print(f'Proxy append API response content: {response.text}')

        # Return the response from the API
        # Wrap the response.json() in jsonify() to ensure proper Flask response format
        try:
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except ValueError:
            # Handle case where response is not valid JSON
            return jsonify({'error': 'Invalid JSON response from API', 'content': response.text}), 500
    except Exception as e:
        print(f'Error in proxy_append_annotation: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Proxy route for getting bounding boxes
@app.route('/api/proxy/get-bounding-boxes', methods=['GET'])
def proxy_get_bounding_boxes():
    try:
        # Get the json_name from the query parameters
        json_name = request.args.get('json_name')

        if not json_name:
            return jsonify({'error': 'json_name parameter is required'}), 400

        # Extract the filename from json_name (e.g., 'affindacom' from 'affindacom.json')
        if json_name.endswith('.json'):
            filename = json_name[:-5]  # Remove '.json' from the end
        else:
            filename = json_name

        print(f'Fetching bounding boxes for filename: {filename}')

        # Forward the request to the actual API
        response = requests.get(
            f'{API_URL}/get/{filename}',
            headers={'Accept': 'application/json'}
        )

        # Log the response for debugging
        print(f'Get bounding boxes API response status: {response.status_code}')
        print(f'Get bounding boxes API response content: {response.text}')

        # Return the response from the API
        # Wrap the response.json() in jsonify() to ensure proper Flask response format
        try:
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except ValueError:
            # Handle case where response is not valid JSON
            return jsonify({'error': 'Invalid JSON response from API', 'content': response.text}), 500
    except Exception as e:
        print(f'Error in proxy_get_bounding_boxes: {str(e)}')
        return jsonify({'error': str(e)}), 500

# User Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        contact_number = data.get('contactNumber')
        password = data.get('password')

        # Validate input
        if not contact_number or not password:
            return jsonify({'error': 'Contact number and password are required'}), 400

        # Check if user already exists
        db = get_db()
        existing_user = db.users.find_one({'contactNumber': contact_number})
        if existing_user:
            return jsonify({'error': 'User with this contact number already exists'}), 409

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Create new user
        new_user = {
            'contactNumber': contact_number,
            'password': hashed_password,
            'createdAt': datetime.datetime.now()
        }

        # Insert user into database
        result = db.users.insert_one(new_user)

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'userId': str(result.inserted_id)
        })
    except Exception as e:
        print(f'Error in register: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        contact_number = data.get('contactNumber')
        password = data.get('password')

        print(f'Login attempt for contact number: {contact_number}')

        # Validate input
        if not contact_number or not password:
            print('Login failed: Missing contact number or password')
            return jsonify({'error': 'Contact number and password are required'}), 400

        # Find user
        db = get_db()
        user = db.users.find_one({'contactNumber': contact_number})

        if not user:
            print(f'Login failed: User not found for contact number: {contact_number}')
            return jsonify({'error': 'Invalid credentials'}), 401

        # Verify password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if user['password'] != hashed_password:
            print(f'Login failed: Invalid password for contact number: {contact_number}')
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate a simple auth token (in a real app, use JWT)
        auth_token = hashlib.sha256(f"{str(user['_id'])}-{secrets.token_hex(16)}".encode()).hexdigest()

        # Store the token in the database
        db.auth_tokens.update_one(
            {'user_id': str(user['_id'])},
            {'$set': {
                'token': auth_token,
                'contact_number': user['contactNumber'],
                'created_at': datetime.datetime.now()
            }},
            upsert=True
        )

        print(f'Auth token created for user: {contact_number}')

        # Return the token to the client
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'contactNumber': user['contactNumber']
            },
            'auth_token': auth_token  # Send the token to the client
        })
    except Exception as e:
        print(f'Error in login: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        # Get auth token from Authorization header
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            # Extract the token
            token = auth_header.split(' ')[1]
            print(f'Logging out token: {token}')

            # Remove the token from the database
            db = get_db()
            result = db.auth_tokens.delete_one({'token': token})

            if result.deleted_count > 0:
                print(f'Token removed successfully')
            else:
                print(f'Token not found in database')

        # Clear session as well (for backward compatibility)
        session.clear()

        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        print(f'Error in logout: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        # Log request information for debugging
        print(f'Request method: {request.method}')
        print(f'Request headers: {dict(request.headers)}')

        # Get auth token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            print('No Authorization header or invalid format')
            return jsonify({
                'success': False,
                'error': 'Not authenticated',
                'auth_required': True  # Special flag for frontend to redirect to login
            }), 200  # Return 200 instead of 401 to avoid CORS preflight issues

        # Extract the token
        token = auth_header.split(' ')[1]
        print(f'Auth token received: {token}')

        # Find the token in the database
        db = get_db()
        token_doc = db.auth_tokens.find_one({'token': token})

        if not token_doc:
            print('Invalid or expired token')
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token',
                'auth_required': True
            }), 200

        # Get the user information
        user_id = token_doc['user_id']
        contact_number = token_doc['contact_number']

        print(f'User authenticated via token: user_id={user_id}, contact_number={contact_number}')

        # Get user from database to ensure it still exists
        user = db.users.find_one({'_id': ObjectId(user_id)})

        if not user:
            print(f'User not found in database: user_id={user_id}')
            # Remove the invalid token
            db.auth_tokens.delete_one({'token': token})
            return jsonify({
                'success': False,
                'error': 'User not found',
                'auth_required': True
            }), 200

        return jsonify({
            'success': True,
            'user': {
                'contactNumber': contact_number
            }
        })
    except Exception as e:
        print(f'Error in get_user: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable (Render.com sets this automatically)
    port = int(os.environ.get('PORT', 5001))

    # Set debug mode based on environment
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'

    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
