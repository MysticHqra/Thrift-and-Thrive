from flask import Flask, render_template, request, redirect, url_for, flash, session
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
    # You can add logic to fetch and display items for sale here
    return render_template('shop.html')

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
        return redirect(url_for('home'))
    else:
        flash("Invalid email or password!", "error")
        return redirect(url_for('home'))

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

if __name__ == '__main__':
    app.run(debug=True)