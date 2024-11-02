from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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
    # Add login logic here
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    email = request.form['reg-email']
    password = request.form['reg-password']
    confirm_password = request.form['confirm-password']
    # Add registration logic here
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)