from flask import Flask, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ADMIN_KEY = "1234"

clients = {}  # sid -> data


# ---------------- HOME ----------------
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Live Tracker</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;font-family:Arial;background:#0b0b1a;color:white;text-align:center}
#map{height:100vh}
#panel{
  position:absolute;top:10px;left:10px;
  background:#111;padding:10px;border-radius:10px;z-index:999
}
</style>
</head>
<body>

<div id="panel">
<h3>📡 Live Tracking</h3>
<button onclick="start()">Start Share</button>
<p id="status"></p>
</div>

<div id="map"></div>

<script>

let socket = io();
let watchId;
let myId;
let marker;

let map = L.map('map').setView([13.7,100.5],6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
.addTo(map);

function start(){
  if(!navigator.geolocation){
    alert("no gps");
    return;
  }

  watchId = navigator.geolocation.watchPosition(pos=>{
    socket.emit("update",{
      lat:pos.coords.latitude,
      lon:pos.coords.longitude,
      acc:pos.coords.accuracy
    });

    document.getElementById("status").innerText =
      "accuracy: "+Math.round(pos.coords.accuracy)+"m";

  },err=>{
    document.getElementById("status").innerText="permission denied";
  },{
    enableHighAccuracy:true,
    maximumAge:0
  });
}

socket.on("connect",()=>{
  myId = socket.id;
});

</script>

</body>
</html>
"""


# ---------------- ADMIN DASHBOARD ----------------
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
body{margin:0;background:#0b0b1a;color:white;font-family:Arial}
#map{height:100vh}
</style>
</head>
<body>

<div id="map"></div>

<script>

let socket = io();
let map = L.map('map').setView([13.7,100.5],6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
.addTo(map);

let markers = {};

socket.on("live", data=>{

  let id = data.id;

  if(!markers[id]){
    markers[id] = L.marker([data.lat,data.lon]).addTo(map);
  } else {
    markers[id].setLatLng([data.lat,data.lon]);
  }

});

</script>

</body>
</html>
"""


# ---------------- SOCKET LIVE ----------------
@socketio.on("update")
def handle_update(data):
    sid = request.sid

    lat = data.get("lat")
    lon = data.get("lon")
    acc = data.get("acc")

    clients[sid] = {
        "lat": lat,
        "lon": lon,
        "acc": acc,
        "time": str(datetime.now())
    }

    emit("live", {
        "id": sid,
        "lat": lat,
        "lon": lon,
        "acc": acc
    }, broadcast=True)


# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
