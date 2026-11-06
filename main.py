from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# ════════════════════════════════════════════════
# 🔧 إعدادات البوت (متسجلة وجاهزة)
# ════════════════════════════════════════════════
BOT_TOKEN = "8506499854:AAG3RdbtjIn-y0_lOGGL9BEFf4-PtcHTrgg"
ADMIN_CHAT_ID = "8739363751"
# ════════════════════════════════════════════════

API_KEY = "RAVEN_SECRET_2026_XYZ"  # كلمة السر دي هتستخدمها في المود والأداة

users_db = {}

def check_key():
    return request.headers.get("X-Raven-Key") == API_KEY

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except Exception as e:
        print(f"Telegram error: {e}")

@app.route("/")
def home():
    return "🦅 RAVEN Server is running!"

@app.route("/api/ping")
def ping():
    if not check_key():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"status": "ok", "users": len(users_db)})

@app.route("/api/login", methods=["POST"])
def login():
    if not check_key():
        return jsonify({"error": "unauthorized"}), 401
    data = request.json
    did = data.get("device_id", "unknown")
    label = data.get("label", "USER")
    now = datetime.now().isoformat()
    
    if did not in users_db:
        users_db[did] = {"label": label, "allowed": True, "last_seen": now, "blocked_reason": ""}
        send_telegram(f"🆕 <b>مستخدم جديد فتح المود</b>\n📱 <code>{did[:16]}</code>\n👤 <b>{label}</b>")
    else:
        users_db[did]["last_seen"] = now
        users_db[did]["label"] = label
        
    u = users_db[did]
    return jsonify({"allow": u["allowed"], "reason": u["blocked_reason"]})

@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    if not check_key():
        return jsonify({"error": "unauthorized"}), 401
    did = request.json.get("device_id", "unknown")
    if did not in users_db:
        return jsonify({"allow": False, "reason": "unknown"})
    
    users_db[did]["last_seen"] = datetime.now().isoformat()
    return jsonify({"allow": users_db[did]["allowed"], "reason": users_db[did]["blocked_reason"]})

@app.route("/api/list_users")
def list_users():
    if not check_key():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(users_db)

@app.route("/api/toggle", methods=["POST"])
def toggle():
    if not check_key():
        return jsonify({"error": "unauthorized"}), 401
    data = request.json
    did = data.get("device_id")
    allow = data.get("allow", True)
    
    if did in users_db:
        users_db[did]["allowed"] = allow
        users_db[did]["blocked_reason"] = "" if allow else "blocked by admin"
        send_telegram(f"{'✅ سمحت' if allow else '🚫 منعت'}: <b>{users_db[did]['label']}</b>")
        
    return jsonify({"status": "ok"})

@app.route("/panel")
def panel():
    key = request.args.get("key", "")
    return f"""<!DOCTYPE html><html><head><title>RAVEN</title><meta charset="UTF-8">
<style>body{{background:#0b0b12;color:#ece9f5;font-family:monospace;padding:20px}}
h1{{color:#a855f7}}table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #333}}
th{{background:#1a1a2e;color:#f5c518}}
.allow{{color:#4ade80;font-weight:bold}}.deny{{color:#fb7185;font-weight:bold}}
button{{padding:8px 16px;border:none;cursor:pointer;border-radius:4px;font-weight:bold;margin:2px}}
.btn-block{{background:#fb7185;color:white}}.btn-allow{{background:#4ade80;color:black}}
</style></head><body><h1>🦅 RAVEN CONTROL</h1>
<table id="users"><tr><th>DEVICE</th><th>NAME</th><th>STATUS</th><th>LAST</th><th>ACTION</th></tr></table>
<script>
const KEY="{key}";
function load(){{fetch('/api/list_users',{{headers:{{'X-Raven-Key':KEY}}}}).then(r=>r.json()).then(d=>{{
const t=document.getElementById('users');
t.innerHTML='<tr><th>DEVICE</th><th>NAME</th><th>STATUS</th><th>LAST</th><th>ACTION</th></tr>';
for(const[id,u]of Object.entries(d)){{
t.innerHTML+=`<tr><td><code>${{id.substring(0,16)}}</code></td><td>${{u.label}}</td>
<td class="${{u.allowed?'allow':'deny'}}">${{u.allowed?'✅':'🚫'}}</td>
<td>${{u.last_seen}}</td>
<td>${{u.allowed?`<button class="btn-block" onclick="tg('${{id}}',false)">BLOCK</button>`:`<button class="btn-allow" onclick="tg('${{id}}',true)">ALLOW</button>`}}</td></tr>`;}}}});}}
function tg(id,a){{fetch('/api/toggle',{{method:'POST',headers:{{'Content-Type':'application/json','X-Raven-Key':KEY}},body:JSON.stringify({{device_id:id,allow:a}})}}).then(()=>load());}}
load();setInterval(load,5000);
</script></body></html>"""