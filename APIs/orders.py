from flask import request, jsonify

# customer creates order items, and when they submit, it creates an order

# create orders:
def create_order():
    from app import db, Order
    """
    Create a new order.
    Expected JSON payload:
    {
        "Total_Amount": 100.0,
        "Order_Date": "2024-11-17",
        "Status": "Pending",
        "Total_Price": 150.0
    }
    """
    try:
        data = request.get_json()

        # Extract and validate required fields
        total_amount = data.get('Total_Amount')
        order_date = data.get('Order_Date')
        status = data.get('Status')
        total_price = data.get('Total_Price')

        if not all([total_amount, order_date, status, total_price]):
            return jsonify({'error': 'All fields (Total_Amount, Order_Date, Status, Total_Price) are required'}), 400

        # Create and save the new order
        new_order = Order(
            Total_Amount=total_amount,
            Order_Date=order_date,
            Status=status,
            Total_Price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({'message': 'Order created successfully', 'Order_ID': new_order.Order_ID}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# update_order:
def update_order_status(order_id):
    from app import db, Order
    """
    Update the status of an order.
    Expected JSON payload:
    {
        "Status": "Completed"
    }
    """
    try:
        data = request.get_json()
        new_status = data.get('Status')

        if not new_status:
            return jsonify({'error': 'Status is required'}), 400

        # Find the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': f'Order with ID {order_id} not found'}), 404

        # Update the status
        order.Status = new_status
        db.session.commit()

        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# view all orders:
def view_all_orders():
    from app import db, Order
    """
    View all orders in the system.
    """
    try:
        # Query all orders from the database
        orders = Order.query.all()

        if not orders:
            return jsonify({'message': 'No orders found'}), 200

        # Serialize the orders
        order_list = [
            {
                'Order_ID': order.Order_ID,
                'Total_Amount': order.Total_Amount,
                'Order_Date': str(order.Order_Date),
                'Status': order.Status,
                'Total_Price': order.Total_Price
            }
            for order in orders
        ]

        return jsonify(order_list), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
#create order item:
def create_order_item():
    from app import db, OrderItem
    """
    Create a new order item.
    Expected JSON payload:
    {
        "Order_ID": 1,
        "Product_ID": 101,
        "Quantity": 2,
        "Price": 50.0
    }
    """
    try:
        data = request.get_json()

        # Extract and validate required fields
        order_id = data.get('Order_ID')
        product_id = data.get('Product_ID')
        quantity = data.get('Quantity')
        price = data.get('Price')

        if not all([order_id, product_id, quantity, price]):
            return jsonify({'error': 'All fields (Order_ID, Product_ID, Quantity, Price) are required'}), 400

        # Create and save the new order item
        new_order_item = OrderItem(
            Order_ID=order_id,
            Product_ID=product_id,
            Quantity=quantity,
            Price=price
        )
        db.session.add(new_order_item)
        db.session.commit()

        return jsonify({'message': 'Order item added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

#remove order item:
def remove_order_item():
    from app import db, OrderItem
    """
    Remove an order item.
    Expected JSON payload:
    {
        "Order_ID": 1,
        "Product_ID": 101
    }
    """
    try:
        data = request.get_json()

        # Extract and validate required fields
        order_id = data.get('Order_ID')
        product_id = data.get('Product_ID')

        if not all([order_id, product_id]):
            return jsonify({'error': 'Order_ID and Product_ID are required'}), 400

        # Find the order item
        order_item = OrderItem.query.filter_by(Order_ID=order_id, Product_ID=product_id).first()

        if not order_item:
            return jsonify({'error': f'Order item with Order_ID {order_id} and Product_ID {product_id} not found'}), 404

        # Delete the order item
        db.session.delete(order_item)
        db.session.commit()

        return jsonify({'message': 'Order item removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    

# return item, should delete from orders