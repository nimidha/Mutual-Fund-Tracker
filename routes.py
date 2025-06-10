# inside app.py or routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3

main = Blueprint('main', __name__)

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        print("✅ Login form submitted")  # Debug message
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result and password == result[0]:
            session['username'] = username
            return redirect(url_for('main.home'))  # make sure this matches your home route
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)
