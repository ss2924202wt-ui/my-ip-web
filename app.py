from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

ADMIN_KEY = "0949205717As"

# ----------------- SCORE -----------------

def calc_reliability(acc, percent, proxy, device):
    score = 0

    # accuracy score
    if acc <= 20: score += 45
    elif acc <= 50: score += 35
    elif acc <= 100: score += 25
    elif acc <= 200: score += 15
    elif acc <= 500: score += 8
    else: score += 3

    # percent
    score += int(percent * 0.3)

    # device bonus
    if device == "mobile":
        score += 5

    # proxy penalty
    if proxy:
        score -= 30

    return max(0, min(100, score))


def detect_device(ua):
    if "Mobile" in ua:
        return "mobile"
    return "desktop"

# ----------------- HOME -----------------

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Verification System</title>
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
</style>
</head>
<body>

<div class="card">
  <h2>🔐 กดเพื่อยืนยัน</h2>
  <p>ระบบกำลังตรวจสอบข้อมูล</p>
  <button onclick="start()">เริ่ม</button>
  <p id="status"></p>
</div>

<script>

let tries = 0;
let MAX = 10;
let results = [];

function start(){
  document.getElementById("status").innerText = "กำลังวิเคราะห์...";

  for(let i=0;i<MAX;i++){
    scan();
  }
}

function scan(){
  setTimeout(() => {
    tries++;

    let data = {
      acc: Math.random() * 500
    };

    results.push(data);

    document.getElementById("status").innerText =
      "กำลังประมวลผล ("+tries+"/"+MAX+") | "+Math.round(data.acc)+"m";

    if(tries >= MAX){
      finish();
    }
  }, 200);
}

function calcPercent(acc){
  if(acc <= 20) return 99;
  if(acc <= 50) return 90;
  if(acc <= 100) return 80;
  if(acc <= 200) return 65;
  if(acc <= 500) return 50;
  return 30;
}

function finish(){
  results.sort((a,b)=>a.acc-b.acc);
  let best = results[0];

  let percent = calcPercent(best.acc);

  fetch("/location", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      acc: best.acc,
      percent: percent
    })
  }).then(()=>window.location="/done");
}

</script>

</body>
</html>
"""

# ----------------- DONE -----------------

@app.route("/done")
def done():
    return """
    <body style="background:black;color:white;text-align:center;padding:100px">
    <h1>✅ เสร็จแล้ว</h1>
    <p>ระบบทำงานเรียบร้อย</p>
    </body>
    """

# ----------------- API -----------------

@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()

    acc = float(data.get("acc", 999))
    percent = int(data.get("percent", 0))

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    device = detect_device(ua)

    proxy = False  # ปิดระบบตรวจ proxy แบบง่าย

    reliability = calc_reliability(acc, percent, proxy, device)

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("log.txt", "a") as f:
        f.write(f"{time}|{ip}|{device}|{acc}|{percent}|{reliability}\n")

    return jsonify({"ok": True})

# ----------------- ADMIN -----------------

@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_KEY:
        return "Denied"

    rows = ""

    try:
        with open("log.txt") as f:
            for line in f:
                t, ip, device, acc, percent, rel = line.strip().split("|")

                color = "lime" if int(percent) > 80 else "orange" if int(percent) > 50 else "red"

                rows += f"""
                <tr>
                  <td>{t}</td>
                  <td>{ip}</td>
                  <td>{device}</td>
                  <td>{acc}</td>
                  <td style="color:{color}">{percent}%</td>
                  <td>{rel}</td>
                </tr>
                """
    except:
        rows = "<tr><td colspan=6>No data</td></tr>"

    return f"""
    <html>
    <head>
    <title>Dashboard</title>
    <style>
    body{{background:#0f0f1f;color:white;font-family:Arial}}
    table{{width:100%;text-align:center}}
    </style>
    </head>

    <body>
    <h1>📊 Dashboard</h1>

    <table border=1>
    <tr>
    <th>Time</th><th>IP</th><th>Device</th><th>Accuracy</th><th>%</th><th>Score</th>
    </tr>
    {rows}
    </table>

    </body>
    </html>
    """

# -----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
