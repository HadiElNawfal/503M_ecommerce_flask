from flask import request, jsonify
from datetime import datetime
from sqlalchemy import extract, func

def edit_inventory(warehouse_id):
    from app import Inventory, db, Product
    """Edit inventory stock level by adding or removing stock."""
    data = request.get_json()

    # Extract data from the request
    product_id = data.get('Product_ID')
    to_be_added = data.get('to_be_added')

    # Validate inputs
    if not product_id or not warehouse_id:
        return jsonify({'error': 'Product_ID and Warehouse_ID are required'}), 400

    if to_be_added is None:  # Check for None because 0 is valid input
        return jsonify({'error': 'Please specify the quantity to be added or removed'}), 400

    try:
        # Find the inventory record
        inventory = Inventory.query.filter_by(Product_ID=product_id, Warehouse_ID=warehouse_id).first()

        if not inventory:
            return jsonify({'error': 'Inventory record not found'}), 404

        # Update the stock level
        new_stock_level = inventory.Stock_Level + int(to_be_added)
        if new_stock_level < 0:
            return jsonify({'error': 'Stock level cannot be negative'}), 400

        inventory.Stock_Level = new_stock_level
        db.session.commit()

        return jsonify({
            'message': 'Stock level updated successfully',
            'Product_ID': product_id,
            'Warehouse_ID': warehouse_id,
            'New_Stock_Level': inventory.Stock_Level
        }), 200

    except Exception as e:
        db.session.rollback()  # Roll back transaction in case of error
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

#view inventory:
def view_inventory(warehouse_id):
    from app import Inventory, Product, Warehouse
    """
    View inventory for a specific warehouse.
    :param warehouse_id: The ID of the warehouse whose inventory is to be viewed.
    """
    try:
        # Check if the warehouse exists
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return jsonify({'error': f'Warehouse with ID {warehouse_id} not found'}), 404

        # Query inventory for the given warehouse
        inventory_items = Inventory.query.filter_by(Warehouse_ID=warehouse_id).all()

        # If no inventory is found, return an empty list
        if not inventory_items:
            return jsonify({'message': 'No inventory items found for this warehouse'}), 200

        # Format the response with inventory details
        inventory_data = []
        for item in inventory_items:
            product = Product.query.get(item.Product_ID)  # Get the product details
            inventory_data.append({
                'Product_ID': item.Product_ID,
                'Product_Name': product.Name if product else "Unknown Product",
                'Stock_Level': item.Stock_Level,
                'Warehouse_ID': item.Warehouse_ID,
            })

        return jsonify({
            'Warehouse_ID': warehouse_id,
            'Inventory': inventory_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def initialize_inventory():
    from app import db, Product, Warehouse, Inventory
    """
    Add all products to the inventory of each warehouse with stock = 0 if not already present.
    """
    try:
        # Fetch all warehouses and products
        warehouses = Warehouse.query.all()
        products = Product.query.all()

        if not warehouses:
            print("No warehouses found.")
            return
        
        if not products:
            print("No products found.")
            return

        for warehouse in warehouses:
            for product in products:
                # Check if the product already exists in the inventory for the current warehouse
                existing_inventory = Inventory.query.filter_by(
                    Product_ID=product.Product_ID,
                    Warehouse_ID=warehouse.Warehouse_ID
                ).first()

                if not existing_inventory:
                    # Add the product to the warehouse's inventory with stock = 0
                    new_inventory = Inventory(
                        Product_ID=product.Product_ID,
                        Warehouse_ID=warehouse.Warehouse_ID,
                        Stock_Level=0
                    )
                    db.session.add(new_inventory)
                    print(f"Added Product_ID {product.Product_ID} to Warehouse_ID {warehouse.Warehouse_ID} with Stock_Level 0")

        # Commit the changes to the database
        db.session.commit()
        print("Inventory initialization completed successfully.")

    except Exception as e:
        db.session.rollback()  # Rollback in case of any errors
        print(f"An error occurred during inventory initialization: {str(e)}")
        


# inventory reports:
# monthly turnover:
def get_monthly_inventory_turnover(warehouse_id):
    from app import db, User, Warehouse, Inventory, OrderItem, Order
    """
    Get monthly inventory turnover for the inventory manager.
    :param user_id: The ID of the inventory manager (username or user_id).
    :return: Monthly revenue for the manager's inventory in the format:
             {"labels": ["January", "February", ...], "values": [1000, 1500, ...]}
    """
    try:
        # Step 2: Get all Product_IDs managed by this inventory manager
        inventory_items = Inventory.query.filter(Inventory.Warehouse_ID.in_(warehouse_id)).all()
        product_ids = [item.Product_ID for item in inventory_items]

        if not product_ids:
            return jsonify({'error': 'No products found in the inventory for this manager'}), 404

        # Step 3: Calculate revenue per month based on orders
        # Join OrderItem, Order, and filter by Product_ID and Order_Date
        turnover_data = db.session.query(
            extract('month', Order.Order_Date).label('month'),  # Extract month from the order date
            func.sum(OrderItem.Quantity * OrderItem.Price).label('revenue')  # Calculate revenue
        ).join(OrderItem, Order.Order_ID == OrderItem.Order_ID) \
         .filter(OrderItem.Product_ID.in_(product_ids)) \
         .group_by('month') \
         .order_by('month') \
         .all()

        # Step 4: Prepare the response in the desired format
        month_labels = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        turnover_dict = {month: 0 for month in range(1, 13)}  # Initialize all months with 0 revenue

        for row in turnover_data:
            month = row.month  # Extract the month
            revenue = row.revenue  # Extract the revenue for the month
            turnover_dict[month] = revenue

        # Format the response
        response = {
            "labels": [month_labels[month - 1] for month in turnover_dict.keys()],  # Month names
            "values": [turnover_dict[month] for month in turnover_dict.keys()]  # Monthly revenue values
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
# most popular products:
def get_most_popular_products(warehouse_id):
    from app import db, Product, Inventory, OrderItem
    """
    Get the most popular products for a given warehouse.
    :param warehouse_id: The ID of the warehouse to calculate popularity for.
    :return: Popular products in the format:
             {"labels": ["Apple", "Banana", "Orange", ...], "values": [200, 150, 300, ...]}
    """
    try:
        # Step 1: Get all Product_IDs managed by this warehouse
        inventory_items = Inventory.query.filter(Inventory.Warehouse_ID == warehouse_id).all()
        product_ids = [item.Product_ID for item in inventory_items]

        if not product_ids:
            return jsonify({'error': 'No products found in the inventory for this manager'}), 404

        # Step 2: Calculate popularity based on quantity sold
        popular_data = db.session.query(
            Product.Name.label('product_name'),  # Product name for labels
            func.sum(OrderItem.Quantity).label('total_quantity')  # Sum of quantities sold
        ).join(OrderItem, OrderItem.Product_ID == Product.Product_ID) \
         .filter(OrderItem.Product_ID.in_(product_ids)) \
         .group_by(Product.Name) \
         .order_by(func.sum(OrderItem.Quantity).desc()) \
         .all()

        if not popular_data:
            return jsonify({'error': 'No sales data found for these products'}), 404

        # Step 3: Prepare the response
        labels = [row.product_name for row in popular_data]
        values = [row.total_quantity for row in popular_data]

        response = {
            "labels": labels,
            "values": values
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
