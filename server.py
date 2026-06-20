import os
import json
import time
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
API_SECRET = os.getenv('API_SECRET', 'change_this_secret_key_in_production')
DATABASE_URL = os.getenv('DATABASE_URL')

# Rate limiting
rate_limit_store = {}
RATE_LIMIT = 30
RATE_WINDOW = 60

# ============================================
# ВСЕ 120 КЛЮЧЕЙ
# ============================================
ALL_KEYS = [
    ("SCARED-BASIC-0GRF5A4M", "BASIC"), ("SCARED-BASIC-0MVAPYIX", "BASIC"),
    ("SCARED-BASIC-0P55CST0", "BASIC"), ("SCARED-BASIC-0UPJ6X4H", "BASIC"),
    ("SCARED-BASIC-16FYFTFQ", "BASIC"), ("SCARED-BASIC-1KX1H92I", "BASIC"),
    ("SCARED-BASIC-39VA4A62", "BASIC"), ("SCARED-BASIC-3DRANVCN", "BASIC"),
    ("SCARED-BASIC-53AF32WY", "BASIC"), ("SCARED-BASIC-5TCSMO0W", "BASIC"),
    ("SCARED-BASIC-5ZX65IFA", "BASIC"), ("SCARED-BASIC-7BY9KLBA", "BASIC"),
    ("SCARED-BASIC-7F969OL7", "BASIC"), ("SCARED-BASIC-7GIU1GUY", "BASIC"),
    ("SCARED-BASIC-7TWIKDSV", "BASIC"), ("SCARED-BASIC-88050UMG", "BASIC"),
    ("SCARED-BASIC-8I0L9S1Y", "BASIC"), ("SCARED-BASIC-B6U9UEJF", "BASIC"),
    ("SCARED-BASIC-B99CKJZ0", "BASIC"), ("SCARED-BASIC-CAU78JM9", "BASIC"),
    ("SCARED-BASIC-CERGLLHO", "BASIC"), ("SCARED-BASIC-ED1AYH81", "BASIC"),
    ("SCARED-BASIC-EXFSSLHB", "BASIC"), ("SCARED-BASIC-EXGIMMN3", "BASIC"),
    ("SCARED-BASIC-FJSNY16U", "BASIC"), ("SCARED-BASIC-G2SJ4AVQ", "BASIC"),
    ("SCARED-BASIC-G94PU2YO", "BASIC"), ("SCARED-BASIC-GYLFJYWQ", "BASIC"),
    ("SCARED-BASIC-HG9LJYEW", "BASIC"), ("SCARED-BASIC-HO4I7JRF", "BASIC"),
    ("SCARED-BASIC-HYKMDOZE", "BASIC"), ("SCARED-BASIC-I0YY22MP", "BASIC"),
    ("SCARED-BASIC-I2KKGZ7Y", "BASIC"), ("SCARED-BASIC-IDU3649G", "BASIC"),
    ("SCARED-BASIC-IEAR3TKM", "BASIC"), ("SCARED-BASIC-JAP4LKQ7", "BASIC"),
    ("SCARED-BASIC-LGWYVT61", "BASIC"), ("SCARED-BASIC-MHU0TIHC", "BASIC"),
    ("SCARED-BASIC-MRJNU1PJ", "BASIC"), ("SCARED-BASIC-N5YCZ0G2", "BASIC"),
    ("SCARED-BASIC-NHQ0K4N7", "BASIC"), ("SCARED-BASIC-O4TGRRZ6", "BASIC"),
    ("SCARED-BASIC-O6GV9ZJ1", "BASIC"), ("SCARED-BASIC-P3MQPS3O", "BASIC"),
    ("SCARED-BASIC-PMZJME7A", "BASIC"), ("SCARED-BASIC-Q0XE3ZJL", "BASIC"),
    ("SCARED-BASIC-Q60ORSWJ", "BASIC"), ("SCARED-BASIC-SIY657E3", "BASIC"),
    ("SCARED-BASIC-SLSRV5EV", "BASIC"), ("SCARED-BASIC-SPHHRT5Z", "BASIC"),
    ("SCARED-BASIC-TB1YJ3KV", "BASIC"), ("SCARED-BASIC-TFVVX548", "BASIC"),
    ("SCARED-BASIC-U6GB3KOY", "BASIC"), ("SCARED-BASIC-V5Z15U46", "BASIC"),
    ("SCARED-BASIC-V9RPP3FY", "BASIC"), ("SCARED-BASIC-VV7IP3O1", "BASIC"),
    ("SCARED-BASIC-XLZQDCKM", "BASIC"), ("SCARED-BASIC-Z9Q2FXE7", "BASIC"),
    ("SCARED-BASIC-ZIMZNHJR", "BASIC"), ("SCARED-BASIC-ZT0JRIYO", "BASIC"),
    ("SCARED-PREM-01LEM9O1", "PREM"), ("SCARED-PREM-0FBM2MPP", "PREM"),
    ("SCARED-PREM-107RQOJ1", "PREM"), ("SCARED-PREM-10LN3WBH", "PREM"),
    ("SCARED-PREM-1CKMM6R7", "PREM"), ("SCARED-PREM-1MZIFYIK", "PREM"),
    ("SCARED-PREM-3027OZNN", "PREM"), ("SCARED-PREM-329P0GOA", "PREM"),
    ("SCARED-PREM-3PSYL9FS", "PREM"), ("SCARED-PREM-40YBBXCE", "PREM"),
    ("SCARED-PREM-46XTOAMS", "PREM"), ("SCARED-PREM-4BZPTGJ3", "PREM"),
    ("SCARED-PREM-4J9L0ARQ", "PREM"), ("SCARED-PREM-53HEFPAW", "PREM"),
    ("SCARED-PREM-6BVERWWU", "PREM"), ("SCARED-PREM-6HKXW9S3", "PREM"),
    ("SCARED-PREM-7C9OBUS0", "PREM"), ("SCARED-PREM-AFGB3VQI", "PREM"),
    ("SCARED-PREM-AHAA21MF", "PREM"), ("SCARED-PREM-AJH2HHRE", "PREM"),
    ("SCARED-PREM-CT055VX9", "PREM"), ("SCARED-PREM-EGGURNEY", "PREM"),
    ("SCARED-PREM-F38KD12Z", "PREM"), ("SCARED-PREM-F7U9VNZF", "PREM"),
    ("SCARED-PREM-G3HJ1UBF", "PREM"), ("SCARED-PREM-IIHRFPQV", "PREM"),
    ("SCARED-PREM-JG6G8V42", "PREM"), ("SCARED-PREM-JNCWF97A", "PREM"),
    ("SCARED-PREM-K3SP5MWO", "PREM"), ("SCARED-PREM-KEN8FDS8", "PREM"),
    ("SCARED-PREM-KGVM7TBN", "PREM"), ("SCARED-PREM-KJY3WDUE", "PREM"),
    ("SCARED-PREM-KO68N7SD", "PREM"), ("SCARED-PREM-LL2M2Q5C", "PREM"),
    ("SCARED-PREM-M8Y7FF8O", "PREM"), ("SCARED-PREM-OE53FDZ9", "PREM"),
    ("SCARED-PREM-QSI9HVC5", "PREM"), ("SCARED-PREM-QU6VA5BJ", "PREM"),
    ("SCARED-PREM-SZANYS01", "PREM"), ("SCARED-PREM-TGRWR6TF", "PREM"),
    ("SCARED-PREM-THPZLWMV", "PREM"), ("SCARED-PREM-U5VXE1KR", "PREM"),
    ("SCARED-PREM-UPFODCFH", "PREM"), ("SCARED-PREM-VASUPEW2", "PREM"),
    ("SCARED-PREM-VSKC4FV4", "PREM"), ("SCARED-PREM-VUJBV74K", "PREM"),
    ("SCARED-PREM-VXECK2LR", "PREM"), ("SCARED-PREM-W2JPAW11", "PREM"),
    ("SCARED-PREM-WLJOV9NV", "PREM"), ("SCARED-PREM-X1L9H8TS", "PREM"),
    ("SCARED-PREM-XC27B7YC", "PREM"), ("SCARED-PREM-XEG1S1OD", "PREM"),
    ("SCARED-PREM-XMT2J7HZ", "PREM"), ("SCARED-PREM-XOZ3WSIU", "PREM"),
    ("SCARED-PREM-XWQ28MKC", "PREM"), ("SCARED-PREM-YB2JXI6A", "PREM"),
    ("SCARED-PREM-YJUMV7LT", "PREM"), ("SCARED-PREM-YO2EMVKN", "PREM"),
    ("SCARED-PREM-ZR3SGYI0", "PREM"), ("SCARED-PREM-ZUVBT0RX", "PREM"),
]

# ============================================
# БАЗА ДАННЫХ
# ============================================
def get_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = psycopg2.connect(
            dbname='scaredopti',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            tier TEXT NOT NULL,
            status TEXT DEFAULT 'unused',
            hwid TEXT,
            activated_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Вставляем все ключи если их нет
    for key, tier in ALL_KEYS:
        cursor.execute('''
            INSERT INTO licenses (key, tier, status) 
            VALUES (%s, %s, 'unused')
            ON CONFLICT (key) DO NOTHING
        ''', (key, tier))
    
    cursor.close()
    conn.close()
    print(f"[OK] Database initialized with {len(ALL_KEYS)} keys")

# ============================================
# RATE LIMITING
# ============================================
def check_rate_limit(ip):
    current_time = time.time()
    if ip not in rate_limit_store:
        rate_limit_store[ip] = []
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if current_time - t < RATE_WINDOW]
    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        return False
    rate_limit_store[ip].append(current_time)
    return True

# ============================================
# ДЕКОРАТОРЫ
# ============================================
def require_api_secret(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        s = request.headers.get('X-API-Secret')
        if not s or not secrets.compare_digest(s, API_SECRET):
            return jsonify({'status': 'error', 'message': 'Invalid API secret'}), 401
        return f(*args, **kwargs)
    return decorated

# ============================================
# HTML ИНТЕРФЕЙС
# ============================================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ScaredOpti Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); 
            color: #fff; 
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { 
            text-align: center; 
            color: #667eea; 
            margin-bottom: 30px;
            font-size: 36px;
        }
        .stats { 
            display: flex; 
            gap: 20px; 
            justify-content: center; 
            flex-wrap: wrap; 
            margin-bottom: 30px; 
        }
        .stat { 
            background: rgba(102, 126, 234, 0.1); 
            padding: 25px 40px; 
            border-radius: 15px; 
            text-align: center;
            border: 1px solid rgba(102, 126, 234, 0.3);
        }
        .stat h3 { color: #888; font-size: 12px; margin-bottom: 10px; text-transform: uppercase; }
        .stat .num { font-size: 36px; font-weight: bold; color: #667eea; }
        .filters { 
            display: flex; 
            gap: 10px; 
            justify-content: center; 
            flex-wrap: wrap; 
            margin-bottom: 30px; 
        }
        button { 
            padding: 12px 24px; 
            background: rgba(102, 126, 234, 0.3); 
            border: 1px solid #667eea; 
            border-radius: 8px; 
            color: #fff; 
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        button:hover, button.active { 
            background: #667eea;
            transform: translateY(-2px);
        }
        input { 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: 1px solid rgba(102, 126, 234, 0.3); 
            background: rgba(102, 126, 234, 0.1); 
            color: #fff; 
            width: 300px;
            outline: none;
        }
        input::placeholder { color: #666; }
        .keys { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
            gap: 15px; 
        }
        .key { 
            background: rgba(102, 126, 234, 0.05); 
            padding: 20px; 
            border-radius: 12px;
            border-left: 4px solid #2ecc71;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        .key.used { border-left-color: #e74c3c; }
        .key-header { 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 12px; 
        }
        .key-code { 
            font-family: monospace; 
            font-weight: bold; 
            color: #667eea;
            font-size: 14px;
        }
        .tier { 
            padding: 4px 12px; 
            border-radius: 12px; 
            font-size: 11px; 
            background: #667eea;
            font-weight: bold;
        }
        .tier.prem { background: #e74c3c; }
        .status { 
            display: inline-block;
            padding: 5px 12px; 
            border-radius: 12px; 
            font-size: 11px;
            font-weight: bold;
            margin: 8px 0;
            text-transform: uppercase;
        }
        .status.unused { background: #2ecc71; color: #000; }
        .status.used { background: #e74c3c; color: #fff; }
        .info { 
            font-size: 12px; 
            color: #888; 
            margin: 8px 0;
        }
        .toggle { 
            width: 100%; 
            padding: 10px; 
            margin-top: 12px;
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: bold;
            transition: all 0.3s;
        }
        .toggle.to-used { 
            background: rgba(231, 76, 60, 0.3); 
            color: #e74c3c;
            border: 1px solid #e74c3c;
        }
        .toggle.to-unused { 
            background: rgba(46, 204, 113, 0.3); 
            color: #2ecc71;
            border: 1px solid #2ecc71;
        }
        .toggle:hover { transform: translateY(-2px); opacity: 0.9; }
        .error { 
            text-align: center; 
            padding: 60px; 
            color: #e74c3c;
            font-size: 18px;
        }
        .loading {
            text-align: center;
            padding: 60px;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 ScaredOpti Admin Panel</h1>
        <div class="stats">
            <div class="stat"><h3>Total</h3><div class="num" id="total">0</div></div>
            <div class="stat"><h3>Used</h3><div class="num" id="used">0</div></div>
            <div class="stat"><h3>Unused</h3><div class="num" id="unused">0</div></div>
            <div class="stat"><h3>Basic</h3><div class="num" id="basic">0</div></div>
            <div class="stat"><h3>Premium</h3><div class="num" id="prem">0</div></div>
        </div>
        <div class="filters">
            <button onclick="setFilter('all')" id="btn-all" class="active">All</button>
            <button onclick="setFilter('used')" id="btn-used">Used</button>
            <button onclick="setFilter('unused')" id="btn-unused">Unused</button>
            <button onclick="setFilter('basic')" id="btn-basic">Basic</button>
            <button onclick="setFilter('prem')" id="btn-prem">Premium</button>
            <input type="text" id="search" placeholder="Search keys..." onkeyup="render()">
        </div>
        <div id="keys" class="keys"><div class="loading">Loading keys...</div></div>
    </div>
    <script>
        let keys = [];
        let filter = 'all';

        async function load() {
            try {
                const r = await fetch('/api/keys', {
                    headers: {'X-API-Secret': '{{ api_secret }}'}
                });
                const data = await r.json();
                keys = data.keys;
                updateStats();
                render();
            } catch(e) {
                document.getElementById('keys').innerHTML = '<div class="error">Error: ' + e.message + '</div>';
            }
        }

        function updateStats() {
            document.getElementById('total').textContent = keys.length;
            document.getElementById('used').textContent = keys.filter(k => k.status === 'used').length;
            document.getElementById('unused').textContent = keys.filter(k => k.status === 'unused').length;
            document.getElementById('basic').textContent = keys.filter(k => k.tier === 'BASIC').length;
            document.getElementById('prem').textContent = keys.filter(k => k.tier === 'PREM').length;
        }

        function setFilter(f) {
            filter = f;
            document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
            document.getElementById('btn-' + f).classList.add('active');
            render();
        }

        function render() {
            const s = document.getElementById('search').value.toLowerCase();
            let filtered = keys.filter(k => {
                if (filter === 'used' && k.status !== 'used') return false;
                if (filter === 'unused' && k.status !== 'unused') return false;
                if (filter === 'basic' && k.tier !== 'BASIC') return false;
                if (filter === 'prem' && k.tier !== 'PREM') return false;
                if (s && !k.key.toLowerCase().includes(s)) return false;
                return true;
            });

            if (filtered.length === 0) {
                document.getElementById('keys').innerHTML = '<div class="error" style="color:#888;">No keys found</div>';
                return;
            }

            document.getElementById('keys').innerHTML = filtered.map(k => `
                <div class="key ${k.status}">
                    <div class="key-header">
                        <div class="key-code">${k.key}</div>
                        <div class="tier ${k.tier === 'PREM' ? 'prem' : ''}">${k.tier}</div>
                    </div>
                    <div class="status ${k.status}">${k.status}</div>
                    ${k.hwid ? '<div class="info">HWID: ' + k.hwid + '</div>' : ''}
                    ${k.activated_at ? '<div class="info">Activated: ' + new Date(k.activated_at).toLocaleString() + '</div>' : ''}
                    <button class="toggle ${k.status === 'used' ? 'to-unused' : 'to-used'}" 
                            onclick="toggle('${k.key}', '${k.status === 'used' ? 'unused' : 'used'}')">
                        ${k.status === 'used' ? 'Mark as Unused' : 'Mark as Used'}
                    </button>
                </div>
            `).join('');
        }

        async function toggle(key, status) {
            await fetch('/api/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Secret': '{{ api_secret }}'
                },
                body: JSON.stringify({key: key, status: status})
            });
            await load();
        }

        load();
    </script>
</body>
</html>
"""

# ============================================
# РОУТЫ
# ============================================
@app.route('/')
@app.route('/admin')
def home():
    return render_template_string(HTML_PAGE, api_secret=API_SECRET)

@app.route('/api/keys')
@require_api_secret
def get_keys():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT key, tier, status, hwid, activated_at, is_active FROM licenses ORDER BY tier, key')
    keys = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'status': 'ok', 'keys': keys})

@app.route('/api/update', methods=['POST'])
@require_api_secret
def update():
    data = request.get_json()
    key = data.get('key')
    status = data.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if status == 'unused':
        cursor.execute('''
            UPDATE licenses 
            SET status = 'unused', hwid = NULL, activated_at = NULL 
            WHERE key = %s
        ''', (key,))
    else:
        cursor.execute('''
            UPDATE licenses 
            SET status = 'used' 
            WHERE key = %s
        ''', (key,))
    
    cursor.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/activate', methods=['POST'])
def activate():
    # Rate limiting
    ip = request.remote_addr
    if not check_rate_limit(ip):
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429
    
    data = request.get_json()
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '').strip()
    
    if not key or not hwid:
        return jsonify({'status': 'error', 'message': 'Key and HWID required'}), 400
    
    # Проверка формата ключа
    parts = key.split('-')
    if len(parts) != 3 or parts[0] != 'SCARED' or parts[1] not in ['BASIC', 'PREM'] or len(parts[2]) != 8:
        return jsonify({'status': 'invalid', 'message': 'Invalid key format'}), 400
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Проверяем ключ
    cursor.execute('SELECT * FROM licenses WHERE key = %s', (key,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'status': 'invalid', 'message': 'Key not found'}), 404
    
    if not row['is_active']:
        cursor.close()
        conn.close()
        return jsonify({'status': 'blocked', 'message': 'Key is deactivated'}), 403
    
    tier = row['tier']
    stored_hwid = row['hwid']
    
    # Первая активация
    if row['status'] == 'unused':
        cursor.execute('''
            UPDATE licenses 
            SET status = 'used', hwid = %s, activated_at = %s 
            WHERE key = %s
        ''', (hwid, datetime.now(), key))
        cursor.close()
        conn.close()
        return jsonify({'status': 'activated', 'tier': tier, 'message': 'License activated'})
    
    # Уже активирован - проверяем HWID
    if stored_hwid and stored_hwid != hwid:
        cursor.close()
        conn.close()
        return jsonify({'status': 'blocked', 'message': 'HWID mismatch'})
    
    cursor.close()
    conn.close()
    return jsonify({'status': 'ok', 'tier': tier, 'message': 'License valid'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

# ============================================
# ЗАПУСК
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SCAREDOPTI LICENSE SERVER")
    print("="*60)
    print(f"\n  Total keys: {len(ALL_KEYS)}")
    print(f"  API Secret: {API_SECRET[:4]}...")
    print(f"  Database: {'PostgreSQL' if DATABASE_URL else 'Local'}")
    print(f"  Server: http://localhost:5000")
    print(f"  Admin:  http://localhost:5000/admin")
    print("\n" + "="*60)
    print("  Press CTRL+C to stop")
    print("="*60 + "\n")
    
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)