from flask import Flask, request, jsonify
import os, re
from datetime import datetime
import requests

app = Flask(__name__)

ADMIN_KEY = "0949205717As"

# --------- Device ----------
MOBILE_RE = re.compile(r"Android|iPhone|iPad|iPod|Mobile", re.I)

def detect_device(ua):
    return "mobile" if MOBILE_RE.search(ua or "") else "desktop"

# --------- IP Location ----------
def get_ip_info(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=4).json()
        return {
            "city": r.get("city", "Unknown"),
            "country": r.get("country", "Unknown"),
            "isp": r.get("isp", "Unknown"),
            "lat": r.get("lat", 0),
            "lon": r.get("lon", 0)
        }
    except:
        return {
            "city": "Unknown",
            "country": "Unknown",
            "isp": "Unknown",
            "lat": 0,
            "lon": 0
        }

# --------- Home ----------
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>IP Tracker</title>
</head>
<body style="background:black;color:white;text-align:center;padding:50px">

<h1>🔐 ระบบกำลังทำงาน</h1>
<p>ระบบนี้ใช้ IP tracking (ไม่ขอ permission)</p>

<button onclick="send()">เริ่ม</button>

<p id="status"></p>

<script>
function send(){
    document.getElementById("status").innerText = "กำลังตรวจสอบ IP...";

    fetch("/track", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({})
    }).then(r=>r.json()).then(d=>{
        document.getElementById("status").innerText =
        "สำเร็จ: " + d.city + ", " + d.country;
    });
}
</script>

</body>
</html>
"""

# --------- Track ----------
@app.route("/track", methods=["POST"])
def track():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    device = detect_device(ua)
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info = get_ip_info(ip)

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time}|{ip}|{device}|{info['country']}|{info['city']}|{info['isp']}|{info['lat']}|{info['lon']}\n")

    return jsonify(info)

# --------- Admin ----------
@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_KEY:
        return "Access Denied"

    rows = ""

    try:
        with open("log.txt", encoding="utf-8") as f:
            for line in f:
                t, ip, device, country, city, isp, lat, lon = line.strip().split("|")

                map_link = f"https://www.google.com/maps?q={lat},{lon}"

                rows += f"""
                <tr>
                    <td>{t}</td>
                    <td>{ip}</td>
                    <td>{device}</td>
                    <td>{country}</td>
                    <td>{city}</td>
                    <td>{isp}</td>
                    <td><a href="{map_link}" target="_blank">📍</a></td>
                </tr>
                """
    except:
        rows = "<tr><td colspan=7>No data</td></tr>"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>
<style>
body{{background:#0f0f1f;color:white;font-family:Arial}}
table{{width:100%;text-align:center}}
</style>
</head>
<body>

<h1>📊 IP DASHBOARD</h1>

<table border="1">
<tr>
<th>Time</th><th>IP</th><th>Device</th>
<th>Country</th><th>City</th><th>ISP</th><th>Map</th>
</tr>
{rows}
</table>

</body>
</html>
"""

# ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
# ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
