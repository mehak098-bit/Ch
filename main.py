# ============================================
#  INSTAGRAM COMMENT BOT - PURE PYTHON
#  NO instagrapi, NO pydantic, NO Pillow
#  Sirf urllib + json + flask
# ============================================

from flask import Flask, render_template_string, redirect, jsonify
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import re
import time
import os
import threading
import ssl
import gzip
import io
import random
from datetime import datetime

app = Flask(__name__)

# ==========================================
#  CONFIG - Already Set
# ==========================================
USERNAME = "hey_abhi_9292"
PASSWORD = "8082119076"
REEL_URL = "https://www.instagram.com/reel/DV5XgV0jkrD/"
BASE_TEXT = "I am winner"

# ==========================================
#  COMMENT TEXT GENERATOR
# ==========================================
class TextGen:
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
    
    INV = ['\u200b','\u200c','\u200d','\u2060','\ufeff']
    
    @staticmethod
    def make():
        text = random.choice(TextGen.TEXTS)
        e1 = random.choice(TextGen.EMOJIS)
        e2 = random.choice(TextGen.EMOJIS)
        inv = random.choice(TextGen.INV)
        m = random.randint(1,10)
        if m==1: return f"{e1} {text} {e2}"
        elif m==2: return f"{text} {e1}"
        elif m==3: return f"{e1}{e2} {text}"
        elif m==4: return f"{text}{inv}{e1}"
        elif m==5: return f"{inv}{text} {e1}{e2}"
        elif m==6:
            d = random.choice(['.','..','...','!','!!'])
            return f"{text}{d} {e1}"
        elif m==7:
            r = ''.join(c.upper() if random.random()>0.5 else c.lower() for c in text)
            return f"{r} {e1}"
        elif m==8:
            p = random.choice(['Yes','Bro','Yeah','Yo',''])
            return f"{p} {text} {e1}".strip()
        elif m==9: return f"{e1}{inv}{text}{inv}{e2}"
        else:
            n = random.randint(1,99)
            return f"{text} {e1} #{n}"


# ==========================================
#  PURE PYTHON INSTAGRAM CLIENT
# ==========================================
class InstaAPI:
    def __init__(self):
        self.cookies = http.cookiejar.MozillaCookieJar()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPSHandler(context=ctx)
        )
        self.csrf = ''
        self.uid = ''
        self.logged_in = False
        self.ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/125.0.0.0 Safari/537.36')
    
    def _dec(self, resp):
        data = resp.read()
        if resp.headers.get('Content-Encoding','') == 'gzip':
            try: data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
            except: pass
        return data.decode('utf-8', errors='ignore')
    
    def _get(self, url, h=None):
        headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        }
        if h: headers.update(h)
        req = urllib.request.Request(url, headers=headers)
        try:
            resp = self.opener.open(req, timeout=20)
            return self._dec(resp)
        except urllib.error.HTTPError as e:
            try: return self._dec(e)
            except: return ''
        except: return ''
    
    def _post(self, url, data, h=None):
        headers = {
            'User-Agent': self.ua,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'X-CSRFToken': self.csrf,
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-Instagram-AJAX': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        if h: headers.update(h)
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            resp = self.opener.open(req, timeout=20)
            return self._dec(resp), resp.getcode()
        except urllib.error.HTTPError as e:
            try: b = self._dec(e)
            except: b = ''
            return b, e.code
        except Exception as ex:
            return str(ex), 0
    
    def _sync_csrf(self):
        for c in self.cookies:
            if c.name == 'csrftoken':
                self.csrf = c.value
    
    def login(self, user, pwd):
        """Full login flow"""
        # Step 1: Get cookies + CSRF
        self._get('https://www.instagram.com/')
        self._sync_csrf()
        time.sleep(1)
        
        self._get('https://www.instagram.com/accounts/login/')
        self._sync_csrf()
        time.sleep(1)
        
        if not self.csrf:
            r = self._get('https://www.instagram.com/data/shared_data/')
            self._sync_csrf()
            if not self.csrf and r:
                try:
                    self.csrf = json.loads(r).get('config',{}).get('csrf_token','')
                except: pass
        
        if not self.csrf:
            return False, "CSRF token nahi mila"
        
        # Step 2: Login
        ts = int(time.time())
        login_data = {
            'username': user,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{ts}:{pwd}',
            'queryParams': '{}',
            'optIntoOneTap': 'false',
            'stopDeletionNonce': '',
            'trustedDeviceRecords': '{}',
        }
        
        resp, code = self._post('https://www.instagram.com/accounts/login/ajax/', login_data)
        
        if not resp:
            return False, f"Empty response (HTTP {code})"
        
        if resp.strip().startswith('<'):
            return False, "HTML response - Instagram blocking"
        
        try:
            result = json.loads(resp)
        except:
            return False, f"Invalid JSON: {resp[:100]}"
        
        self._sync_csrf()
        
        if result.get('authenticated'):
            self.logged_in = True
            self.uid = str(result.get('userId',''))
            return True, "Login successful!"
        
        if result.get('two_factor_required'):
            return False, "2FA required - browser se session ID lo"
        
        if result.get('checkpoint_url'):
            return False, "Checkpoint - Instagram app me verify karo"
        
        msg = result.get('message', str(result)[:100])
        return False, f"Login failed: {msg}"
    
    def login_session_id(self, sid):
        """Login using session ID from browser"""
        ck = http.cookiejar.Cookie(
            version=0, name='sessionid', value=sid,
            port=None, port_specified=False,
            domain='.instagram.com', domain_specified=True,
            domain_initial_dot=True, path='/', path_specified=True,
            secure=True, expires=int(time.time())+86400*90,
            discard=False, comment=None, comment_url=None,
            rest={'HttpOnly': None}, rfc2109=False
        )
        self.cookies.set_cookie(ck)
        
        self._get('https://www.instagram.com/')
        self._sync_csrf()
        time.sleep(1)
        
        # Verify
        r = self._get('https://www.instagram.com/api/v1/accounts/edit/web_form_data/', {
            'X-CSRFToken': self.csrf,
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
        })
        
        if r and 'form_data' in r:
            self.logged_in = True
            try:
                self.uid = json.loads(r).get('form_data',{}).get('username','')
            except: pass
            return True, "Session ID login successful!"
        
        return False, "Session ID invalid/expired"
    
    def comment(self, media_id, text):
        """Post a comment"""
        self._sync_csrf()
        
        # Try endpoint 1
        url1 = f'https://www.instagram.com/api/v1/web/comments/{media_id}/add/'
        resp, code = self._post(url1, {'comment_text': text})
        
        # If empty try endpoint 2
        if not resp or resp.strip() == '':
            url2 = f'https://www.instagram.com/web/comments/{media_id}/add/'
            resp, code = self._post(url2, {'comment_text': text})
        
        if not resp:
            return False, f"Empty (HTTP {code})", code
        
        if resp.strip().startswith('<'):
            return False, "Session expired", code
        
        try:
            r = json.loads(resp)
        except:
            if '"status":"ok"' in resp:
                return True, "OK", 200
            return False, f"Parse err: {resp[:60]}", code
        
        if r.get('status') == 'ok':
            return True, "OK", 200
        
        return False, r.get('message', str(r)[:60]), code


# ==========================================
#  URL → MEDIA ID
# ==========================================
def url_to_media_id(url):
    patterns = [
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reels/([A-Za-z0-9_-]+)',
    ]
    sc = None
    for p in patterns:
        m = re.search(p, url)
        if m:
            sc = m.group(1)
            break
    if not sc:
        return None, None
    
    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    mid = 0
    for ch in sc:
        mid = mid * 64 + alpha.index(ch)
    return str(mid), sc


# ==========================================
#  BOT ENGINE
# ==========================================
class Bot:
    def __init__(self):
        self.api = InstaAPI()
        self.running = False
        self.thread = None
        self.media_id = None
        self.shortcode = None
        self.session_id_mode = False
        
        self.s = 0    # success
        self.f = 0    # failed
        self.t = 0    # total
        self.burst = 0
        self.status = "⏹️ STOPPED"
        self.last_c = "-"
        self.last_e = "-"
        self.started = "-"
        self.speed = "0/min"
        self.times = []
    
    def do_login(self):
        self.status = "🔐 LOGGING IN..."
        print(f"[🔐] Login attempt: @{USERNAME}")
        
        ok, msg = self.api.login(USERNAME, PASSWORD)
        
        if ok:
            self.status = "✅ LOGGED IN"
            self.last_e = "-"
            print(f"[✅] {msg}")
            
            # Get media ID
            mid, sc = url_to_media_id(REEL_URL)
            if mid:
                self.media_id = mid
                self.shortcode = sc
                print(f"[🎬] Reel: {sc} → {mid}")
                return True
            else:
                self.status = "❌ INVALID REEL URL"
                self.last_e = "Reel URL galat hai"
                return False
        else:
            self.status = "❌ LOGIN FAILED"
            self.last_e = msg
            print(f"[❌] {msg}")
            
            if 'checkpoint' in msg.lower() or '2fa' in msg.lower():
                self.status = "⚠️ NEED SESSION ID"
                self.last_e = "Password login blocked. Session ID use karo (page pe guide hai)"
            
            return False
    
    def do_session_login(self, sid):
        self.status = "🔐 SESSION LOGIN..."
        self.api = InstaAPI()
        
        ok, msg = self.api.login_session_id(sid)
        if ok:
            self.status = "✅ LOGGED IN (Session)"
            self.last_e = "-"
            self.session_id_mode = True
            
            mid, sc = url_to_media_id(REEL_URL)
            if mid:
                self.media_id = mid
                self.shortcode = sc
                return True
            
        self.status = "❌ SESSION FAILED"
        self.last_e = msg
        return False
    
    def worker(self):
        while self.running:
            try:
                self.burst += 1
                bc = random.randint(5, 10)
                self.status = f"🟢 RUNNING (Burst #{self.burst})"
                
                for i in range(bc):
                    if not self.running:
                        break
                    
                    txt = TextGen.make()
                    self.last_c = txt
                    
                    try:
                        ok, msg, code = self.api.comment(self.media_id, txt)
                        self.t += 1
                        
                        if ok:
                            self.s += 1
                            self.last_e = "-"
                            self.times.append(time.time())
                            print(f"[✅] #{self.s}: {txt}")
                        else:
                            self.f += 1
                            self.last_e = msg
                            print(f"[❌] {msg}")
                            
                            ml = msg.lower()
                            
                            if code == 429 or 'rate' in ml or 'limit' in ml or 'wait' in ml:
                                w = random.uniform(60, 120)
                                self.status = f"⏸️ RATE LIMIT ({w:.0f}s)"
                                print(f"[⏸️] Rate limit! {w:.0f}s wait")
                                time.sleep(w)
                                break
                            
                            elif 'block' in ml or 'spam' in ml or 'feedback' in ml or 'restrict' in ml:
                                w = random.uniform(300, 600)
                                self.status = f"🚫 BLOCKED ({w:.0f}s)"
                                print(f"[🚫] Blocked! {w:.0f}s rest")
                                time.sleep(w)
                                break
                            
                            elif 'login' in ml or 'session' in ml or code == 401:
                                self.status = "🔒 SESSION EXPIRED"
                                print("[🔒] Re-login...")
                                self.do_login()
                                break
                            
                            else:
                                time.sleep(5)
                                continue
                    
                    except Exception as e:
                        self.f += 1
                        self.t += 1
                        self.last_e = str(e)[:60]
                        time.sleep(5)
                    
                    # Speed calc
                    now = time.time()
                    self.times = [x for x in self.times if now - x < 60]
                    self.speed = f"{len(self.times)}/min"
                    
                    # Human delay
                    d = random.uniform(2, 5)
                    if random.random() < 0.1:
                        d += random.uniform(3, 8)
                    time.sleep(d)
                
                # Burst rest
                if self.running:
                    rest = random.uniform(15, 45)
                    self.status = f"😴 REST ({rest:.0f}s)"
                    print(f"[😴] Rest {rest:.0f}s")
                    time.sleep(rest)
                    
            except Exception as e:
                self.last_e = str(e)[:60]
                time.sleep(10)
        
        self.status = "⏹️ STOPPED"
    
    def start(self):
        if not self.api.logged_in:
            if not self.do_login():
                return False
        if self.running:
            return True
        self.running = True
        self.started = datetime.now().strftime("%H:%M:%S")
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        self.running = False

bot = Bot()

# ==========================================
#  WEB DASHBOARD
# ==========================================
PAGE = """<!DOCTYPE html>
<html>
<head>
<title>Comment Bot</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="5">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;min-height:100vh;padding:15px}
.box{max-width:700px;margin:15px auto;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);border-radius:18px;padding:22px;backdrop-filter:blur(10px)}
h1{text-align:center;font-size:1.6em;margin-bottom:4px}
.sub{text-align:center;opacity:.5;margin-bottom:20px;font-size:.85em}
.sr{display:flex;justify-content:space-between;align-items:center;background:rgba(0,0,0,.3);padding:10px 16px;border-radius:10px;margin-bottom:16px}
.bd{padding:5px 14px;border-radius:18px;font-weight:bold;font-size:.82em}
.bg1{background:#00b894}.bg2{background:#d63031}.bg3{background:#fdcb6e;color:#2d3436}.bg4{background:#0984e3}.bg5{background:#6c5ce7}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
.c{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.08);padding:16px;border-radius:12px;text-align:center}
.c .n{font-size:2em;font-weight:bold;color:#ffd700}
.c .l{font-size:.78em;opacity:.7;margin-top:3px}
.btns{display:flex;gap:10px;justify-content:center;margin:20px 0;flex-wrap:wrap}
.btn{padding:12px 28px;border:none;border-radius:22px;font-size:.95em;font-weight:bold;cursor:pointer;color:#fff;text-decoration:none}
.btn:hover{opacity:.85}
.b1{background:linear-gradient(135deg,#00b894,#00cec9)}
.b2{background:linear-gradient(135deg,#d63031,#e17055)}
.b3{background:linear-gradient(135deg,#0984e3,#6c5ce7)}
.info{background:rgba(0,0,0,.25);padding:14px;border-radius:10px;font-family:monospace;font-size:.82em;line-height:1.9}
.info .k{opacity:.6;display:inline-block;min-width:125px}
.info .v{color:#ffd700}.err{color:#ff7675}
.foot{text-align:center;margin-top:15px;opacity:.35;font-size:.72em}
.sid-box{background:rgba(0,0,0,.3);padding:14px;border-radius:10px;margin:16px 0}
.sid-box input{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);color:#fff;font-size:.9em;margin:8px 0}
.sid-box .guide{font-size:.75em;opacity:.6;line-height:1.6}
@media(max-width:500px){.g{grid-template-columns:repeat(2,1fr)}.btns{flex-direction:column;align-items:center}}
</style>
</head>
<body>
<div class="box">
<h1>🔥 Instagram Comment Bot</h1>
<div class="sub">Pure Python | Zero pip errors | Anti-Block</div>

<div class="sr">
<span>Status:</span>
<span class="bd {% if 'RUNNING' in st or '🟢' in st %}bg1{% elif 'STOP' in st or '⏹' in st %}bg2{% elif 'REST' in st or '😴' in st or '⏸' in st %}bg3{% elif '🔐' in st or 'LOGIN' in st %}bg4{% else %}bg5{% endif %}">{{st}}</span>
</div>

<div class="g">
<div class="c"><div class="n">{{s}}</div><div class="l">✅ Success</div></div>
<div class="c"><div class="n">{{f}}</div><div class="l">❌ Failed</div></div>
<div class="c"><div class="n">{{t}}</div><div class="l">📝 Total</div></div>
<div class="c"><div class="n">{{spd}}</div><div class="l">⚡ Speed</div></div>
<div class="c"><div class="n">{{burst}}</div><div class="l">🔄 Bursts</div></div>
<div class="c"><div class="n">{{started}}</div><div class="l">⏱️ Since</div></div>
</div>

<div class="btns">
<a href="/login" class="btn b3">🔐 LOGIN</a>
<a href="/start" class="btn b1">▶️ START</a>
<a href="/stop" class="btn b2">⏹️ STOP</a>
</div>

<div class="sid-box">
<b>🔑 Session ID Login (Agar Password Login Fail Ho):</b>
<form action="/session_login" method="POST">
<input name="sid" placeholder="Browser se Session ID paste karo..." required>
<button type="submit" class="btn b3" style="width:100%;margin-top:5px">🔐 Session ID se Login</button>
</form>
<div class="guide">
📱 <b>Session ID kaise nikale:</b><br>
1. Chrome me instagram.com kholo (logged in)<br>
2. F12 key dabao → Application tab<br>
3. Cookies → instagram.com → "sessionid" ki VALUE copy karo
</div>
</div>

<div class="info">
<div><span class="k">👤 Account:</span><span class="v">@{{user}}</span></div>
<div><span class="k">🎬 Reel:</span><span class="v">{{reel}}</span></div>
<div><span class="k">💬 Last:</span><span class="v">{{lc}}</span></div>
<div><span class="k">⚠️ Error:</span><span class="v err">{{le}}</span></div>
</div>

<div class="foot">🛡️ Anti-Block ON | 🔄 Text Variation ON | Auto-refresh 5s</div>
</div>
</body>
</html>"""

@app.route('/')
def home():
    return render_template_string(PAGE,
        st=bot.status, s=bot.s, f=bot.f, t=bot.t,
        spd=bot.speed, burst=bot.burst, started=bot.started,
        user=USERNAME, lc=bot.last_c, le=bot.last_e,
        reel=bot.shortcode or REEL_URL[-20:])

@app.route('/login')
def login():
    threading.Thread(target=bot.do_login, daemon=True).start()
    time.sleep(1)
    return redirect('/')

@app.route('/session_login', methods=['POST'])
def session_login():
    from flask import request
    sid = request.form.get('sid','').strip()
    if sid:
        threading.Thread(target=bot.do_session_login, args=(sid,), daemon=True).start()
        time.sleep(2)
    return redirect('/')

@app.route('/start')
def start():
    threading.Thread(target=bot.start, daemon=True).start()
    time.sleep(1)
    return redirect('/')

@app.route('/stop')
def stop():
    bot.stop()
    return redirect('/')

@app.route('/api/stats')
def api():
    return jsonify(status=bot.status, success=bot.s, failed=bot.f,
                   total=bot.t, speed=bot.speed, burst=bot.burst,
                   last_comment=bot.last_c, last_error=bot.last_e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
