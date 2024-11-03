from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thrift_and_thrive.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')  # Define the folder where images will be uploaded
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Define the folder where images will be uploaded

os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the 'uploads' folder if it doesn't exist
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Float, default=0)
    image_filename = db.Column(db.String(100), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/shop')
def shop():
    products = Product.query.all()
    return render_template('shop.html', products=products)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['user_id'] = user.id
        flash("Login successful!", "success")
        # Check if 'next' is valid; if not, default to 'home'
        next_page = request.form.get('next') or url_for('home')
        return redirect(next_page)
    else:
        flash("Invalid email or password!", "error")
        failed_login_redirect = request.form.get('next') or url_for('home')
        return redirect(f"{failed_login_redirect}?login_failed=true")

@app.route('/register', methods=['POST'])
def register():
    email = request.form['reg-email']
    password = request.form['reg-password']
    confirm_password = request.form['confirm-password']

    if password != confirm_password:
        flash("Passwords do not match!", "error")
        # Check if 'next' is valid; if not, default to 'home'
        next_page = request.form.get('next') or url_for('home')
        return redirect(next_page)

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password=hashed_password)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered!", "error")
        # Check if 'next' is valid; if not, default to 'home'
        next_page = request.form.get('next') or url_for('home')
        return redirect(next_page)

    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id  # Log the user in
    flash("Registration successful! You are now logged in.", "success")
    # Check if 'next' is valid; if not, default to 'home'
    next_page = request.form.get('next') or url_for('home')
    return redirect(next_page)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route('/sell', methods=['POST'])
def sell_product():
    if 'user_id' not in session:
        # Redirect to login page or return with an error flash
        flash("You need to be logged in to add items to your cart.", "error")
        return redirect(url_for('shop'))  # Or redirect to the shop page

    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    condition = request.form['condition']
    image = request.files['image']

    if image:
        # Save the image
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Create and save the new product in the database
        new_product = Product(name=name, description=description, 
                              price=price, condition=condition, image_filename=filename)
        db.session.add(new_product)
        db.session.commit()

        flash("Product listed successfully!", "success")
        return redirect(url_for('shop'))

    flash("Failed to list the product. Please try again.", "danger")
    return redirect(url_for('shop'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        # Redirect to login page or return with an error flash
        flash("You need to be logged in to add items to your cart.", "error")
        return redirect(url_for('shop'))  # Or redirect to the shop page

    user_id = session['user_id']
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        # Item is already in the cart, flash an error message
        flash("Item already exists in your cart!", "error")
    else:
        # Item is not in the cart, add it as a new item
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
        flash("Item successfully added to your cart.", "success")
    
    # Redirect to the 'shop' page or another relevant page
    return redirect(url_for('shop'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(request.referrer or url_for('home'))

    user_id = session['user_id']
    # Get all cart items for the user, along with product details
    cart_items = db.session.query(Cart, Product).join(Product, Cart.product_id == Product.id).filter(Cart.user_id == user_id).all()

    # Calculate total items and total price
    total_items = sum(cart_item.quantity for cart_item, product in cart_items)
    total_price = round(sum(cart_item.quantity * product.price for cart_item, product in cart_items), 2)

    # Pass the totals to the template
    return render_template('cart.html', cart_items=cart_items, total_items=total_items, total_price=total_price)

@app.route('/updateitem', methods=['POST'])
def updateitem():
    if 'user_id' not in session:
        flash("Please log in to manage your cart.", "error")
        return redirect(url_for('cart'))  # Redirect to login page if not logged in

    product_id = request.form.get('product_id')
    action = request.form.get('action')
    user_id = session.get('user_id')

    if action == "remove":
        # Remove the item from the cart
        Cart.query.filter_by(user_id=user_id, product_id=product_id).delete()
        db.session.commit()
        flash("Item removed from your cart.", "success")
    
    elif action == "update":
        # Update the quantity of the item in the cart
        quantity = request.form.get('quantity', type=int)
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity = quantity
            db.session.commit()
            flash("Cart updated successfully.", "success")
    
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash("Please log in to checkout.", "error")
        return redirect(url_for('home'))

    user_id = session['user_id']
    cart_items = db.session.query(Cart, Product).join(Product, Cart.product_id == Product.id).filter(Cart.user_id == user_id).all()
    return render_template('checkout.html', cart_items=cart_items)

@app.context_processor
def cart_count_processor():
    cart_count = 0
    if 'user_id' in session:
        cart_count = Cart.query.filter_by(user_id=session['user_id']).count()
    return dict(cart_count=cart_count)

@app.after_request
def add_cache_control_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/add_sample_products')
def add_sample_products():
    # Define a list of sample products with varying details
    sample_products = [
        {"name": "Vintage Jacket", "price": 29.99, "image_url": "https://via.placeholder.com/150", "description": "A stylish vintage jacket."},
        {"name": "Classic Watch", "price": 89.99, "image_url": "https://via.placeholder.com/150", "description": "Timeless elegance."},
        {"name": "Retro Sneakers", "price": 49.99, "image_url": "https://via.placeholder.com/150", "description": "Comfortable and stylish retro sneakers."},
        {"name": "Leather Wallet", "price": 19.99, "image_url": "https://via.placeholder.com/150", "description": "A sleek, durable leather wallet."},
        {"name": "Denim Backpack", "price": 39.99, "image_url": "https://via.placeholder.com/150", "description": "Casual and versatile denim backpack."},
        {"name": "Minimalist Necklace", "price": 15.99, "image_url": "https://via.placeholder.com/150", "description": "Elegant necklace with a minimalist design."},
        {"name": "Bluetooth Earbuds", "price": 59.99, "image_url": "https://via.placeholder.com/150", "description": "High-quality wireless earbuds for music on the go."}
    ]

    # Randomly select 3 to 5 products from the sample_products list
    num_products_to_add = random.randint(3, 5)
    products_to_add = random.sample(sample_products, num_products_to_add)

    # Create Product instances and add them to the database
    new_products = [Product(name=product["name"], price=product["price"], image_url=product["image_url"], description=product["description"]) for product in products_to_add]
    
    db.session.add_all(new_products)
    db.session.commit()

    return jsonify({"message": f"{num_products_to_add} sample products added!", "products": [product["name"] for product in products_to_add]})

@app.route('/delete_all_products')
def delete_all_products():
    try:
        # Delete all entries from the Product table
        num_deleted = Product.query.delete()
        db.session.commit()
        
        return jsonify({"message": f"Successfully deleted {num_deleted} products from the database."})
    except Exception as e:
        db.session.rollback()  # Roll back in case of an error
        return jsonify({"error": "Failed to delete products", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)