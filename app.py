from flask import Flask, render_template, request, redirect, url_for, session
import requests
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = "8442421660:AAFQegysS7Pq5Yp0huu_R42e8W6QjpxyVBM"
CHAT_ID = "7489169342"

ADMIN_PASS = "admin123"
USER_PASS = "user123"
SECURITY_ANSWER = "mothername"

# ==========================
# TELEGRAM FUNCTION
# ==========================

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

# ==========================
# INCIDENT GENERATOR
# ==========================

def generate_incident(role, threat):

    today_date = datetime.now().strftime("%d-%m-%Y")
    now_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    counter_file = "incident_counter.txt"

    # Read existing counter
    try:
        with open(counter_file, "r") as f:
            saved_date, count = f.read().split("|")
            count = int(count)

            if saved_date == today_date:
                count += 1
            else:
                count = 1
    except:
        count = 1

    # Save updated counter
    with open(counter_file, "w") as f:
        f.write(f"{today_date}|{count}")

    incident_number = str(count).zfill(3)

    incident_id = f"INC-{today_date}-{incident_number}"

    message = f"""🚨 SECURITY INCIDENT DETECTED

Date: {now_time}
Incident ID: {incident_id}
Role: {role}
Threat Level: {threat}
System Status: ALERT
"""

    send_alert(message)
# ==========================
# ROUTES
# ==========================

@app.route('/')
def home():
    session.clear()
    return render_template("index.html")

# ==========================
# LOGIN
# ==========================

@app.route('/login', methods=['POST'])
def login():

    role = request.form.get("role")
    password = request.form.get("password")
    security_answer = request.form.get("security_answer")
    otp_input = request.form.get("otp")

    if "attempts" not in session:
        session["attempts"] = 0

    # ================= ADMIN =================
    if role == "admin":

        # STEP 1: PASSWORD CHECK
        if password and password == ADMIN_PASS:
            session["attempts"] = 0
            otp = random.randint(1000, 9999)
            session["otp"] = str(otp)
            session["role"] = "ADMIN"

            send_alert(f"🔐 ADMIN MFA CODE: {otp}")
            return render_template("index.html", show_mfa=True, role="admin")

        # STEP 2: SECURITY QUESTION AFTER 3 FAILS
        if session["attempts"] >= 3 and security_answer:

            if security_answer == SECURITY_ANSWER:
                otp = random.randint(1000, 9999)
                session["otp"] = str(otp)
                session["role"] = "ADMIN"

                send_alert(f"🔐 ADMIN MFA CODE: {otp}")
                return render_template("index.html", show_mfa=True, role="admin")

            else:
                generate_incident("ADMIN", "CRITICAL")
                return render_template("index.html", error="Wrong Security Answer", role="admin")

        # STEP 3: MFA VERIFY
        if otp_input:
            if otp_input == session.get("otp"):
                send_alert("✅ ADMIN LOGIN SUCCESS")
                return render_template("index.html", success="Admin Login Successful")
            else:
                generate_incident("ADMIN", "HIGH")
                return render_template("index.html", error="Invalid OTP")

        # STEP 4: WRONG PASSWORD
        session["attempts"] += 1
        generate_incident("ADMIN", "HIGH")

        if session["attempts"] >= 3:
            return render_template("index.html", show_security=True, role="admin")

        return render_template("index.html", error=f"Wrong Admin Password ({session['attempts']}/3)", role="admin")

    # ================= USER =================
    elif role == "user":

        if password and password == USER_PASS:
            session["attempts"] = 0
            otp = random.randint(1000, 9999)
            session["otp"] = str(otp)
            session["role"] = "USER"

            send_alert(f"🔐 USER MFA CODE: {otp}")
            return render_template("index.html", show_mfa=True, role="user")

        if otp_input:
            if otp_input == session.get("otp"):
                send_alert("✅ USER LOGIN SUCCESS")
                return render_template("index.html", success="User Login Successful")
            else:
                generate_incident("USER", "MEDIUM")
                return render_template("index.html", error="Invalid OTP")

        session["attempts"] += 1
        generate_incident("USER", "MEDIUM")

        if session["attempts"] >= 3:
            session["attempts"] = 0
            return render_template("index.html", error="User Blocked After 3 Attempts")

        return render_template("index.html", error=f"Wrong User Password ({session['attempts']}/3)", role="user")

    return render_template("index.html", error="Invalid Role")

# ==========================
# SECURITY QUESTION
# ==========================

@app.route('/security', methods=['POST'])
def security():

    answer = request.form.get("answer")

    if answer == SECURITY_ANSWER:
        return "Admin Verified via Security Question"
    else:
        generate_incident("ADMIN", "CRITICAL")
        return "Security Verification Failed"

# ==========================
# MFA VERIFY
# ==========================

@app.route('/verify', methods=['POST'])
def verify():

    entered_otp = request.form.get("otp")

    if entered_otp == session.get("otp"):
        send_alert(f"✅ {session.get('role')} Login Successful")
        return f"{session.get('role')} Login Successful"
    else:
        generate_incident(session.get("role"), "HIGH")
        return "Invalid OTP"

# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    app.run(debug=True)
