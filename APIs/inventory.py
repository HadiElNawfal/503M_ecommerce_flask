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

def view_inventory(warehouse_id=None):
    from app import Inventory, Product, Warehouse, db
    """
    View inventory for a specific warehouse or all warehouses.
    :param warehouse_id: (Optional) The ID of the warehouse whose inventory is to be viewed.
    """
    try:
        # Query warehouses
        if warehouse_id:
            warehouse = Warehouse.query.get(warehouse_id)
            if not warehouse:
                return jsonify({'error': f'Warehouse with ID {warehouse_id} not found'}), 404
            warehouses = [warehouse]  # Treat as a list for consistent processing
        else:
            warehouses = Warehouse.query.all()
            if not warehouses:
                return jsonify({'error': 'No warehouses found'}), 404

        # Prepare response data
        inventory_data = []
        for warehouse in warehouses:
            inventory_items = Inventory.query.filter_by(Warehouse_ID=warehouse.Warehouse_ID).all()

            # Gather inventory data for this warehouse
            for item in inventory_items:
                product = Product.query.get(item.Product_ID)  # Get the product details
                inventory_data.append({
                    'Product_ID': item.Product_ID,
                    'Product_Name': product.Name if product else "Unknown Product",
                    'Stock_Level': item.Stock_Level,
                    'Warehouse_ID': warehouse.Warehouse_ID,  # Ensure correct Warehouse_ID is included
                })
        # Return data in a consistent structure
        return jsonify({'inventory': inventory_data}), 200

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


# Assuming `warehouse_id` is passed to this function
def get_monthly_inventory_turnover(warehouse_id):
    from app import db, Inventory, Order, OrderItem

    # Get all Product_IDs managed by this inventory manager
    inventory_items = Inventory.query.filter_by(Warehouse_ID=warehouse_id).all()
    product_ids = [item.Product_ID for item in inventory_items]

    if not product_ids:
        return jsonify({'error': 'No products found in the inventory for this manager'}), 404

    # Calculate revenue per month based on orders
    turnover_data_query = (
        db.session.query(
            extract('month', Order.Order_Date).label('month'),
            func.sum(OrderItem.Quantity * OrderItem.Price).label('revenue')
        )
        .join(OrderItem, Order.Order_ID == OrderItem.Order_ID)
        .filter(OrderItem.Product_ID.in_(product_ids))
        .group_by(extract('month', Order.Order_Date))
        .order_by(extract('month', Order.Order_Date))
        .all()
    )

    # Prepare the response in the desired format
    month_labels = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    labels = []
    values = []

    for row in turnover_data_query:
        month = int(row.month)
        labels.append(month_labels[month - 1])
        values.append(float(row.revenue))

    turnover_data = {
        "labels": labels,
        "values": values
    }
    return jsonify({
        "turnoverData": turnover_data,
    }), 200

    
# most popular products:
def get_most_popular_products(warehouse_id):
    from app import db, Product, Inventory, OrderItem
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
        values = [float(row.total_quantity) for row in popular_data]  #Convert Decimal to float

        popular_products_data = {
            "labels": labels,
            "values": values
        }
        return jsonify({
            "popularProductsData": popular_products_data,
        }), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    

def get_demands():
     demand_prediction_data = {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "values": [300, 400, 450, 500]
    }
     return jsonify({"demandPredictionData": demand_prediction_data}), 200
