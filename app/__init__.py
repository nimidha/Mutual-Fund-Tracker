from flask import Flask, flash, session, request, render_template, redirect, url_for
import sqlite3
from flask import Response, jsonify
import csv,sys, io
from app.utils import get_mutual_fund_names
from collections import defaultdict
from datetime import datetime

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
        

        # # Chart Data - show each fund individually
        fund_names = [fund['fund_name'] for fund in funds]
        amounts = [fund['amount'] for fund in funds]
       

        #summary stats
        total_entries = len(funds)
        total_amount = sum(fund['amount'] for fund in funds)
         


          # Prepare data for chart: Group by fund_name
        fund_totals = defaultdict(float)
        for fund in funds:
           fund_totals[fund['fund_name']] += fund['amount']

        fund_labels = list(fund_totals.keys())
        fund_amounts = list(fund_totals.values())

        fund_options = get_mutual_fund_names()

        return render_template('dashboard.html',
        username=username,
        funds=funds,
        total_entries=total_entries,
        total_amount=total_amount,
        fund_labels=fund_labels,              # ✅ Add this
        fund_amounts=fund_amounts ,
        fund_options=fund_options)
    


    @app.route('/investments')
    def show_investments():
        if 'username' not in session:
            return redirect(url_for('login'))
        conn = get_db_connection()
        username = session['username']
        funds = conn.execute('SELECT * FROM funds WHERE username = ?', (username,)).fetchall()
        conn.close()
        return render_template('investments.html', funds=funds, username=username )


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
        with get_db_connection() as conn:
            cursor=conn.cursor()

            cursor.execute("DELETE FROM funds WHERE username = ? AND id = ?",(username,fund_id))
            conn.commit()
        
        return redirect(url_for('dashboard'))
    



    @app.route('/export_csv')
    def export_csv():
        if 'username' not in session:
            return redirect(url_for('login'))
        
        username = session['username']
        print(f"Session username: {username}", file=sys.stdout)
        conn = get_db_connection()
        cursor = conn.execute('SELECT fund_name, amount, date FROM funds WHERE username =?', (username,))
        funds = cursor.fetchall()
        conn.close()
        print(f"Fetched rows: {len(funds)}", file=sys.stdout)     # 🔍 Number of rows
        print(f"Rows: {funds}", file=sys.stdout)   

        def generate():
            data = io.StringIO()
            writer = csv.writer(data)

            #HEADER
            writer.writerow(('Fund Name', 'Amount Invested', 'Date'))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)


            #data rows
            for row in funds:
                writer.writerow((row['fund_name'], row['amount'], row['date']))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)

        headers = {
        'Content-Disposition': 'attachment; filename="investments.csv"',
        'Content-Type': 'text/csv',
        }
        

        return Response(generate(), headers=headers)
    



    @app.route('/upload_csv', methods=['POST'])
    def upload_csv():
        if 'username' not in session:
            redirect(url_for('login'))


        file = request.files.get('file')
        if not file or file.filename=='':
            return "No file selected", 400
        

        username = session['username']
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_input = csv.reader(stream)

        #Skip header

        next(csv_input)

        conn=get_db_connection()
        cursor = conn.cursor()

        try:
            for row in csv_input:
                fund_name, amount, date=row
                cursor.execute(
                    'INSERT INTO funds (fund_name, amount,date, username) VALUES (?,?,?,?)',
                    (fund_name.strip(), float(amount), date.strip(), username)

                )
                conn.commit()
                message = "Investments upload successfully!"
        except Exception as e:
            conn.rollback()
            message =f"Error uploadimg: {e}"

        finally:
            conn.close()

        return redirect(url_for('show_investments'))
    
   

    @app.route('/api/investments', methods=['GET'])
    def api_get_investmnets():
        if 'username' not in session:
            return jsonify({'error':'Unauthorized'}), 401
        

        username = session['username']
        conn = get_db_connection()
        cursor = conn.execute('SELECT id, fund_name, amount, date FROM funds WHERE username = ?', (username,))
        investments = cursor.fetchall()
        conn.close()


        #convert row objects to python dictionaries
        investment_list =[]
        for row in investments:
            investment_list.append({
                'id': row['id'],
                'fund_name': row['fund_name'],
                'amount':row['amount'],
                'date': row['date']
            })

        return jsonify({'investmnets': investment_list})

    @app.route('/api/investments', methods=['POST'])
    def api_add_investments():
        if 'username' not in session:
            return jsonify({'error':'Unauthorized'}), 401


        username= session['nimidhag']

        #parse json input
        data = request.get_json()

        #validate required field
        required_fields = ['fund_name', 'amount', 'date']
        if not all (field in data for field in required_fields):
            return jsonify({'error': 'Missing field in request'}) , 400
        

        #Extract and sanitize values 
        fund_name = data['fund_name'].strip()
        try:
            amount = float(data['amount'])
        except ValueError:
            return jsonify({'error': 'Amount must be a number'}), 400
        date= data['date'].strip()

        #insert into db

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO funds (fund_name, amount, date, username) VALUES (?,?,?,?)',
                (fund_name, amount, date ,username)
            )
            conn.commit()
            conn.close()
            return jsonify({'message': 'Investmnet added successfully'}), 201
        except Exception as e:
            return jsonify({'error': f'Database error: {e}'}), 500

    @app.route('/api/investments/<int:fund_id>', methods=['PUT'])
    def api_put_investments(fund_id):
        if 'username' not in session:
            return jsonify({'error':'Unauthorized'}),401
        
        username = session['username']
        data=request.get_json()


        required_fields = ['fund_name', 'amount', 'date']
        if not all (field in data for field in required_fields):
            return jsonify({'error':'Missing field in request'}), 400
        

        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE funds SET fund_name =?,amount=?, date=? WHERE id =? AND username=?',
                (data['fund_name'], float(data['amount']), data['date'], fund_id,username)
            )
            conn.commit()
            conn.close()
            return jsonify({'message': 'Investment updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Database error: {e}'}), 500

      
    @app.route('/api/investments/<int:fund_id>', methods=['DELETE'])
    def delete_investment(fund_id):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        username = session['username']

        try:
            conn = get_db_connection()
            conn.execute(
            'DELETE FROM funds WHERE id=? AND username=?',
            (fund_id, username)
        )
            conn.commit()
            conn.close()
        
            return jsonify({'message': 'Investment deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Database error: {e}'}), 500



    

        


    return app


  

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
