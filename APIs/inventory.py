from flask import request, jsonify

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
        new_stock_level = inventory.Stock_Level + to_be_added
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