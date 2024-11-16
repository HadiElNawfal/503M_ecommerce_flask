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
