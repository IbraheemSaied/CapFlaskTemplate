from app import app
from flask import render_template, flash, redirect, url_for
from flask_login import current_user

# This is for rendering the home page
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('msgsList'))
    else:
        return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/messages')
def messages(): 
    return render_template('messages.html')
