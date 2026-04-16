from flask import Flask, request
import requests
import os

app = Flask(__name__)

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

    return f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
    <meta charset="UTF-8">
    <title>Welcome</title>
    <style>
    body {{
        background: linear-gradient(135deg, #1e1e2f, #3a3a6a);
        color: white;
        font-family: Arial;
        text-align: center;
        padding-top: 100px;
    }}
    .box {{
        background: rgba(0,0,0,0.3);
        padding: 30px;
        border-radius: 15px;
        width: 300px;
        margin: auto;
    }}
    button {{
        padding: 10px 20px;
        border: none;
        border-radius: 10px;
        background: #6c5ce7;
        color: white;
        cursor: pointer;
    }}
    button:hover {{
        background: #a29bfe;
    }}
    .small {{
        font-size: 12px;
        color: #ccc;
        margin-top: 20px;
    }}
    </style>
    </head>
    <body>

    <div class="box">
        <h1>🎉 Welcome</h1>
        <p>กดปุ่มด้านล่างเพื่อเริ่มต้น</p>

        <button onclick="alert('เริ่มแล้ว!')">Start</button>

        <div class="small">
            เว็บไซต์นี้มีการเก็บข้อมูลการใช้งานเพื่อสถิติ
        </div>
    </div>

    </body>
    </html>
    """

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
