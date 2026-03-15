from flask import Flask, render_template_string, jsonify
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError, ChallengeRequired
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================
# 🔐 CONFIGURATION (Pre-set)
# ==========================================
USERNAME = "hey_abhi_9292"
PASSWORD = "8082119076"
REEL_URL = "https://www.instagram.com/reel/DV5XgV0jkrD/?igsh=ODgwNmRwOGo1ZWo4"

# Comment Settings
BASE_COMMENT = "I am winner"
COMMENTS_PER_BURST = 8
BURST_DELAY_MIN = 15  # seconds between bursts
BURST_DELAY_MAX = 45
COMMENT_DELAY_MIN = 2
COMMENT_DELAY_MAX = 5

# ==========================================
# 🧠 SMART TEXT GENERATOR
# ==========================================
class CommentGenerator:
    EMOJIS = ['🔥', '💯', '⚡', '✨', '🏆', '👑', '💪', '🚀', '🎯', '🥇']
    VARIATIONS = [
        "I am winner", "I'm winner", "i am winner", "I AM WINNER",
        "I am a winner", "Winner here", "I am the winner", "Im winner",
        "I am winnerr", "I am winner bro", "Yes I am winner"
    ]
    
    @staticmethod
    def generate():
        text = random.choice(CommentGenerator.VARIATIONS)
        emoji = random.choice(CommentGenerator.EMOJIS)
        patterns = [
            f"{text} {emoji}",
            f"{emoji} {text}",
            f"{text}{emoji}",
            f"{emoji}{text} {emoji}",
            f"{text} {emoji} {random.choice(CommentGenerator.EMOJIS)}"
        ]
        return random.choice(patterns)

# ==========================================
# 🤖 INSTAGRAM BOT ENGINE
# ==========================================
class InstaBot:
    def __init__(self):
        self.client = Client()
        self.client.delay_range = [2, 5]  # Random delays
        
        self.running = False
        self.thread = None
        
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "status": "STOPPED",
            "last_comment": "-",
            "last_error": "-",
            "started_at": "-"
        }
        
        self.media_id = None
        self.logged_in = False
        
    def login(self):
        """Login with retry logic"""
        try:
            self.stats["status"] = "LOGGING IN..."
            print(f"[🔐] Logging in as {USERNAME}")
            
            # Try to load existing session
            session_file = f"{USERNAME}_session.json"
            if os.path.exists(session_file):
                try:
                    self.client.load_settings(session_file)
                    self.client.login(USERNAME, PASSWORD)
                    self.client.get_timeline_feed()  # Verify session
                    print("[✅] Session loaded successfully")
                except:
                    print("[⚠️] Session expired, fresh login...")
                    self.client.set_settings({})
                    self.client.login(USERNAME, PASSWORD)
            else:
                self.client.login(USERNAME, PASSWORD)
            
            self.client.dump_settings(session_file)
            self.logged_in = True
            self.stats["status"] = "LOGGED IN"
            
            # Extract media ID from reel URL
            media_pk = self.client.media_pk_from_url(REEL_URL)
            self.media_id = self.client.media_id(media_pk)
            print(f"[🎬] Reel loaded: {self.media_id}")
            return True
            
        except ChallengeRequired:
            self.stats["status"] = "CHALLENGE REQUIRED"
            self.stats["last_error"] = "Instagram verification needed. Check email/SMS."
            return False
        except Exception as e:
            self.stats["status"] = "LOGIN FAILED"
            self.stats["last_error"] = str(e)
            print(f"[❌] Login error: {e}")
            return False
    
    def comment_worker(self):
        """Main commenting loop"""
        while self.running:
            try:
                # Burst of comments
                for i in range(COMMENTS_PER_BURST):
                    if not self.running:
                        break
                    
                    text = CommentGenerator.generate()
                    self.stats["last_comment"] = text
                    
                    try:
                        self.client.media_comment(self.media_id, text)
                        self.stats["success"] += 1
                        self.stats["last_error"] = "-"
                        print(f"[✅] Commented: {text}")
                    except RateLimitError:
                        self.stats["last_error"] = "Rate Limited - Resting..."
                        print("[⏸️] Rate limit hit, resting 60s...")
                        time.sleep(60)
                        continue
                    except Exception as e:
                        self.stats["failed"] += 1
                        self.stats["last_error"] = str(e)[:50]
                        print(f"[❌] Error: {e}")
                        time.sleep(5)
                        continue
                    
                    self.stats["total"] += 1
                    
                    # Random delay between comments
                    delay = random.uniform(COMMENT_DELAY_MIN, COMMENT_DELAY_MAX)
                    time.sleep(delay)
                
                # Rest between bursts (anti-block)
                if self.running:
                    rest = random.uniform(BURST_DELAY_MIN, BURST_DELAY_MAX)
                    self.stats["status"] = f"RESTING ({rest:.0f}s)"
                    print(f"[😴] Burst complete. Resting {rest:.0f}s...")
                    time.sleep(rest)
                    self.stats["status"] = "RUNNING"
                    
            except Exception as e:
                self.stats["last_error"] = f"Worker error: {str(e)[:50]}"
                time.sleep(10)
        
        self.stats["status"] = "STOPPED"
    
    def start(self):
        if not self.logged_in:
            if not self.login():
                return False
        
        if self.running:
            return True
        
        self.running = True
        self.stats["started_at"] = datetime.now().strftime("%H:%M:%S")
        self.stats["status"] = "RUNNING"
        self.thread = threading.Thread(target=self.comment_worker, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        self.running = False
        self.stats["status"] = "STOPPING..."
        return True

# Global bot instance
bot = InstaBot()

# ==========================================
# 🌐 WEB INTERFACE (Render ke liye)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Comment Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 { text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; opacity: 0.8; margin-bottom: 30px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .stat-number { 
            font-size: 2em; 
            font-weight: bold; 
            margin-bottom: 5px;
            color: #ffd700;
        }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .status-bar {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .status-STOPPED { background: #ff4757; }
        .status-RUNNING { background: #2ed573; }
        .status-RESTING { background: #ffa502; }
        .status-LOGGING { background: #3742fa; }
        .btn {
            padding: 15px 40px;
            font-size: 1.1em;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
            margin: 5px;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-start { background: #2ed573; color: white; }
        .btn-stop { background: #ff4757; color: white; }
        .info-section {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .info-row { margin: 8px 0; }
        .label { opacity: 0.7; display: inline-block; width: 120px; }
        .value { color: #ffd700; }
        .refresh-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            float: right;
        }
        .error-msg { color: #ff6b6b; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 Instagram Comment Bot</h1>
        <p class="subtitle">Render Deployment Ready | Anti-Block System</p>
        
        <div class="status-bar">
            <div>
                <span class="label">Status:</span>
                <span class="status-badge status-{{ status.replace(' ', '-') }}">{{ status }}</span>
            </div>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.success }}</div>
                <div class="stat-label">✅ Success</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.failed }}</div>
                <div class="stat-label">❌ Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total }}</div>
                <div class="stat-label">📝 Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ started }}</div>
                <div class="stat-label">⏱️ Started</div>
            </div>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <form action="/start" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-start" {{ 'disabled' if running else '' }}>
                    ▶️ START ENGINE
                </button>
            </form>
            <form action="/stop" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-stop" {{ 'disabled' if not running else '' }}>
                    ⏹️ STOP
                </button>
            </form>
        </div>

        <div class="info-section">
            <div class="info-row">
                <span class="label">Account:</span>
                <span class="value">@{{ username }}</span>
            </div>
            <div class="info-row">
                <span class="label">Target Reel:</span>
                <span class="value">{{ reel_short }}</span>
            </div>
            <div class="info-row">
                <span class="label">Last Comment:</span>
                <span class="value">{{ stats.last_comment }}</span>
            </div>
            <div class="info-row">
                <span class="label">Last Error:</span>
                <span class="value error-msg">{{ stats.last_error }}</span>
            </div>
        </div>

        <p style="text-align: center; margin-top: 30px; opacity: 0.7; font-size: 0.8em;">
            💡 Auto-refresh har 5 second mein<br>
            🛡️ Anti-block: Random delays + Text variation enabled
        </p>
    </div>
    
    <script>
        setTimeout(function() { location.reload(); }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(
        HTML_TEMPLATE,
        stats=bot.stats,
        status=bot.stats["status"],
        running=bot.running,
        username=USERNAME,
        reel_short=REEL_URL.split('/')[-2] if '/' in REEL_URL else REEL_URL,
        started=bot.stats["started_at"]
    )

@app.route('/start', methods=['POST'])
def start_bot():
    success = bot.start()
    if success:
        return jsonify({"status": "started", "message": "Bot started successfully"})
    else:
        return jsonify({"status": "error", "message": bot.stats["last_error"]}), 400

@app.route('/stop', methods=['POST'])
def stop_bot():
    bot.stop()
    return jsonify({"status": "stopped"})

@app.route('/api/stats')
def api_stats():
    return jsonify(bot.stats)

# Initial login on startup
@app.before_request
def init_bot():
    if not bot.logged_in and not bot.thread:
        # Run in background so web server starts immediately
        def delayed_login():
            time.sleep(2)
            bot.login()
        threading.Thread(target=delayed_login, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
