from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔑 รหัสเข้าหน้า admin
ADMIN_KEY = "1234"   # เปลี่ยนเป็นของคุณเอง

@app.route("/")
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        data = requests.get(f"https://ipinfo.io/{ip}/json").json()
        country = data.get("country")
        city = data.get("city")
        isp = data.get("org")
    except:
        country = city = isp = "Unknown"

    # บันทึก log
    with open("log.txt", "a") as f:
        f.write(f"{ip} | {country} | {city} | {isp}\n")

    return """
    <h1>Welcome 🎉</h1>
    <p>กดปุ่มเพื่อเริ่ม</p>
    <button onclick="alert('เริ่มแล้ว!')">Start</button>
    <p style='font-size:12px;'>เว็บไซต์นี้มีการเก็บข้อมูลเพื่อสถิติ</p>
    """

# 🔥 หน้า admin (ดู log)
@app.route("/admin")
def admin():
    key = request.args.get("key")

    if key != ADMIN_KEY:
        return "Access Denied ❌"

    try:
        with open("log.txt", "r") as f:
            logs = f.read()
    except:
        logs = "No data yet"

    return f"<pre>{logs}</pre>"

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
