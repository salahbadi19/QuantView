# app.py
# Pure Flask API + Embedded Admin Panel + Embedded User UI
# No Telegram, No Auth, No DB — Ready for Render

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time
import os

app = Flask(__name__)
CORS(app)  # يسمح بطلبات من أي مصدر (ضروري لواجهة المستخدم)

# ================= IN-MEMORY STORAGE =================
current_signal = None
history = []

# ================= USER INTERFACE (EMBEDDED) =================
USER_UI_HTML = '''
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Pro Signals & History</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #3b82f6;
            --success: #2ecc71;
            --danger: #ef4444;
            --bg-dark: #000000;
            --glass: rgba(20, 20, 20, 0.95);
        }

        body {
            background: radial-gradient(circle at center, #1a1a1a 0%, #000000 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            color: white;
            -webkit-tap-highlight-color: transparent;
        }

        #start-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 2000;
            font-size: 16px;
            color: var(--primary);
            animation: pulse 1.5s infinite;
            pointer-events: none;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: bold;
        }
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }

        .app-container {
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding-bottom: 70px;
            box-sizing: border-box;
            overflow: hidden;
        }

        #gauge-page {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
        }

        .frame {
            background: linear-gradient(145deg, #111111, #0a0a0a);
            border: 1px solid #333;
            border-radius: 20px;
            width: 100%; 
            max-width: 400px;
            aspect-ratio: 4/3; 
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.9), inset 0 1px 1px rgba(255,255,255,0.1);
            position: relative;
            transition: border-color 0.5s ease;
            margin-bottom: 20px;
        }

        .gauge-svg { width: 95%; height: auto; z-index: 1; filter: drop-shadow(0 0 10px rgba(0,0,0,0.5)); }
        #needle-group { transition: transform 1s cubic-bezier(0.3, 0.8, 0.5, 1); transform-origin: 200px 200px; }
        .digital-font { font-family: 'Courier New', monospace; font-weight: bold; }

        .social-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            width: 100%;
        }
        .follow-text { font-size: 12px; color: #ccc; letter-spacing: 0.5px; }
        .social-icons { display: flex; gap: 35px; }
        .social-link { font-size: 28px; color: #888; transition: 0.3s; }
        .social-link:hover { color: white; transform: scale(1.1); }
        
        .risk-warning {
            width: 90%;
            text-align: center;
            font-size: 9px;
            color: #444;
            line-height: 1.4;
            margin-top: 15px;
            border-top: 1px solid #222;
            padding-top: 10px;
        }

        .dev-credit {
            margin-top: 20px;
            font-size: 11px;
            color: #666;
            font-weight: bold;
            text-transform: uppercase;
        }
        .dev-name {
            background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        #history-page {
            display: none;
            flex-direction: column;
            width: 100%;
            height: 100%;
            background: #050505;
            padding: 15px;
            box-sizing: border-box;
        }

        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 15px;
            border-bottom: 1px solid #222;
            margin-bottom: 10px;
        }

        .history-title {
            font-size: 18px;
            color: white;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .table-container {
            flex: 1;
            overflow-y: auto;
            border-radius: 8px;
            background: #0f0f0f;
            border: 1px solid #222;
        }

        table { width: 100%; border-collapse: collapse; }
        thead { background: #1a1a1a; position: sticky; top: 0; }
        th { color: #888; font-size: 11px; text-transform: uppercase; padding: 12px 8px; text-align: center; letter-spacing: 1px; }
        td { padding: 12px 8px; text-align: center; font-size: 13px; border-bottom: 1px solid #1a1a1a; color: #ddd; }
        tr:nth-child(even) { background: #141414; }
        
        .buy-badge { color: var(--primary); font-weight: bold; background: rgba(59, 130, 246, 0.1); padding: 2px 6px; border-radius: 4px; }
        .sell-badge { color: #ff9f43; font-weight: bold; background: rgba(255, 159, 67, 0.1); padding: 2px 6px; border-radius: 4px; }
        .win-res { color: var(--success); font-weight: bold; }
        .loss-res { color: var(--danger); font-weight: bold; }

        .pagination {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid #222;
        }
        
        .page-info { font-size: 12px; color: #666; }
        
        .btn-nav {
            background: #222;
            color: white;
            border: 1px solid #333;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn-nav:active { transform: scale(0.95); }
        .btn-nav:disabled { opacity: 0.5; cursor: not-allowed; }

        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 65px;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid #333;
            display: flex;
            justify-content: space-around;
            align-items: center;
            z-index: 1000;
        }

        .nav-item {
            color: #555;
            font-size: 22px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 50%;
            padding: 10px 0;
            transition: 0.3s;
        }
        .nav-item.active { color: var(--primary); text-shadow: 0 0 10px rgba(59, 130, 246, 0.4); }
        .nav-label { font-size: 10px; margin-top: 4px; font-weight: 500; }

    </style>
</head>
<body>

    <div id="start-overlay">Tap to Activate System</div>

    <div class="app-container">
        <div id="gauge-page">
            <div class="frame" id="mainFrame">
                <svg class="gauge-svg" viewBox="0 0 400 280" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="arcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#ef4444" />
                            <stop offset="20%" stop-color="#ff9f43" />
                            <stop offset="50%" stop-color="#6b7280" />
                            <stop offset="80%" stop-color="#2ecc71" />
                            <stop offset="100%" stop-color="#3b82f6" />
                        </linearGradient>
                        <linearGradient id="needleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#e0e0e0" />
                            <stop offset="50%" stop-color="#ffffff" />
                            <stop offset="100%" stop-color="#b0b0b0" />
                        </linearGradient>
                        <linearGradient id="cardGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#222" stop-opacity="0.95"/>
                            <stop offset="100%" stop-color="#000" stop-opacity="0.98"/>
                        </linearGradient>
                        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
                        </filter>
                        <filter id="dropShadow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
                            <feOffset dx="2" dy="4" result="offsetblur"/>
                            <feMerge><feMergeNode in="offsetblur"/><feMergeNode in="SourceGraphic"/></feMerge>
                        </filter>
                    </defs>

                    <path d="M 50 200 A 150 150 0 0 1 350 200" fill="none" stroke="#1f1f1f" stroke-width="16" stroke-linecap="round"/>
                    <path d="M 50 200 A 150 150 0 0 1 350 200" fill="none" stroke="url(#arcGradient)" stroke-width="16" stroke-linecap="round" filter="url(#glow)"/>
                    <circle cx="200" cy="200" r="14" fill="#222" stroke="#444" stroke-width="2" filter="url(#dropShadow)"/>

                    <g id="needle-group" filter="url(#dropShadow)">
                        <polygon points="200,200 196,110 200,95 204,110 200,200" fill="url(#needleGradient)"/>
                        <path d="M 200 200 L 200 100" stroke="rgba(255,255,255,0.6)" stroke-width="1"/>
                    </g>

                    <text x="45" y="225" font-size="11" fill="#ef4444" text-anchor="middle" font-weight="bold">S.SELL</text>
                    <text x="45" y="240" font-size="10" fill="#7f1d1d" text-anchor="middle" font-weight="bold">90%</text>
                    <text x="45" y="105" font-size="11" fill="#ff9f43" text-anchor="middle" font-weight="bold">SELL</text>
                    <text x="200" y="30" font-size="11" fill="#a4b0be" text-anchor="middle" font-weight="bold">NEUTRAL</text>
                    <text x="355" y="105" font-size="11" fill="#3b82f6" text-anchor="middle" font-weight="bold">BUY</text>
                    <text x="355" y="225" font-size="11" fill="#2ecc71" text-anchor="middle" font-weight="bold">S.BUY</text>
                    <text x="355" y="240" font-size="10" fill="#14532d" text-anchor="middle" font-weight="bold">90%</text>

                    <g transform="translate(0, 10)">
                        <rect x="120" y="220" width="160" height="50" rx="12" fill="url(#cardGradient)" stroke="#333" stroke-width="1" filter="url(#dropShadow)"/>
                        <path d="M 130 221 L 270 221" stroke="rgba(255,255,255,0.15)" stroke-width="1" stroke-linecap="round"/>
                        <text id="asset-text" x="200" y="240" font-size="12" fill="#ffffff" text-anchor="middle" font-weight="bold" letter-spacing="1">WAITING...</text>
                        <line x1="198" y1="248" x2="198" y2="265" stroke="#444" stroke-width="1" />
                        <text id="time-text" x="160" y="260" font-size="13" fill="#9ca3af" text-anchor="middle" class="digital-font">-- M</text>
                        <text id="percent-text" x="240" y="260" font-size="13" fill="#9ca3af" text-anchor="middle" class="digital-font">--%</text>
                    </g>
                </svg>
            </div>

            <div class="social-wrapper">
                <div class="follow-text">Follow us for updates & more bots:</div>
                <div class="social-icons">
                    <!-- Social media links -->
                    <a href="#" class="social-link"><i class="fab fa-instagram"></i></a>
                    <a href="#" class="social-link"><i class="fab fa-tiktok"></i></a>
                    <a href="#" class="social-link"><i class="fab fa-telegram-plane"></i></a>
                </div>
            </div>

            <div class="risk-warning">
                ⚠️ Warning: Trading involves high risk. Signals are not guaranteed. We accept no liability for any losses.
            </div>

            <div class="dev-credit">Developed by <span class="dev-name">BADI SALAH</span></div>
        </div>

        <div id="history-page">
            <div class="history-header">
                <div class="history-title"><i class="fas fa-list-ul"></i> Trading Logs</div>
            </div>
            <div class="table-container">
                <table id="history-table">
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Dir</th>
                            <th>Time</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            <div class="pagination">
                <button class="btn-nav" id="prev-btn" onclick="changePage(-1)" disabled>Previous</button>
                <span class="page-info" id="page-info">Page 1</span>
                <button class="btn-nav" id="next-btn" onclick="changePage(1)">Next</button>
            </div>
            <div class="dev-credit" style="text-align: center; margin-top: 10px;">Developed by <span class="dev-name">BADI SALAH</span></div>
        </div>
    </div>

    <div class="nav-bar">
        <div class="nav-item active" onclick="switchPage('gauge')">
            <i class="fas fa-gauge-high"></i>
            <span class="nav-label">Indicator</span>
        </div>
        <div class="nav-item" onclick="switchPage('history')">
            <i class="fas fa-chart-line"></i>
            <span class="nav-label">Results</span>
        </div>
    </div>

    <script>
        const USE_API = true;
        const API_URL_SIGNAL = "/api/latest-signal";
        const API_URL_HISTORY = "/api/history";

        const gaugePage = document.getElementById('gauge-page');
        const historyPage = document.getElementById('history-page');
        const navItems = document.querySelectorAll('.nav-item');
        const overlay = document.getElementById('start-overlay');
        const needleGroup = document.getElementById('needle-group');
        const timeText = document.getElementById('time-text');
        const percentText = document.getElementById('percent-text');
        const assetText = document.getElementById('asset-text');
        const mainFrame = document.getElementById('mainFrame');
        const historyTableBody = document.querySelector('#history-table tbody');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const pageInfo = document.getElementById('page-info');
        
        let allHistoryData = [];
        let currentPage = 1;
        const rowsPerPage = 20;
        let audioCtx;
        let isStarted = false;
        let lastSignalTimestamp = null;

        function switchPage(page) {
            if (page === 'gauge') {
                gaugePage.style.display = 'flex';
                historyPage.style.display = 'none';
                navItems[0].classList.add('active');
                navItems[1].classList.remove('active');
            } else {
                gaugePage.style.display = 'none';
                historyPage.style.display = 'flex';
                navItems[0].classList.remove('active');
                navItems[1].classList.add('active');
                loadAndRenderHistory();
            }
        }

        async function playChimeSequence(count) {
            if (!audioCtx) return;
            for (let i = 0; i < count; i++) {
                playOneTone();
                await new Promise(r => setTimeout(r, 600));
            }
        }

        function playOneTone() {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, audioCtx.currentTime);
            gain.gain.setValueAtTime(0, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.2, audioCtx.currentTime + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.0);
            osc.start();
            osc.stop(audioCtx.currentTime + 1.0);
        }

        async function fetchSignalData() {
            if (!USE_API) return;
            try {
                const response = await fetch(API_URL_SIGNAL);
                const data = await response.json();
                if (Object.keys(data).length === 0) {
                    if (lastSignalTimestamp === null) resetGauge();
                    return;
                }
                if (lastSignalTimestamp === data.timestamp) return;
                lastSignalTimestamp = data.timestamp;
                processSignal(data);
            } catch (error) {
                console.error("Error fetching signal:", error);
            }
        }

        function resetGauge() {
            assetText.textContent = "WAITING...";
            timeText.textContent = "-- M";
            percentText.textContent = "--%";
            needleGroup.style.transform = "rotate(-90deg)";
            percentText.setAttribute('fill', '#9ca3af');
            mainFrame.style.borderColor = "#333";
        }

        function processSignal(data) {
            const angle = (data.needleValue / 100 * 180) - 90;
            needleGroup.style.transform = `rotate(${angle}deg)`;

            let distanceFromCenter = Math.abs(data.needleValue - 50);
            let successRate = Math.round(distanceFromCenter * 1.95);
            if (successRate > 98) successRate = 98;
            if (successRate < 10) successRate = 10;

            assetText.textContent = data.asset;
            timeText.textContent = data.duration + " Min";
            percentText.textContent = successRate + "%";

            mainFrame.style.borderColor = "#333";
            percentText.setAttribute('fill', '#9ca3af');
            
            let chimeCount = 0;
            if (data.needleValue >= 85) {
                mainFrame.style.borderColor = "#2ecc71";
                percentText.setAttribute('fill', "#2ecc71");
                chimeCount = 3;
            } else if (data.needleValue >= 60) {
                percentText.setAttribute('fill', "#3b82f6");
                chimeCount = 1;
            } else if (data.needleValue <= 15) {
                mainFrame.style.borderColor = "#ef4444";
                percentText.setAttribute('fill', "#ef4444");
                chimeCount = 3;
            } else if (data.needleValue <= 40) {
                percentText.setAttribute('fill', "#ff9f43");
                chimeCount = 1;
            } else {
                percentText.setAttribute('fill', "#a4b0be");
            }

            if (chimeCount > 0) playChimeSequence(chimeCount);
        }

        async function loadAndRenderHistory() {
            try {
                const response = await fetch(API_URL_HISTORY);
                const data = await response.json();
                allHistoryData = Array.isArray(data) ? data : [];
                currentPage = 1;
                renderTable();
            } catch (error) {
                console.error("Error loading history:", error);
                allHistoryData = [];
                renderTable();
            }
        }

        function renderTable() {
            historyTableBody.innerHTML = "";
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            const pageItems = allHistoryData.slice(start, end);

            pageItems.forEach(item => {
                const row = document.createElement('tr');
                let dirHTML = item.dir === "BUY" 
                    ? `<span class="buy-badge">BUY</span>` 
                    : `<span class="sell-badge">SELL</span>`;
                let resHTML = item.res === "WIN" 
                    ? `<span class="win-res">WIN</span>` 
                    : `<span class="loss-res">LOSS</span>`;

                row.innerHTML = `
                    <td>${item.asset}</td>
                    <td>${dirHTML}</td>
                    <td>${item.time}</td>
                    <td>${resHTML}</td>
                `;
                historyTableBody.appendChild(row);
            });

            if (pageItems.length < rowsPerPage) {
                for (let i = 0; i < (rowsPerPage - pageItems.length); i++) {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>-</td><td>-</td><td>-</td><td>-</td>`;
                    historyTableBody.appendChild(row);
                }
            }

            pageInfo.textContent = `Page ${currentPage}`;
            prevBtn.disabled = currentPage === 1;
            nextBtn.disabled = end >= allHistoryData.length;
        }

        function changePage(direction) {
            currentPage += direction;
            renderTable();
        }

        document.body.addEventListener('click', function() {
            if (!isStarted) {
                isStarted = true;
                overlay.style.display = 'none';
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                fetchSignalData();
                setInterval(fetchSignalData, 1000);
                loadAndRenderHistory();
            }
        });
    </script>
</body>
</html>
'''

# ================= ADMIN PANEL (EMBEDDED) =================
ADMIN_PANEL_HTML = '''
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

# ================= ROUTES =================
@app.route("/")
def user_ui():
    return Response(USER_UI_HTML, mimetype="text/html")

@app.route("/admin")
def admin_panel():
    return Response(ADMIN_PANEL_HTML, mimetype="text/html")

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

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
