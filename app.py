from flask import Flask, jsonify, request, session, make_response
from flask_talisman import Talisman
from functools import wraps
from dotenv import load_dotenv
import jwt
from waitress import serve
import requests
from db_config import DB_CONFIG
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, timedelta
from flask_cors import CORS
from models import db, Warehouse, Category, SubCategory, Product, Inventory, InventoryAlert, Order, OrderItem, Return
import os
import random
import string

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Replace with a secure key
app.config['SESSION_TYPE'] = 'filesystem'     # Use 'redis' for production
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG
JWT_ALGORITHM = 'HS256'
RBAC_SERVICE_URL = 'https://localhost:5001'
CA_CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "ca.crt")
csrf = CSRFProtect(app) # Enable CSRF protection for Flask app

db.init_app(app)

# Initialize the database
with app.app_context():
    db.create_all()

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            authenticated, user_data = is_authenticated()
            if not authenticated:
                return jsonify({'error': 'Unauthorized'}), 401
            user_roles = user_data.get('roles', [])
            if not any(role in user_roles for role in required_roles):
                return jsonify({'error': 'Forbidden: Insufficient role'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(required_permissions):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            authenticated, user_data = is_authenticated()
            if not authenticated:
                return jsonify({'error': 'Unauthorized'}), 401
            user_permissions = user_data.get('permissions', [])
            if not any(perm in user_permissions for perm in required_permissions):
                return jsonify({'error': 'Forbidden: Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Set up the path to your certificates
cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "flask.crt")
key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "flask.key")
print(cert_path, key_path)
# Enforce HTTPS with Flask-Talisman for security headers
Talisman(app, content_security_policy={
    'default-src': ["'self'"],
    'img-src': ["'self'", "data:"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'script-src': ["'self'"]
})

# Enable CORS for React frontend (assuming it's running on https://localhost:3000)
CORS(app, origins=["https://localhost:3000"], supports_credentials=True)

def is_authenticated():
    token = request.cookies.get('token')
    if not token:
        print("No token found in cookies.")
        return False, None

    try:
        response = requests.post(
            f'{RBAC_SERVICE_URL}/api/verify-token',
            json={'token': token},
            verify=CA_CERT_PATH
        )
        # print(f"Verify Token Response Status Code: {response.status_code}")
        # print(f"Verify Token Response Content: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print(f"Authentication successful for user_id: {data.get('user_id')}")
            return True, data  # Includes 'user_id', 'roles', 'permissions'
        else:
            print(f"Authentication failed with status {response.status_code}: {response.json()}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"Error verifying token with RBAC service: {e}")
        return False, None

def generate_admin_url():
    return '/admin-' + ''.join(random.choices(string.ascii_letters + string.digits, k=12))

admin_url = generate_admin_url()
print(f"Admin URL: {admin_url}")  # For server logs only

@app.route('/api/get-csrf-token', methods=['GET'])
def get_csrf_token():
    try:
        response = requests.get(
            f'{RBAC_SERVICE_URL}/api/get-csrf-token',
            cookies=request.cookies,
            verify=CA_CERT_PATH
        )

        resp = make_response(response.content, response.status_code)

        if 'Set-Cookie' in response.headers:
            resp.headers['Set-Cookie'] = response.headers['Set-Cookie']

        return resp
    except requests.exceptions.RequestException as e:
        print(f"Error contacting RBAC service: {e}")
        return jsonify({'error': 'CSRF token service unavailable'}), 503

@app.route('/api/login', methods=['POST'])
@csrf.exempt
def login():
    try:
        # Forward the login request to the RBAC service
        response = requests.post(
            f'{RBAC_SERVICE_URL}/api/login',
            json=request.get_json(),
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': request.headers.get('X-CSRFToken')
            },
            cookies=request.cookies,
            verify=CA_CERT_PATH
        )

        # Create a response object to return to the client
        resp = make_response(response.content, response.status_code)

        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            roles = data.get('roles', [])
            permissions = data.get('permissions', [])

            if token:
                # Set the token cookie for the main application
                resp.set_cookie(
                    'token',
                    token,
                    httponly=True,
                    secure=True,
                    samesite='Strict'  # Changed from 'Strict' to 'None'
                )

        return resp
    except requests.exceptions.RequestException as e:
        print(f"Error contacting RBAC service: {e}")
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
@app.route('/api/get-admin-url', methods=['GET'])
def get_admin_url():
    authenticated, user_data = is_authenticated()
    if not authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'admin_url': admin_url})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    authenticated, user_data = is_authenticated()
    if authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': user_data.get('user_id'),
            'roles': user_data.get('roles'),
            'permissions': user_data.get('permissions')
        }), 200
    else:
        return jsonify({'authenticated': False}), 401

@csrf.exempt
@app.route('/api/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.set_cookie('token', '', expires=0, httponly=True, secure=True, samesite='Strict')
    return response

# Test Route
@app.route('/api/data')
def get_data():
    return jsonify({"message": "Secure data transfer over HTTPS!"})

@app.route('/api/dashboard')
@role_required(['Admin'])
def get_dashboard():
    data= {
        "totalProducts": 320,
        "ordersToday": 15,
        "totalCustomers": 1234,
        "pendingOrders": 42
}
    return jsonify(data)


if __name__ == "__main__":
    app.run(ssl_context=(cert_path, key_path), host='0.0.0.0', port=5000, debug=True)
