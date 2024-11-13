from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import DB_CONFIG

db = SQLAlchemy()

# Inventory Management Tables
class Warehouse(db.Model):
    __tablename__ = 'warehouse'
    Warehouse_ID = db.Column(db.Integer, primary_key=True)
    Manager_Name = db.Column(db.String(100), nullable=False)
    Location = db.Column(db.String(200), nullable=False)
    
    # Relationship to Inventory
    inventories = db.relationship('Inventory', back_populates='warehouse')

class Category(db.Model):
    __tablename__ = 'category'
    Category_ID = db.Column(db.Integer, primary_key=True)
    Category_Name = db.Column(db.String(100), nullable=False)

    # Relationship to SubCategory and Product
    subcategories = db.relationship('SubCategory', back_populates='category')
    products = db.relationship('Product', back_populates='category')
    
class SubCategory(db.Model):
    __tablename__ = 'subcategory'
    SubCategory_ID = db.Column(db.Integer, primary_key=True)
    SubCategory_Name = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(255))
    
    # Foreign key to Category
    Category_ID = db.Column(db.Integer, db.ForeignKey('category.Category_ID'), nullable=False)
    
    # Back-populates relationship
    category = db.relationship('Category', back_populates='subcategories')
    products = db.relationship('Product', back_populates='subcategory')

class Product(db.Model):
    __tablename__ = 'product'
    Product_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Price = db.Column(db.Float, nullable=False)
    Description = db.Column(db.String(255))
    ImageURL = db.Column(db.String(255))
    Listed = db.Column(db.Boolean, default=True)
    Discount_Percentage = db.Column(db.Integer, default=0)
    
    # Foreign keys to Category and SubCategory
    Category_ID = db.Column(db.Integer, db.ForeignKey('category.Category_ID'), nullable=False)
    SubCategory_ID = db.Column(db.Integer, db.ForeignKey('subcategory.SubCategory_ID'), nullable=False)
    
    # Back-populates relationships
    category = db.relationship('Category', back_populates='products')
    subcategory = db.relationship('SubCategory', back_populates='products')
    inventories = db.relationship('Inventory', back_populates='product')
    order_items = db.relationship('OrderItem', back_populates='product')

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    # Composite primary key columns (also foreign keys)
    Product_ID = db.Column(db.Integer, db.ForeignKey('product.Product_ID'), primary_key=True)
    Warehouse_ID = db.Column(db.Integer, db.ForeignKey('warehouse.Warehouse_ID'), primary_key=True)
    
    # Regular columns
    Stock_Level = db.Column(db.Integer, nullable=False)
    
    # Relationships
    product = db.relationship('Product', back_populates='inventories')
    warehouse = db.relationship('Warehouse', back_populates='inventories')
    alerts = db.relationship('InventoryAlert', back_populates='inventory')

class InventoryAlert(db.Model):
    __tablename__ = 'inventory_alert'
    
    # Primary key
    Alert_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys (reference composite key of Inventory)
    Product_ID = db.Column(db.Integer, nullable=False)
    Warehouse_ID = db.Column(db.Integer, nullable=False)
    
    # Regular columns
    Alert_Date = db.Column(db.Date, nullable=False)
    Description_of_Alert = db.Column(db.String(255))
    
    # Composite foreign key constraint
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['Product_ID', 'Warehouse_ID'],
            ['inventory.Product_ID', 'inventory.Warehouse_ID']
        ),
    )
    
    # Relationship
    inventory = db.relationship('Inventory', back_populates='alerts')

# Order Management Tables
class Order(db.Model):
    __tablename__ = 'order'
    Order_ID = db.Column(db.Integer, primary_key=True)
    Total_Amount = db.Column(db.Float, nullable=False)
    Order_Date = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(50), nullable=False)
    Total_Price = db.Column(db.Float, nullable=False)
    
    # Relationship to OrderItem and Return
    order_items = db.relationship('OrderItem', back_populates='order')
    returns = db.relationship('Return', back_populates='order')

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    Quantity = db.Column(db.Integer, nullable=False)
    Price = db.Column(db.Float, nullable=False)
    
    # Composite primary key with Order_ID and Product_ID
    Order_ID = db.Column(db.Integer, db.ForeignKey('order.Order_ID'), primary_key=True)
    Product_ID = db.Column(db.Integer, db.ForeignKey('product.Product_ID'), primary_key=True)
    
    # Back-populates relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

class Return(db.Model):
    __tablename__ = 'return'
    Return_ID = db.Column(db.Integer, primary_key=True)
    Return_Date = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(50), nullable=False)
    Refund_Amount = db.Column(db.Float, nullable=False)
    
    # Foreign key to Order
    Order_ID = db.Column(db.Integer, db.ForeignKey('order.Order_ID'), nullable=False)
    
    # Back-populates relationship
    order = db.relationship('Order', back_populates='returns')
