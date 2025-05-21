# Complete integrated `app.py` with all required functionality including:
# - User registration/login/logout
# - Forgot password, OTP, reset
# - Subscription (MongoDB)
# - Career + Discussion (SQLite)
# - Email sending

from flask import Flask, render_template, request, jsonify, redirect, session
from flask_pymongo import PyMongo
import sqlite3
import random
import datetime
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"
app.config["MONGO_URI"] = "mongodb://localhost:27017/subscriptions"
mongo = PyMongo(app)

# ---------- Utility: Email OTP ----------
def send_email(to, subject, content):
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = "youremail@example.com"
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("youremail@example.com", "yourpassword")
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template("home.html")




@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    email = data["email"]
    password = data["password"]

    with sqlite3.connect("database.db") as conn:
        cursor = conn.execute("SELECT password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    if user and check_password_hash(user[0], password):
        session["user_id"] = email
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"})

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    hashed = generate_password_hash(data["password"])

    with sqlite3.connect("database.db") as conn:
        try:
            conn.execute('''INSERT INTO users (username, email, phone, country, state, password)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (data["username"], data["email"], data["phone"],
                            data["country"], data["state"], hashed))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "Email already registered"}), 400
    return jsonify({"message": "Signup successful"})

# ---------- Forgot/Reset Password with OTP ----------
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))

    with sqlite3.connect('database.db') as conn:
        conn.execute("REPLACE INTO otp_tokens (email, otp, created_at) VALUES (?, ?, datetime('now'))", (email, otp))
        conn.commit()

    send_email(email, "Password Reset OTP", f"Your OTP is: {otp}")
    return redirect('/verify-otp')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.form['email']
    user_otp = request.form['otp']

    with sqlite3.connect('database.db') as conn:
        cursor = conn.execute("SELECT otp FROM otp_tokens WHERE email = ?", (email,))
        row = cursor.fetchone()

    if row and row[0] == user_otp:
        return redirect(f"/new-password?email={email}")
    else:
        return "Invalid OTP"

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.args.get("email")
    new_password = request.form["new_password"]
    confirm = request.form["confirm_password"]

    if new_password != confirm:
        return "Passwords do not match"

    hashed = generate_password_hash(new_password)

    with sqlite3.connect("database.db") as conn:
        conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed, email))
        conn.commit()

    return redirect('/login')

# ---------- Subscription ----------
@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 403
    data = request.get_json()
    session["cart"] = data
    return jsonify({"message": "Plan added to cart"})

@app.route("/apply-coupon", methods=["POST"])
def apply_coupon():
    data = request.get_json()
    if data["coupon"] == "SAVE10":
        return jsonify({"message": "Coupon applied! 10% off"})
    return jsonify({"error": "Invalid coupon"})

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session or "cart" not in session:
        return jsonify({"error": "Login and plan selection required"}), 403

    cart = session["cart"]
    user_id = session["user_id"]
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(days=30)
    payment_method = request.json.get("payment_method", "unknown")

    order = {
        "user_id": user_id,
        "plan": cart["plan"],
        "price": cart["price"],
        "start": start,
        "end": end,
        "payment_method": payment_method
    }

    mongo.db.orders.insert_one(order)

    return jsonify({
        "message": "Subscription successful!",
        "start": start.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
        "purchased_plan": cart["plan"]
    })

@app.route("/admin/subscriptions", methods=["GET"])
def view_subscriptions():
    orders = list(mongo.db.orders.find({}, {"_id": 0}))
    return jsonify(orders)

# ---------- Careers ----------
@app.route("/careers", methods=["GET", "POST"])
def careers():
    if request.method == "POST":
        data = request.get_json()
        with sqlite3.connect("database.db") as conn:
            conn.execute('''INSERT INTO careers (user_email, title, skills, experience)
                            VALUES (?, ?, ?, ?)''',
                            (session["user_id"], data["title"], data["skills"], data["experience"]))
            conn.commit()
        return jsonify({"message": "Career posted successfully"})
    else:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.execute("SELECT * FROM careers WHERE approved = 1")
            careers = cursor.fetchall()
        return jsonify(careers)

@app.route("/career-edit/<int:id>", methods=["PUT"])
def edit_career(id):
    data = request.get_json()
    with sqlite3.connect("database.db") as conn:
        conn.execute("UPDATE careers SET title = ?, skills = ?, experience = ? WHERE id = ? AND user_email = ?",
                     (data["title"], data["skills"], data["experience"], id, session["user_id"]))
        conn.commit()
    return jsonify({"message": "Career updated"})

@app.route("/career-delete/<int:id>", methods=["DELETE"])
def delete_career(id):
    with sqlite3.connect("database.db") as conn:
        conn.execute("DELETE FROM careers WHERE id = ? AND user_email = ?", (id, session["user_id"]))
        conn.commit()
    return jsonify({"message": "Career deleted"})

# ---------- Discussions ----------
@app.route("/discussions", methods=["GET", "POST"])
def discussions():
    if request.method == "POST":
        data = request.get_json()
        now = datetime.datetime.utcnow().isoformat()
        with sqlite3.connect("database.db") as conn:
            conn.execute("INSERT INTO discussions (user_email, title, message, parent_id, created_at) VALUES (?, ?, ?, ?, ?)",
                         (session["user_id"], data["title"], data["message"], data.get("parent_id"), now))
            conn.commit()
        return jsonify({"message": "Posted successfully"})
    else:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.execute("SELECT * FROM discussions ORDER BY created_at DESC")
            all_discussions = cursor.fetchall()
        return jsonify(all_discussions)

@app.route("/discussion-delete/<int:id>", methods=["DELETE"])
def delete_discussion(id):
    with sqlite3.connect("database.db") as conn:
        conn.execute("DELETE FROM discussions WHERE id = ? AND user_email = ?", (id, session["user_id"]))
        conn.commit()
    return jsonify({"message": "Deleted successfully"})

if __name__ == "__main__":
    app.run(debug=True)

