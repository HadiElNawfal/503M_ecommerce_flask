from flask import Flask, jsonify, request, make_response

# API to create a category
def create_category():
    from app import Category, db
    """Create a new category."""
    data = request.get_json()
    category_name = data.get('Category_Name')

    # Validate input
    if not category_name:
        return jsonify({'error': 'Category_Name is required'}), 400

    # Check for duplicate category
    existing_category = Category.query.filter_by(Category_Name=category_name).first()
    if existing_category:
        return jsonify({'error': 'Category already exists'}), 409

    # Create and save the new category
    new_category = Category(Category_Name=category_name)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({'message': 'Category created successfully', 'Category_ID': new_category.Category_ID}), 201


# API to create a subcategory
def create_subcategory():
    from app import SubCategory, db
    """Create a new subcategory."""
    data = request.get_json()
    subcategory_name = data.get('SubCategory_Name')
    description = data.get('Description', '')  # Optional field

    # Validate input
    if not subcategory_name:
        return jsonify({'error': 'SubCategory_Name and Category_ID are required'}), 400

    # Check for duplicate subcategory within the same category
    existing_subcategory = SubCategory.query.filter_by(SubCategory_Name=subcategory_name).first()
    if existing_subcategory:
        return jsonify({'error': 'SubCategory already exists under this category'}), 409

    # Create and save the new subcategory
    new_subcategory = SubCategory(
        SubCategory_Name=subcategory_name,
        Description=description,
    )
    db.session.add(new_subcategory)
    db.session.commit()

    return jsonify({'message': 'SubCategory created successfully', 'SubCategory_ID': new_subcategory.SubCategory_ID}), 201


# Get all products:
def get_products():
    from app import Product, db
    """Retrieve all products."""
    products = Product.query.all()
    return jsonify([
        {
            'Product_ID': product.Product_ID,
            'Name': product.Name,
            'Price': product.Price,
            'Description': product.Description,
            'ImageURL': product.ImageURL,
            'Listed': product.Listed,
            'Discount_Percentage': product.Discount_Percentage,
            'Category_ID': product.Category_ID,
            'SubCategory_ID': product.SubCategory_ID
        } for product in products
    ]), 200
    
# Get a single product: 
def get_product(product_id):
    from app import Product, db
    """Retrieve a single product by ID."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({
        'Product_ID': product.Product_ID,
        'Name': product.Name,
        'Price': product.Price,
        'Description': product.Description,
        'ImageURL': product.ImageURL,
        'Listed': product.Listed,
        'Discount_Percentage': product.Discount_Percentage,
        'Category_ID': product.Category_ID,
        'SubCategory_ID': product.SubCategory_ID
    }), 200

# Add Product API:
def add_product():
    from app import Product, db
    """Add a new product."""
    data = request.get_json()

    # Extract and validate input
    name = data.get('Name')
    price = data.get('Price')
    description = data.get('Description', '')
    image_url = data.get('ImageURL', '')
    listed = data.get('Listed', True)
    discount_percentage = data.get('Discount_Percentage', 0)
    category_id = data.get('Category_ID')
    subcategory_id = data.get('SubCategory_ID')

    if not name or price is None or category_id is None or subcategory_id is None:
        return jsonify({'error': 'Name, Price, Category_ID, and SubCategory_ID are required'}), 400

    if discount_percentage < 0 or discount_percentage > 100:
        return jsonify({'error': 'Discount_Percentage must be between 0 and 100'}), 400

    # Create a new product
    new_product = Product(
        Name=name,
        Price=price,
        Description=description,
        ImageURL=image_url,
        Listed=listed,
        Discount_Percentage=discount_percentage,
        Category_ID=category_id,
        SubCategory_ID=subcategory_id
    )

    # Save to the database
    db.session.add(new_product)
    db.session.commit()

    return jsonify({'message': 'Product added successfully', 'Product_ID': new_product.Product_ID}), 201

# Update Product API:
def update_product(product_id):
    from app import Product, db
    """Update an existing product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()

    # Update fields if provided
    product.Name = data.get('Name', product.Name)
    product.Price = data.get('Price', product.Price)
    product.Description = data.get('Description', product.Description)
    product.ImageURL = data.get('ImageURL', product.ImageURL)
    product.Listed = data.get('Listed', product.Listed)
    product.Discount_Percentage = data.get('Discount_Percentage', product.Discount_Percentage)
    product.Category_ID = data.get('Category_ID', product.Category_ID)
    product.SubCategory_ID = data.get('SubCategory_ID', product.SubCategory_ID)

    # Validate discount percentage
    if product.Discount_Percentage < 0 or product.Discount_Percentage > 100:
        return jsonify({'error': 'Discount_Percentage must be between 0 and 100'}), 400

    db.session.commit()
    return jsonify({'message': 'Product updated successfully'}), 200

#Delete API:
def delete_product(product_id):
    from app import Product, db
    """Delete a product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'}), 200

