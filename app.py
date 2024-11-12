from flask import Flask, jsonify, request, session, make_response
from flask_talisman import Talisman
import jwt
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, timedelta
from flask_cors import CORS
import os
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['SESSION_TYPE'] = 'filesystem'     # Use 'redis' for production
JWT_ALGORITHM = 'HS256'
csrf = CSRFProtect(app) # Enable CSRF protection for Flask app

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
        return False
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[JWT_ALGORITHM])
        return payload.get('authenticated', False)
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def generate_admin_url():
    return '/admin-' + ''.join(random.choices(string.ascii_letters + string.digits, k=12))

admin_url = generate_admin_url()
print(f"Admin URL: {admin_url}")  # For server logs only

@app.route('/api/get-csrf-token', methods=['GET'])
def get_csrf_token():
    response = make_response(jsonify({'message': 'CSRF token set'}))
    response.set_cookie('csrf_token', generate_csrf(), secure=True, httponly=False, samesite='Strict')
    return response

@csrf.exempt # disable CSRF protection for route, exempting the login route is generally acceptable because the user doesn't have a session yet.
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # Validate credentials (replace with real validation)
    if username == 'admin' and password == 'password':
        # Create JWT token
        payload = {
            'authenticated': True,
            'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm=JWT_ALGORITHM)
        response = make_response(jsonify({'message': 'Login successful'}), 200)
        response.set_cookie(
            'token',
            token,
            httponly=True, # to prevent XSS attacks
            secure=True, # ensure only sent over HTTPS
            samesite='Strict'  # Adjust maybe?
        )
        return response
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    
@app.route('/api/get-admin-url', methods=['GET'])
def get_admin_url():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'admin_url': admin_url})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    authenticated = is_authenticated()
    return jsonify({'authenticated': authenticated}), 200 if authenticated else 401

@csrf.exempt
@app.route('/api/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    response.set_cookie('token', '', expires=0)
    return response

# Test Route
@app.route('/api/data')
def get_data():
    return jsonify({"message": "Secure data transfer over HTTPS!"})

@app.route('/api/dashboard')
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
