from flask import Flask, request
import requests

app = Flask(__name__)

@app.route("/")
def home():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        data = requests.get(f"https://ipinfo.io/{ip}/json").json()
        country = data.get("country")
        city = data.get("city")
        isp = data.get("org")
    except:
        country = city = isp = "Unknown"

    return f"""
    <h1>Visitor Info</h1>
    <p>IP: {ip}</p>
    <p>Country: {country}</p>
    <p>City: {city}</p>
    <p>ISP: {isp}</p>
    <p style='color:red;'>ตำแหน่งนี้เป็นแค่คร่าวๆ</p>
    """

app.run(host="0.0.0.0", port=5000)