from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)  # URL for the product image
    description = db.Column(db.Text, nullable=True)

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
    cart_count = 0
    if 'user_id' in session:
        cart_count = Cart.query.filter_by(user_id=session['user_id']).count()
    return render_template('shop.html', products=products, cart_count=cart_count)

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
        return redirect(url_for('home'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password=hashed_password)

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered!", "error")
        return redirect(url_for('home'))

    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id  # Log the user in
    flash("Registration successful! You are now logged in.", "success")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

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
        return redirect(url_for('home'))
    
    user_id = session['user_id']
    cart_items = db.session.query(Cart, Product).join(Product, Cart.product_id == Product.id).filter(Cart.user_id == user_id).all()
    return render_template('cart.html', cart_items=cart_items)


@app.route('/add_sample_products')
def add_sample_products():
    product1 = Product(name="Vintage Jacket", price=29.99, image_url="https://via.placeholder.com/150", description="A stylish vintage jacket.")
    product2 = Product(name="Classic Watch", price=89.99, image_url="https://via.placeholder.com/150", description="Timeless elegance.")
    
    db.session.add_all([product1, product2])
    db.session.commit()
    return "Sample products added!"

if __name__ == '__main__':
    app.run(debug=True)