from flask import Flask, request, redirect, render_template_string
import mysql.connector

app = Flask(__name__)

# ---------------------- DATABASE CONNECTION ----------------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="voting_db"
    )

# ---------------------- HOME PAGE ----------------------
@app.route('/')
def home():
    return render_template_string("""
        <h1>Online Voting System</h1>
        <a href="/create">Create Tables</a><br><br>

        <a href="/voter_register">Register Voter</a><br>
        <a href="/voter_login">Voter Login</a><br>
        <a href="/admin_login">Admin Login</a><br><br>

        <h3>Debug / Show Tables</h3>
        <a href='/show_voters'>Show Voters</a><br>
        <a href='/show_candidates'>Show Candidates</a><br>
        <a href='/show_votes'>Show Votes</a><br>
        <a href='/show_admin'>Show Admin</a><br>
    """)

# ---------------------- CREATE TABLES ----------------------
@app.route("/create")
def create_tables():
    db = get_db()
    cur = db.cursor()

    # Create voters table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS voters (
        voter_id INT PRIMARY KEY AUTO_INCREMENT,
        votername VARCHAR(100) UNIQUE,
        password VARCHAR(100),
        email VARCHAR(100),
        has_voted BOOLEAN DEFAULT FALSE
    );
    """)

    # Create candidates table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        candidate_id INT PRIMARY KEY AUTO_INCREMENT,
        candidate_name VARCHAR(100),
        party VARCHAR(100)
    );
    """)

    # Create votes table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        vote_id INT PRIMARY KEY AUTO_INCREMENT,
        voter_id INT,
        candidate_id INT,
        vote_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
        FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
    );
    """)

    # Create admin table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        admin_id INT PRIMARY KEY AUTO_INCREMENT,
        admin_name VARCHAR(100),
        password VARCHAR(100)
    );
    """)

    # Insert sample admin if not exists
    cur.execute("INSERT IGNORE INTO admin (admin_name, password) VALUES ('admin1','admin123')")

    # Insert ONE sample candidate (no duplicates)
    cur.execute("INSERT IGNORE INTO candidates (candidate_name, party) VALUES ('Amit Sharma','Party A')")

    db.commit()
    db.close()

    return "<h3>Tables Created & Sample Data Inserted ✔</h3><a href='/'>Go Home</a>"

# ---------------------- SHOW TABLES ----------------------
@app.route("/show_voters")
def show_voters():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM voters")
    data = cur.fetchall()
    db.close()

    html = "<h2>Voters Table</h2><table border='1'>"
    html += "<tr><th>ID</th><th>Name</th><th>Password</th><th>Email</th><th>Has Voted</th></tr>"
    for row in data:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    html += "</table><br><a href='/'>Go Home</a>"
    return html

@app.route("/show_candidates")
def show_candidates():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM candidates")
    data = cur.fetchall()
    db.close()

    html = "<h2>Candidates Table</h2><table border='1'>"
    html += "<tr><th>ID</th><th>Name</th><th>Party</th></tr>"
    for row in data:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
    html += "</table><br><a href='/'>Go Home</a>"
    return html

@app.route("/show_votes")
def show_votes():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM votes")
    data = cur.fetchall()
    db.close()

    html = "<h2>Votes Table</h2><table border='1'>"
    html += "<tr><th>Vote ID</th><th>Voter ID</th><th>Candidate ID</th><th>Vote Time</th></tr>"
    for row in data:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
    html += "</table><br><a href='/'>Go Home</a>"
    return html

@app.route("/show_admin")
def show_admin():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM admin")
    data = cur.fetchall()
    db.close()

    html = "<h2>Admin Table</h2><table border='1'>"
    html += "<tr><th>ID</th><th>Name</th><th>Password</th></tr>"
    for row in data:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
    html += "</table><br><a href='/'>Go Home</a>"
    return html

# ---------------------- VOTER REGISTER ----------------------
@app.route('/voter_register', methods=['GET', 'POST'])
def voter_register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO voters (votername, password, email) VALUES (%s, %s, %s)", 
                       (name, password, email))
        db.commit()
        return "<h3>Voter Registered Successfully!</h3>"

    return render_template_string("""
        <h2>Voter Registration</h2>
        <form method="POST">
            Name: <input type="text" name="name"><br><br>
            Password: <input type="password" name="password"><br><br>
            Email: <input type="email" name="email"><br><br>
            <button type="submit">Register</button>
        </form>
    """)

# ---------------------- VOTER LOGIN ----------------------
@app.route('/voter_login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT voter_id FROM voters WHERE votername=%s AND password=%s", 
                       (name, password))
        voter = cursor.fetchone()

        if voter:
            return redirect(f"/vote/{voter[0]}")
        else:
            return "<h3>Invalid Login!</h3>"

    return render_template_string("""
        <h2>Voter Login</h2>
        <form method="POST">
            Name: <input type="text" name="name"><br><br>
            Password: <input type="password" name="password"><br><br>
            <button type="submit">Login</button>
        </form>
    """)

# ---------------------- VOTING PAGE ----------------------
@app.route('/vote/<int:voter_id>', methods=['GET', 'POST'])
def vote(voter_id):
    db = get_db()
    cursor = db.cursor()

    # Select all candidates
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    if request.method == 'POST':
        candidate_id = request.form['candidate']

        cursor.execute("INSERT INTO votes (voter_id, candidate_id) VALUES (%s, %s)", 
                       (voter_id, candidate_id))

        cursor.execute("UPDATE voters SET has_voted = TRUE WHERE voter_id=%s", (voter_id,))
        db.commit()
        return "<h3>Vote Submitted Successfully!</h3>"

    html = "<h2>Vote for Your Candidate</h2><form method='POST'>"
    for c in candidates:
        html += f'<input type="radio" name="candidate" value="{c[0]}"> {c[1]} ({c[2]}) <br>'
    html += "<br><button type='submit'>Submit Vote</button></form>"
    return render_template_string(html)

# ---------------------- ADMIN LOGIN ----------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT admin_id FROM admin WHERE admin_name=%s AND password=%s",
                       (name, password))
        admin = cursor.fetchone()

        if admin:
            return redirect("/admin_dashboard")
        else:
            return "<h3>Invalid Admin Login!</h3>"

    return render_template_string("""
        <h2>Admin Login</h2>
        <form method="POST">
            Name: <input type="text" name="name"><br><br>
            Password: <input type="password" name="password"><br><br>
            <button type="submit">Login</button>
        </form>
    """)

# ---------------------- ADMIN DASHBOARD ----------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT candidate_name, COUNT(vote_id)
        FROM candidates LEFT JOIN votes ON candidates.candidate_id = votes.candidate_id
        GROUP BY candidates.candidate_id
    """)
    results = cursor.fetchall()

    html = "<h2>Voting Results</h2>"
    for r in results:
        html += f"{r[0]} → {r[1]} votes<br>"

    return render_template_string(html)

# ---------------------- RUN APP ----------------------
if __name__ == '__main__':
    app.run(debug=True)

