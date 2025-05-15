from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3


app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            course TEXT,
            birthdate TEXT,
            mobile_no TEXT,
            address TEXT,
            gender TEXT,
            age INTEGER
        )
    ''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']


        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'danger')
        finally:
            conn.close()
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']


        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()


        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash('Welcome, {}!'.format(user[1]), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials!', 'danger')
    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash('If this email exists, password reset instructions have been sent.', 'info')
    return render_template('forgot_password.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))


    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()


    # Total applicants
    cursor.execute('SELECT COUNT(*) FROM applicants')
    total_applicants = cursor.fetchone()[0]


    # List of all programs
    programs = ['BSIE', 'BSIT', 'BSCS', 'BIT', 'BSICE', 'BSCPE']


    program_counts = []
    approval_rates = []
    approved_per_program = []
    pending_per_program = []


    for program in programs:
        # Total per program
        cursor.execute('SELECT COUNT(*) FROM applicants WHERE course = ?', (program,))
        total = cursor.fetchone()[0]
        program_counts.append(total)


        # Approved count
        cursor.execute('SELECT COUNT(*) FROM applicants WHERE course = ? AND status = "Approved"', (program,))
        approved = cursor.fetchone()[0]


        # Pending count
        cursor.execute('SELECT COUNT(*) FROM applicants WHERE course = ? AND status = "Pending"', (program,))
        pending = cursor.fetchone()[0]


        approved_per_program.append(approved)
        pending_per_program.append(pending)


        # Calculate approval rate
        rate = (approved / total * 100) if total > 0 else 0
        approval_rates.append(round(rate, 2))


    # Top 3 programs with most applicants
    cursor.execute('''
        SELECT course, COUNT(*) as total
        FROM applicants
        GROUP BY course
        ORDER BY total DESC
        LIMIT 3
    ''')
    top_programs = cursor.fetchall()


    conn.close()


    return render_template('dashboard.html',
                           total=total_applicants,
                           program_labels=programs,
                           program_data=program_counts,
                           approval_rates=approval_rates,
                           approved_per_program=approved_per_program,
                           pending_per_program=pending_per_program,
                           top_programs=top_programs)
   
@app.route('/sync-form-data')
def sync_form_data():
    import requests, csv
    from io import StringIO
    from datetime import datetime, date
    import sqlite3


    def calculate_age(birthdate_str):
        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


    csv_url = 'https://docs.google.com/spreadsheets/d/e/YOUR_CSV_LINK/pub?output=csv'
    response = requests.get(csv_url)


    if response.status_code != 200:
        return "Failed to fetch CSV data", 500


    f = StringIO(response.text)
    reader = csv.DictReader(f)


    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()


    for row in reader:
        try:
            first_name = row['First Name']
            middle_name = row['Middle Name']
            last_name = row['Last Name']
            course = row['Course']
            birthdate = row['Birthdate']
            mobile_no = row['Mobile No']
            address = row['Address']
            gender = row['Gender']
            status = row['Status']
            age = calculate_age(birthdate)


            cursor.execute('''
                INSERT INTO applicants (first_name, middle_name, last_name, course, birthdate, mobile_no, address, gender, age, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (first_name, middle_name, last_name, course, birthdate, mobile_no, address, gender, age, status))
        except Exception as e:
            print(f"Skipping row due to error: {e}")


    conn.commit()
    conn.close()
    return "Applicant data synced successfully"


@app.route('/applicants')
def applicant_list():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM applicants')
    applicants = cursor.fetchall()
    conn.close()
    return render_template('applicant_list.html', applicants=applicants)


@app.route('/add-applicant', methods=['GET', 'POST'])
def add_applicant():
    if 'user_id' not in session:
        return redirect(url_for('login'))


    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        course = request.form['course']
        birthdate = request.form['birthdate']
        mobile_no = request.form['mobile_no']
        address = request.form['address']
        gender = request.form['gender']
        age = request.form['age']
        status = request.form['status']  # <-- NEW


        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applicants (first_name, middle_name, last_name, course, birthdate, mobile_no, address, gender, age, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, middle_name, last_name, course, birthdate, mobile_no, address, gender, age, status))
        conn.commit()
        conn.close()


        flash('Applicant added successfully!', 'success')
        return redirect(url_for('applicant_list'))


    return render_template('add_applicant.html')


@app.route('/edit-applicant/<int:id>', methods=['GET', 'POST'])
def edit_applicant(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))


    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()


    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        course = request.form['course']
        birthdate = request.form['birthdate']
        mobile_no = request.form['mobile_no']
        address = request.form['address']
        gender = request.form['gender']
        age = request.form['age']
        status = request.form['status']  # make sure this exists in the form!


        cursor.execute('''
            UPDATE applicants
            SET first_name = ?, middle_name = ?, last_name = ?, course = ?, birthdate = ?, mobile_no = ?, address = ?, gender = ?, age = ?, status = ?
            WHERE id = ?
        ''', (first_name, middle_name, last_name, course, birthdate, mobile_no, address, gender, age, status, id))


        conn.commit()
        conn.close()
        flash('Applicant updated successfully!', 'success')
        return redirect(url_for('applicant_list'))


    # Get applicant data to pre-fill form
    cursor.execute('SELECT * FROM applicants WHERE id = ?', (id,))
    applicant = cursor.fetchone()
    conn.close()
    return render_template('edit_applicant.html', applicant=applicant)


@app.route('/delete-applicant/<int:id>')
def delete_applicant(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))


    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM applicants WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Applicant deleted successfully!', 'success')
    return redirect(url_for('applicant_list'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
