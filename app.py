# app.py
# Pure Flask API + Embedded Admin Panel – No Telegram, No Auth, No DB

from flask import Flask, request, jsonify, Response
import time

app = Flask(__name__)

# ================= IN-MEMORY STORAGE =================
current_signal = None
history = []

# ================= ADMIN PANEL (HTML + CSS + JS) =================
@app.route("/admin")
def admin_panel():
    admin_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Control Panel</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #3b82f6;
            --success: #2ecc71;
            --danger: #ef4444;
            --bg-dark: #09090b;
            --card-bg: #18181b;
            --input-bg: #27272a;
            --text-light: #f4f4f5;
            --text-gray: #a1a1aa;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-light);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            display: flex;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }

        #dashboard {
            width: 100%;
            max-width: 800px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #333;
            padding-bottom: 15px;
        }
        .brand { font-size: 20px; font-weight: bold; letter-spacing: 1px; }
        .brand span { color: var(--primary); }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #333;
        }
        .stat-val { font-size: 24px; font-weight: bold; color: white; }
        .stat-label { font-size: 12px; color: var(--text-gray); margin-top: 5px; }

        .panel {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #333;
            margin-bottom: 20px;
        }
        .panel-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            color: var(--text-gray);
            text-transform: uppercase;
        }

        .input-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .input-group > input {
            flex: 1;
            min-width: 120px;
            padding: 10px;
            background: var(--input-bg);
            border: 1px solid #333;
            border-radius: 8px;
            color: white;
        }

        .btn-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 10px;
        }

        .btn-sig {
            padding: 15px;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            font-size: 14px;
        }
        .btn-sig:active { transform: scale(0.95); }

        .s-sell { background: linear-gradient(145deg, #7f1d1d, #991b1b); }
        .sell { background: linear-gradient(145deg, #ea580c, #c2410c); }
        .buy { background: linear-gradient(145deg, #2563eb, #1d4ed8); }
        .s-buy { background: linear-gradient(145deg, #16a34a, #15803d); }

        .trade-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #27272a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #555;
        }
        .trade-info { display: flex; flex-direction: column; }
        .trade-asset { font-weight: bold; font-size: 14px; }
        .trade-type { font-size: 12px; color: #aaa; }

        .action-btns { display: flex; gap: 10px; }
        .btn-res {
            padding: 8px 15px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            color: white;
        }
        .btn-win { background: var(--success); }
        .btn-loss { background: var(--danger); }

        @media (max-width: 600px) {
            .stats-grid { grid-template-columns: 1fr; }
            .btn-grid { grid-template-columns: 1fr 1fr; }
            .input-group { flex-direction: column; }
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
            color: #555;
        }
    </style>
</head>
<body>

<div id="dashboard">
    <div class="header">
        <div class="brand">ADMIN <span>CONTROL</span></div>
        <div style="font-size: 12px; color: #666;">v2.0</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card"><div class="stat-val">—</div><div class="stat-label">Total Users</div></div>
        <div class="stat-card"><div class="stat-val">—</div><div class="stat-label">Online Now</div></div>
        <div class="stat-card"><div class="stat-val">—</div><div class="stat-label">Active Signals</div></div>
    </div>

    <div class="panel">
        <div class="panel-title">📡 Create Signal</div>
        <div class="input-group">
            <input type="text" id="asset-input" placeholder="Pair (e.g. EURUSD)">
            <input type="number" id="time-input" placeholder="Time (Min)">
        </div>
        <div style="font-size: 11px; color: #666; margin-bottom: 10px;">Select Signal Type to Send:</div>
        <div class="btn-grid">
            <button class="btn-sig s-sell" onclick="sendSignal('STRONG SELL', 10)">S. SELL</button>
            <button class="btn-sig sell" onclick="sendSignal('SELL', 30)">SELL</button>
            <button class="btn-sig buy" onclick="sendSignal('BUY', 70)">BUY</button>
            <button class="btn-sig s-buy" onclick="sendSignal('STRONG BUY', 90)">S. BUY</button>
        </div>
    </div>

    <div class="panel">
        <div class="panel-title">⚡ Active Trades</div>
        <div id="active-trades-list">
            <div style="text-align: center; color: #444; font-size: 12px;">No active trades</div>
        </div>
    </div>

    <div class="footer">Admin Panel – No Telegram, No Auth</div>
</div>

<script>
    function sendSignal(type, needleVal) {
        const assetRaw = document.getElementById('asset-input').value.trim().toUpperCase();
        const timeVal = document.getElementById('time-input').value.trim();
        if (!assetRaw || !timeVal) {
            alert("Please fill both Asset and Time.");
            return;
        }
        const finalAsset = assetRaw.includes("OTC") ? assetRaw : assetRaw + " (OTC)";
        fetch("/api/send-signal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ asset: finalAsset, time: parseInt(timeVal), type: type, needle: needleVal })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                addActiveTrade(finalAsset, type, timeVal);
                document.getElementById('asset-input').value = "";
                document.getElementById('time-input').value = "";
            }
        })
        .catch(() => alert("Failed to send signal."));
    }

    function addActiveTrade(asset, type, time) {
        const list = document.getElementById('active-trades-list');
        if (list.innerHTML.includes("No active trades")) list.innerHTML = "";
        const id = Date.now();
        const color = type.includes("SELL") ? "#ef4444" : "#3b82f6";
        const div = document.createElement("div");
        div.id = "trade-" + id;
        div.className = "trade-item";
        div.style.borderLeftColor = color;
        div.innerHTML = `
            <div class="trade-info">
                <span class="trade-asset">${asset}</span>
                <span class="trade-type">${type} - ${time} Min</span>
            </div>
            <div class="action-btns">
                <button class="btn-res btn-win" onclick="sendResult(${id}, 'WIN')">WIN</button>
                <button class="btn-res btn-loss" onclick="sendResult(${id}, 'LOSS')">LOSS</button>
            </div>
        `;
        list.prepend(div);
    }

    function sendResult(id, result) {
        fetch("/api/send-result", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ result: result })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "saved") {
                const el = document.getElementById("trade-" + id);
                if (el) el.remove();
                if (document.getElementById('active-trades-list').children.length === 0) {
                    document.getElementById('active-trades-list').innerHTML = 
                        '<div style="text-align: center; color: #444; font-size: 12px;">No active trades</div>';
                }
            }
        })
        .catch(() => alert("Failed to send result."));
    }
</script>
</body>
</html>
    '''
    return Response(admin_html, mimetype="text/html")


# ================= API ENDPOINTS =================
@app.route("/api/send-signal", methods=["POST"])
def send_signal():
    global current_signal
    data = request.json
    current_signal = {
        "asset": data["asset"],
        "duration": data["time"],
        "needleValue": data["needle"],
        "timestamp": int(time.time())
    }
    # ملاحظة: لم يعد هناك إرسال إلى Telegram
    return jsonify({"status": "ok"})


@app.route("/api/latest-signal")
def latest_signal():
    if not current_signal:
        return jsonify({})
    return jsonify(current_signal)


@app.route("/api/send-result", methods=["POST"])
def send_result():
    global current_signal
    result = request.json.get("result")
    if current_signal:
        history.insert(0, {
            "asset": current_signal["asset"].split(" ")[0],
            "dir": "BUY" if current_signal["needleValue"] > 50 else "SELL",
            "time": str(current_signal["duration"]) + "m",
            "res": result
        })
        current_signal = None
    return jsonify({"status": "saved"})


@app.route("/api/history")
def get_history():
    return jsonify(history[:200])


# ================= OPTIONAL: Homepage to avoid 404 =================
@app.route("/")
def home():
    return '<h3>TradeHub API</h3><p>Go to <a href="/admin">Admin Panel</a></p>'


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
