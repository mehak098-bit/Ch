from flask import Flask, render_template_string, jsonify, redirect
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, 
    RateLimitError, 
    ChallengeRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes
)
import threading
import time
import random
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================
#  CONFIGURATION
# ==========================================
USERNAME = "hey_abhi_9292"
PASSWORD = "8082119076"
REEL_URL = "https://www.instagram.com/reel/DV5XgV0jkrD/"

BASE_COMMENT = "I am winner"
COMMENTS_PER_BURST = 8
BURST_REST_MIN = 15
BURST_REST_MAX = 45
COMMENT_DELAY_MIN = 2
COMMENT_DELAY_MAX = 5

# ==========================================
#  SMART COMMENT GENERATOR
# ==========================================
class CommentGen:
    EMOJIS = ['🔥','💯','⚡','✨','🏆','👑','💪','🚀','🎯','🥇',
              '😎','🤩','🙌','👏','🎉','💥','⭐','🌟','💫','🤘']
    
    TEXTS = [
        "I am winner", "I'm winner", "i am winner",
        "I AM WINNER", "I am a winner", "Winner here",
        "I am the winner", "Im winner", "I am winnerr",
        "I am winner bro", "Yes I am winner",
        "I'm the winner", "winner is me",
        "I am Winner", "i Am Winner", "I m winner",
    ]
    
    INVISIBLE = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff']
    
    @staticmethod
    def make():
        text = random.choice(CommentGen.TEXTS)
        e1 = random.choice(CommentGen.EMOJIS)
        e2 = random.choice(CommentGen.EMOJIS)
        inv = random.choice(CommentGen.INVISIBLE)
        
        method = random.randint(1, 10)
        
        if method == 1:
            return f"{e1} {text} {e2}"
        elif method == 2:
            return f"{text} {e1}"
        elif method == 3:
            return f"{e1}{e2} {text}"
        elif method == 4:
            return f"{text}{inv}{e1}"
        elif method == 5:
            return f"{inv}{text} {e1}{e2}"
        elif method == 6:
            dots = random.choice(['.', '..', '...', '!', '!!'])
            return f"{text}{dots} {e1}"
        elif method == 7:
            result = ''
            for ch in text:
                result += ch.upper() if random.random() > 0.5 else ch.lower()
            return f"{result} {e1}"
        elif method == 8:
            prefix = random.choice(['Yes', 'Bro', 'Yeah', 'Yo', ''])
            return f"{prefix} {text} {e1}".strip()
        elif method == 9:
            return f"{e1}{inv}{text}{inv}{e2}"
        else:
            num = random.randint(1, 99)
            return f"{text} {e1} #{num}"


# ==========================================
#  BOT ENGINE
# ==========================================
class Bot:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [2, 5]
        
        self.running = False
        self.logged_in = False
        self.media_id = None
        self.thread = None
        self.init_done = False
        
        self.stats = {
            "success": 0,
            "failed": 0,
            "total": 0,
            "status": "⏹️ STOPPED",
            "last_comment": "-",
            "last_error": "-",
            "started_at": "-",
            "speed": "0/min",
            "burst": 0,
        }
    
    def do_login(self):
        try:
            self.stats["status"] = "🔐 LOGGING IN..."
            print(f"[🔐] Logging in as @{USERNAME}")
            
            session_file = f"session_{USERNAME}.json"
            
            if os.path.exists(session_file):
                try:
                    print("[📂] Loading saved session...")
                    self.cl.load_settings(session_file)
                    self.cl.login(USERNAME, PASSWORD)
                    self.cl.get_timeline_feed()
                    print("[✅] Session loaded!")
                except Exception as e:
                    print(f"[⚠️] Session expired: {e}")
                    print("[🔄] Fresh login...")
                    os.remove(session_file)
                    self.cl = Client()
                    self.cl.delay_range = [2, 5]
                    self.cl.login(USERNAME, PASSWORD)
            else:
                print("[🆕] Fresh login...")
                self.cl.login(USERNAME, PASSWORD)
            
            # Save session
            self.cl.dump_settings(session_file)
            print("[💾] Session saved!")
            
            # Get media ID
            print(f"[🎬] Loading reel...")
            media_pk = self.cl.media_pk_from_url(REEL_URL)
            self.media_id = media_pk
            print(f"[✅] Reel loaded! Media PK: {media_pk}")
            
            self.logged_in = True
            self.stats["status"] = "✅ LOGGED IN - Ready"
            self.stats["last_error"] = "-"
            return True
            
        except ChallengeRequired as e:
            self.stats["status"] = "⚠️ CHALLENGE REQUIRED"
            self.stats["last_error"] = "Instagram verification needed! App me jaake verify karo."
            print(f"[❌] Challenge: {e}")
            return False
            
        except Exception as e:
            self.stats["status"] = "❌ LOGIN FAILED"
            self.stats["last_error"] = str(e)[:100]
            print(f"[❌] Login error: {e}")
            return False
    
    def worker(self):
        comment_times = []
        
        while self.running:
            try:
                self.stats["burst"] += 1
                burst_count = random.randint(
                    max(3, COMMENTS_PER_BURST - 2),
                    COMMENTS_PER_BURST + 2
                )
                
                self.stats["status"] = f"🟢 RUNNING (Burst #{self.stats['burst']})"
                
                for i in range(burst_count):
                    if not self.running:
                        break
                    
                    comment_text = CommentGen.make()
                    self.stats["last_comment"] = comment_text
                    
                    try:
                        self.cl.media_comment(self.media_id, comment_text)
                        self.stats["success"] += 1
                        self.stats["last_error"] = "-"
                        comment_times.append(time.time())
                        print(f"[✅] #{self.stats['success']}: {comment_text}")
                        
                    except RateLimitError:
                        self.stats["failed"] += 1
                        wait = random.uniform(60, 120)
                        self.stats["status"] = f"⏸️ RATE LIMITED ({wait:.0f}s)"
                        self.stats["last_error"] = "Rate limited by Instagram"
                        print(f"[⏸️] Rate limit! Waiting {wait:.0f}s")
                        time.sleep(wait)
                        continue
                        
                    except FeedbackRequired:
                        self.stats["failed"] += 1
                        wait = random.uniform(300, 600)
                        self.stats["status"] = f"⚠️ FEEDBACK REQ ({wait:.0f}s)"
                        self.stats["last_error"] = "Feedback required - long rest"
                        print(f"[⚠️] Feedback required! Waiting {wait:.0f}s")
                        time.sleep(wait)
                        continue
                        
                    except PleaseWaitFewMinutes:
                        self.stats["failed"] += 1
                        wait = random.uniform(180, 300)
                        self.stats["status"] = f"⏳ WAIT ({wait:.0f}s)"
                        self.stats["last_error"] = "Please wait - cooling down"
                        print(f"[⏳] Please wait! Resting {wait:.0f}s")
                        time.sleep(wait)
                        continue
                        
                    except LoginRequired:
                        self.stats["last_error"] = "Session expired - re-login"
                        print("[🔒] Session expired, re-logging...")
                        self.do_login()
                        continue
                        
                    except Exception as e:
                        self.stats["failed"] += 1
                        err = str(e)[:80]
                        self.stats["last_error"] = err
                        print(f"[❌] Error: {err}")
                        
                        if 'block' in err.lower() or 'spam' in err.lower():
                            wait = random.uniform(300, 600)
                            self.stats["status"] = f"🚫 BLOCKED ({wait:.0f}s rest)"
                            time.sleep(wait)
                            break
                        
                        time.sleep(5)
                        continue
                    
                    self.stats["total"] += 1
                    
                    # Calculate speed
                    now = time.time()
                    comment_times = [t for t in comment_times if now - t < 60]
                    self.stats["speed"] = f"{len(comment_times)}/min"
                    
                    # Human delay between comments
                    delay = random.uniform(COMMENT_DELAY_MIN, COMMENT_DELAY_MAX)
                    if random.random() < 0.1:
                        delay += random.uniform(3, 8)
                    time.sleep(delay)
                
                # Burst rest
                if self.running:
                    rest = random.uniform(BURST_REST_MIN, BURST_REST_MAX)
                    self.stats["status"] = f"😴 RESTING ({rest:.0f}s)"
                    print(f"[😴] Burst done. Rest {rest:.0f}s")
                    time.sleep(rest)
                    
            except Exception as e:
                self.stats["last_error"] = f"Worker crash: {str(e)[:50]}"
                print(f"[💥] Worker error: {e}")
                time.sleep(10)
        
        self.stats["status"] = "⏹️ STOPPED"
    
    def start(self):
        if not self.logged_in:
            if not self.do_login():
                return False
        
        if self.running:
            return True
        
        self.running = True
        self.stats["started_at"] = datetime.now().strftime("%H:%M:%S")
        self.stats["status"] = "🟢 STARTING..."
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        self.running = False
        self.stats["status"] = "⏹️ STOPPING..."

bot = Bot()

# ==========================================
#  WEB DASHBOARD
# ==========================================

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 Insta Comment Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .box {
            max-width: 700px;
            margin: 20px auto;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        .title {
            text-align: center;
            font-size: 1.8em;
            margin-bottom: 5px;
        }
        .sub { text-align: center; opacity: 0.6; margin-bottom: 25px; font-size: 0.9em; }
        
        .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.3);
            padding: 12px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85em;
        }
        .bg-green { background: #00b894; }
        .bg-red { background: #d63031; }
        .bg-yellow { background: #fdcb6e; color: #2d3436; }
        .bg-blue { background: #0984e3; }
        .bg-purple { background: #6c5ce7; }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 18px;
            border-radius: 14px;
            text-align: center;
        }
        .card .num {
            font-size: 2.2em;
            font-weight: bold;
            color: #ffd700;
        }
        .card .lbl {
            font-size: 0.8em;
            opacity: 0.8;
            margin-top: 4px;
        }
        
        .btns {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin: 25px 0;
        }
        .btn {
            padding: 14px 35px;
            border: none;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            color: #fff;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { opacity: 0.85; transform: scale(1.03); }
        .btn-go { background: linear-gradient(135deg, #00b894, #00cec9); }
        .btn-no { background: linear-gradient(135deg, #d63031, #e17055); }
        .btn-login { background: linear-gradient(135deg, #0984e3, #6c5ce7); }
        .btn[disabled] { opacity: 0.4; cursor: not-allowed; }
        
        .info {
            background: rgba(0,0,0,0.25);
            padding: 15px;
            border-radius: 12px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.8;
        }
        .info .k { opacity: 0.6; display: inline-block; min-width: 130px; }
        .info .v { color: #ffd700; }
        .err { color: #ff7675; }
        
        .footer { text-align: center; margin-top: 20px; opacity: 0.4; font-size: 0.75em; }
        
        @media (max-width: 500px) {
            .grid { grid-template-columns: repeat(2, 1fr); }
            .btns { flex-direction: column; align-items: center; }
        }
    </style>
</head>
<body>
    <div class="box">
        <div class="title">🔥 Instagram Comment Bot</div>
        <div class="sub">Anti-Block System | Auto Refresh 5s</div>
        
        <div class="status-row">
            <span>Status:</span>
            <span class="badge 
                {% if '🟢' in status or 'RUNNING' in status %}bg-green
                {% elif '⏹' in status or 'STOP' in status %}bg-red
                {% elif '😴' in status or 'REST' in status or '⏸' in status %}bg-yellow
                {% elif '🔐' in status or 'LOGIN' in status %}bg-blue
                {% else %}bg-purple{% endif %}
            ">{{ status }}</span>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="num">{{ s }}</div>
                <div class="lbl">✅ Success</div>
            </div>
            <div class="card">
                <div class="num">{{ f }}</div>
                <div class="lbl">❌ Failed</div>
            </div>
            <div class="card">
                <div class="num">{{ t }}</div>
                <div class="lbl">📝 Total</div>
            </div>
            <div class="card">
                <div class="num">{{ spd }}</div>
                <div class="lbl">⚡ Speed</div>
            </div>
            <div class="card">
                <div class="num">{{ burst }}</div>
                <div class="lbl">🔄 Bursts</div>
            </div>
            <div class="card">
                <div class="num">{{ started }}</div>
                <div class="lbl">⏱️ Since</div>
            </div>
        </div>
        
        <div class="btns">
            <a href="/login" class="btn btn-login">🔐 LOGIN</a>
            <a href="/start" class="btn btn-go {{ 'disabled' if running else '' }}">▶️ START</a>
            <a href="/stop" class="btn btn-no {{ 'disabled' if not running else '' }}">⏹️ STOP</a>
        </div>
        
        <div class="info">
            <div><span class="k">👤 Account:</span> <span class="v">@{{ user }}</span></div>
            <div><span class="k">🎬 Reel:</span> <span class="v">{{ reel }}</span></div>
            <div><span class="k">💬 Last Comment:</span> <span class="v">{{ lc }}</span></div>
            <div><span class="k">⚠️ Last Error:</span> <span class="v err">{{ le }}</span></div>
        </div>
        
        <div class="footer">
            🛡️ Anti-Block: ON | 🔄 Text Variation: ON | 🧠 Smart Delays: ON<br>
            Page auto-refreshes every 5 seconds
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    st = bot.stats
    return render_template_string(PAGE,
        status=st["status"],
        s=st["success"],
        f=st["failed"],
        t=st["total"],
        spd=st["speed"],
        burst=st["burst"],
        started=st["started_at"],
        running=bot.running,
        user=USERNAME,
        reel=REEL_URL.split('/reel/')[-1].split('/')[0] if '/reel/' in REEL_URL else REEL_URL[-20:],
        lc=st["last_comment"],
        le=st["last_error"]
    )

@app.route('/login')
def login():
    def do():
        bot.do_login()
    threading.Thread(target=do, daemon=True).start()
    time.sleep(1)
    return redirect('/')

@app.route('/start')
def start():
    def do():
        bot.start()
    threading.Thread(target=do, daemon=True).start()
    time.sleep(1)
    return redirect('/')

@app.route('/stop')
def stop():
    bot.stop()
    return redirect('/')

@app.route('/api/stats')
def api():
    return jsonify(bot.stats)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
