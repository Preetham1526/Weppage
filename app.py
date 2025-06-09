from flask import Flask, render_template, request, jsonify, redirect, session
from flask_pymongo import PyMongo
import psycopg2
import sqlite3
import os
import random
import traceback
import datetime
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")

# ---------- MongoDB (for subscriptions) ----------
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/subscriptions")
mongo = PyMongo(app)

# ---------- PostgreSQL (Render deployment) ----------
USE_POSTGRES = os.getenv("dpg-d0mmolbuibrs73er6ju0-a", "False").lower() == "true"


#USE_POSTGRES = bool(os.getenv("postgresql://webpage_postgre_user:q2xDdUb6bPsdsZYSr2MUQYm5N6K3dy3P@dpg-d0mmolbuibrs73er6ju0-a/webpage_postgre"))

if not os.path.exists('users.db'):
    import init_db


def get_db_conn():
    if USE_POSTGRES:
        return psycopg2.connect(
            host="dpg-d0mmolbuibrs73er6ju0-a",
            database="webpage_postgre",
            user="webpage_postgre_user",
            password="q2xDdUb6bPsdsZYSr2MUQYm5N6K3dy3P"
        )
    else:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn

    

# ---------- Email OTP Utility ----------
EMAIL_USER = os.getenv("EMAIL_USER", "youremail@example.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "yourpassword")

def send_email(to, subject, content):
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())

# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/home_login")
def home_login():
    if "user" not in session:
        return redirect("/login")
    return render_template("home.html", user=session["user"])


@app.route('/signup_method', methods=["POST"])
def signup_method():
    data = request.get_json()
    username = data.get('username')
    full_name = data.get('full_name')
    email = data.get('email')
    password = generate_password_hash(data.get('password'))  # secure
    phone = data.get('phone')

    conn = get_db_conn()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("""
        SELECT id FROM users WHERE email = %s
    """ if USE_POSTGRES else """
        SELECT id FROM users WHERE email = ?
    """, (email,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({"message": "Email already registered"}), 400

    try:
        cursor.execute("""
            INSERT INTO users (username, full_name, email, password, phone)
            VALUES (%s, %s, %s, %s, %s)
        """ if USE_POSTGRES else """
            INSERT INTO users (username, full_name, email, password, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (username, full_name, email, password, phone))
        conn.commit()
        return jsonify({"message": "Registration successful"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "Registration failed"}), 500
    finally:
        conn.close()


@app.route('/login_method', methods=["POST"])
def login_method():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE email = %s
    """ if USE_POSTGRES else """
        SELECT * FROM users WHERE email = ?
    """, (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[4] if USE_POSTGRES else user["password"], password):
        session['user_id'] = user[0] if USE_POSTGRES else user["id"]
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401


@app.route('/logout_method')
def logout_method():
    session.clear()
    return jsonify({"message": "Logged out"})

# ---------- Forgot Password ----------
@app.route('/forgot_password_method', methods=['POST'])
def forgot_password_method():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO otp_tokens (email, otp, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO UPDATE SET otp = EXCLUDED.otp, created_at = EXCLUDED.created_at
        """ if USE_POSTGRES else """
            REPLACE INTO otp_tokens (email, otp, created_at) VALUES (?, ?, datetime('now'))
        """, (email, otp))
        conn.commit()

    send_email(email, "Password Reset OTP", f"Your OTP is: {otp}")
    return redirect('/verify-otp')

@app.route('/verify_ot_method', methods=['POST'])
def verify_otp_method():
    email = request.form['email']
    user_otp = request.form['otp']
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT otp FROM otp_tokens WHERE email = %s
        """ if USE_POSTGRES else """
            SELECT otp FROM otp_tokens WHERE email = ?
        """, (email,))
        row = cursor.fetchone()

    if row and row[0] == user_otp:
        return redirect(f"/reset-password?email={email}")
    else:
        return "Invalid OTP"

@app.route('/reset_password_method', methods=['POST'])
def reset_password_method():
    email = request.args.get("email")
    new_password = request.form["new_password"]
    confirm = request.form["confirm_password"]

    if new_password != confirm:
        return "Passwords do not match"

    hashed = generate_password_hash(new_password)
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET password = %s WHERE email = %s
        """ if USE_POSTGRES else """
            UPDATE users SET password = ? WHERE email = ?
        """, (hashed, email))
        conn.commit()

    return redirect('/login')

# ---------- Subscription (MongoDB) ----------
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 403
    data = request.get_json()
    session["cart"] = data
    return jsonify({"message": "Plan added to cart"})

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session or "cart" not in session:
        return jsonify({"error": "Login and cart required"}), 403

    cart = session["cart"]
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(days=30)
    payment_method = request.json.get("payment_method", "unknown")

    mongo.db.orders.insert_one({
        "user_id": session["user_id"],
        "plan": cart["plan"],
        "price": cart["price"],
        "start": start,
        "end": end,
        "payment_method": payment_method
    })

    return jsonify({
        "message": "Subscription successful!",
        "start": start.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
        "plan": cart["plan"]
    })

@app.route("/admin/subscriptions", methods=["GET"])
def view_subscriptions():
    return jsonify(list(mongo.db.orders.find({}, {"_id": 0})))

# ---------- Static Pages ----------
@app.route('/appointments')
def appointment(): return render_template('appointments.html')

@app.route('/careers')
def careers(): return render_template('careers.html')

@app.route('/discussion')
def discussion(): return render_template('discussions.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

@app.route('/fg_password')
def fg_password(): return render_template('forgot_password.html')

@app.route('/insurance')
def insurance(): return render_template('insurance.html')

@app.route('/subscription')
def subscription(): return render_template('subscription.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
