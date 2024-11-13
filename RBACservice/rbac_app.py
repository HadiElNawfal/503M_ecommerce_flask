from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from models import db, User, Role, Permission
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, timedelta
from db_config import DB_CONFIG
from waitress import serve
import jwt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG
JWT_ALGORITHM = 'HS256'
csrf = CSRFProtect(app)
CORS(app, origins=["https://localhost:3000"], supports_credentials=True)

cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "rbac.crt")
key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "rbac.key")


db.init_app(app)
def create_roles_and_permissions():
    # Permissions
    permission_names = [
        'add_inventory', 'remove_inventory', 'update_inventory', 'view_inventory',
        'add_product', 'remove_product', 'update_product', 'view_product',
        'add_order', 'remove_order', 'update_order', 'view_order',
    ]
    
    permissions = {}
    for name in permission_names:
        # Check if the permission already exists
        permission = Permission.query.filter_by(Name=name).first()
        if not permission:
            permission = Permission(Name=name)
            db.session.add(permission)
        permissions[name] = permission

    # Roles
    role_names = ['Admin', 'Product Manager', 'Inventory Manager', 'Order Manager', 'Customer']
    roles = {}
    for name in role_names:
        # Check if the role already exists
        role = Role.query.filter_by(Name=name).first()
        if not role:
            role = Role(Name=name)
            db.session.add(role)
        roles[name] = role

    db.session.commit()  # Commit to assign IDs before setting relationships

    # Assign permissions to roles
    roles['Admin'].permissions = list(permissions.values())

    roles['Product Manager'].permissions = [
        permissions['add_product'],
        permissions['remove_product'],
        permissions['update_product'],
        permissions['view_product'],
    ]

    roles['Inventory Manager'].permissions = [
        permissions['add_inventory'],
        permissions['remove_inventory'],
        permissions['update_inventory'],
        permissions['view_inventory'],
    ]

    roles['Order Manager'].permissions = [
        permissions['add_order'],
        permissions['remove_order'],
        permissions['update_order'],
        permissions['view_order'],
    ]

    roles['Customer'].permissions = [
        permissions['view_product'],
        permissions['view_order'],
    ]

    db.session.commit()
def create_users():
    # Fetch roles from the database
    roles = {}
    role_names = ['Admin', 'Product Manager', 'Inventory Manager', 'Order Manager', 'Customer']
    for name in role_names:
        role = Role.query.filter_by(Name=name).first()
        if role:
            roles[name] = role
        else:
            print(f"Role '{name}' not found. Please ensure roles are created properly.")

    # Helper function to create users
    def create_user(username, password, role):
        user = User.query.filter_by(Username=username).first()
        if not user:
            user = User(Username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()  # Commit to assign an ID
            user.roles.append(role)
            db.session.commit()
        else:
            if role not in user.roles:
                user.roles.append(role)
                db.session.commit()

    # Create users for each role
    create_user('admin', 'admin123', roles['Admin'])
    create_user('product_manager', 'product123', roles['Product Manager'])
    create_user('inventory_manager', 'inventory123', roles['Inventory Manager'])
    create_user('order_manager', 'order123', roles['Order Manager'])
    create_user('customer', 'customer123', roles['Customer'])
# Initialize the database
with app.app_context():
    db.create_all()
    create_roles_and_permissions()  # Ensure roles and permissions are created
    create_users()   # Now create users for each role

@app.after_request
def set_csrf_cookie(response):
    response.set_cookie('csrf_token', generate_csrf(), secure=True, httponly=True, samesite='Strict')
    return response

@app.route('/api/get-csrf-token', methods=['GET'])
def get_csrf_token():
    csrf_token = generate_csrf()
    response = jsonify({'csrf_token': csrf_token})
    response.set_cookie('csrf_token', csrf_token, secure=True, httponly=True, samesite='Strict')
    return response

@app.route('/api/login', methods=['POST'])
@csrf.exempt
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(Username=username).first()
    if user and user.check_password(password):
        # Gather roles and permissions
        user_roles = [role.Name for role in user.roles]
        user_permissions = []
        for role in user.roles:
            user_permissions.extend([perm.Name for perm in role.permissions])
        user_permissions = list(set(user_permissions))  # Remove duplicates

        # Create the JWT payload
        payload = {
            'user_id': user.User_ID,
            'roles': user_roles,
            'permissions': user_permissions,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm=JWT_ALGORITHM)

        return jsonify({
            'message': 'Login successful',
            'permissions': user_permissions,
            'roles': user_roles,
            'token': token
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/verify-token', methods=['POST'])
@csrf.exempt
def verify_token():
    data = request.get_json()
    # print(f"Received verify-token request data: {data}")  # Logging received data
    token = data.get('token')
    if not token:
        print("Token is missing in the request.")
        return jsonify({'error': 'Token is missing'}), 400
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        # print(f"Decoded token for user_id: {user_id}")
        # Fetch user from the database
        user = User.query.get(user_id)
        if not user:
            print(f"User with ID {user_id} not found.")
            return jsonify({'error': 'User not found'}), 404
        # Get user's roles and permissions
        roles = [role.Name for role in user.roles]
        permissions = []
        for role in user.roles:
            permissions.extend([perm.Name for perm in role.permissions])
        permissions = list(set(permissions))  # Remove duplicates
        print(f"User Roles: {roles}")
        print(f"User Permissions: {permissions}")
        return jsonify({
            'user_id': user_id,
            'roles': roles,
            'permissions': permissions
        }), 200
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        print("Invalid token.")
        return jsonify({'error': 'Invalid token'}), 401
    
if __name__ == "__main__":
    app.run(ssl_context=(cert_path, key_path),host='0.0.0.0',port=5001, debug=True)