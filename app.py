from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 เปลี่ยนรหัสตรงนี้
ADMIN_KEY = "1234"

@app.route("/")
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        data = requests.get(f"https://ipinfo.io/{ip}/json").json()
        country = data.get("country", "Unknown")
        city = data.get("city", "Unknown")
        isp = data.get("org", "Unknown")
    except:
        country = city = isp = "Unknown"

    # 📝 บันทึก log
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ip} | {country} | {city} | {isp}\n")

    return """
    <!DOCTYPE html>
    <html lang="th">
    <head>
    <meta charset="UTF-8">
    <title>Welcome</title>
    <style>
    body {
        background: linear-gradient(135deg, #1e1e2f, #3a3a6a);
        color: white;
        font-family: Arial;
        text-align: center;
        padding-top: 100px;
    }
    .box {
        background: rgba(0,0,0,0.3);
        padding: 30px;
        border-radius: 15px;
        width: 300px;
        margin: auto;
    }
    button {
        padding: 10px 20px;
        border: none;
        border-radius: 10px;
        background: #6c5ce7;
        color: white;
        cursor: pointer;
    }
    button:hover {
        background: #a29bfe;
    }
    .small {
        font-size: 12px;
        color: #ccc;
        margin-top: 20px;
    }
    </style>
    </head>
    <body>

    <div class="box">
        <h1>🎉 Welcome</h1>
        <p>กดปุ่มเพื่อเริ่มต้น</p>
        <button onclick="alert('เริ่มแล้ว!')">Start</button>

        <div class="small">
            เว็บไซต์นี้มีการเก็บข้อมูลเพื่อสถิติ
        </div>
    </div>

    </body>
    </html>
    """

# 🔥 หน้าแอดมินดูข้อมูล
@app.route("/admin")
def admin():
    key = request.args.get("key")

    if key != ADMIN_KEY:
        return "Access Denied ❌"

    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            logs = f.read()
    except:
        logs = "No data yet"

    return f"<pre>{logs}</pre>"

# 🚀 รันสำหรับ Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
