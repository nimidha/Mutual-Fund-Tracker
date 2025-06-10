from flask import Flask, flash, session, request, render_template, redirect, url_for
import sqlite3

def create_app():
    app = Flask(__name__)
    app.secret_key = "mykey1234"
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Helper: Connect to DB
    def get_db_connection():
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        return conn

    # Create required tables at app startup
    with app.app_context():
        conn = get_db_connection()

        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS funds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_name TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                username TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    # Home route: Redirect to dashboard if logged in, else to login
    @app.route('/')
    def home():
        if 'username' in session:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login'))

    # Register
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = None
        success = None
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                error = 'Passwords do not match.'
            elif len(password) < 4:
                error = 'Password must be at least 4 characters.'
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
                existing_user = cursor.fetchone()

                if existing_user:
                    error = 'Username or email already exists.'
                else:
                    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                   (username, email, password))
                    conn.commit()
                    success = 'Registration successful! You can now log in.'
                conn.close()
        return render_template('register.html', error=error, success=success)

    # Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()

            if result is None:
                error = "Invalid username or password"
            else:
                stored_password = result['password']
                if password == stored_password:
                    session['username'] = username
                    return redirect(url_for('dashboard'))
                else:
                    error = "Invalid username or password"
        return render_template('login.html', error=error)

    # Logout
    @app.route('/logout')
    def logout():
        session.pop('username', None)
        return redirect(url_for('login'))

    # Dashboard: Add/View Funds
    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard():
        if 'username' not in session:
            return redirect(url_for('login'))

        username = session['username']
    

        if request.method == 'POST':
            fund_name = request.form['fund_name']
            amount =float( request.form['amount'])
            date = request.form['date']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO funds (fund_name, amount, date, username) VALUES (?, ?, ?, ?)",
                (fund_name, amount, date, username)
            )
            conn.commit()
            conn.close()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funds WHERE username = ?", (username,))
        funds = cursor.fetchall()
        conn.close()
        

        #Chart data
        fund_names = [fund['fund_name'] for fund in funds]
        amounts = [fund ['amount'] for fund in funds]

        #summary stats
        total_entries = len(funds)
        total_amount = sum(amounts)

       

        return render_template('dashboard.html', username=username, funds=funds, total_entries=total_entries, total_amount=total_amount, fund_names=fund_names, amounts=amounts)


    @app.route('/edit_fund/<int:fund_id>', methods=['GET','POST'])
    def edit_fund(fund_id):
        if 'username' not in session:
            redirect(url_for('login'))

        username =session['username']
        conn =get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funds WHERE id = ? AND username = ?", (fund_id,username))
        fund = cursor.fetchone()

        if not fund:
            conn.close()
            return "Fund not Found.",404
        
        if request.method == "POST":
            fund_name = request.form['fund_name']
            amount = request.form['amount']
            date = request.form['date']


            cursor.execute(
                "UPDATE funds SET fund_name =?, amount = ?, date =? WHERE id =? AND username =?",
                (fund_name,amount,date,fund_id,username)
            )

            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        
        conn.close()
        return render_template('edit_funds.html',fund=fund)


    @app.route('/delete_fund/<int:fund_id>')
    def delete_fund(fund_id):
        if 'username' not in session:
            redirect(url_for('login'))

        username=session['username']
        conn=get_db_connection()
        cursor=conn.cursor()

        cursor.execute("DELETE FROM funds WHERE username = ? AND id = ?",(username,fund_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
