from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for User and Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.User_ID')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.Role_ID'))
)

# Association table for Role and Permission
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.Role_ID')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.Permission_ID'))
)

class User(db.Model):
    __tablename__ = 'user'
    User_ID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(64), unique=True, nullable=False)
    Password_Hash = db.Column(db.String(256), nullable=False)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')

    def set_password(self, password):
        self.Password_Hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password_Hash, password)

class Role(db.Model):
    __tablename__ = 'role'
    Role_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(64), unique=True, nullable=False)
    
    # Relationships
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    permissions = db.relationship('Permission', secondary=role_permissions, back_populates='roles')

class Permission(db.Model):
    __tablename__ = 'permission'
    Permission_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(64), unique=True, nullable=False)
    
    # Relationships
    roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')