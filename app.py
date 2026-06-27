"""
Geometry Home Invoice Management System v8
Multi-company | PostgreSQL (Railway) + SQLite (local) | UAE VAT
"""
import os, json, secrets, zipfile
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file, send_from_directory)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
#from db import get_db, last_insert_id, returning_id, USE_PG

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(BASE_DIR, "Invoices Archive")
UPLOAD_DIR  = os.path.join(BASE_DIR, "static", "uploads")
IMAGES_DIR  = os.path.join(BASE_DIR, "static", "images")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
@app.route("/")
def home():
    return "OK", 200

for d in [ARCHIVE_DIR, IMAGES_DIR,
          os.path.join(UPLOAD_DIR,"logos"),
          os.path.join(UPLOAD_DIR,"signatures"),
          os.path.join(UPLOAD_DIR,"stamps")]:
    os.makedirs(d, exist_ok=True)

ALLOWED = {'png','jpg','jpeg','gif','webp'}
def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED

# ── DATABASE INIT ──────────────────────────────────────────────────────────
def init_db():
    conn = get_db()

    if USE_PG:
        # PostgreSQL: CREATE TABLE IF NOT EXISTS with pg syntax
        stmts = [
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT, email TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT)""",

            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT)""",

            """CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT, address2 TEXT, address3 TEXT, address4 TEXT,
                telephone TEXT, email TEXT, trn TEXT, website TEXT,
                logo_path TEXT, stamp_path TEXT, letterhead_path TEXT,
                invoice_prefix TEXT, proforma_prefix TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""",

            """CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL, company_name TEXT,
                trn TEXT, address TEXT, country TEXT,
                telephone TEXT, email TEXT, notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""",

            """CREATE TABLE IF NOT EXISTS signatories (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL, position TEXT, image_path TEXT,
                is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""",

            """CREATE TABLE IF NOT EXISTS stamps (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL, company_id INTEGER,
                image_path TEXT,
                is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""",

            """CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_type TEXT DEFAULT 'TAX',
                company_id INTEGER,
                invoice_date TEXT NOT NULL,
                num_pages TEXT DEFAULT 'One (1)',
                purchase_order TEXT,
                client_id INTEGER,
                client_name TEXT, client_trn TEXT,
                client_address TEXT, client_country TEXT,
                client_telephone TEXT, client_email TEXT,
                bank_name TEXT, bank_iban TEXT,
                bank_account TEXT, bank_swift TEXT,
                currency TEXT DEFAULT 'AED',
                subtotal REAL DEFAULT 0,
                vat_amount REAL DEFAULT 0,
                net_payable REAL DEFAULT 0,
                amount_in_words TEXT,
                payment_terms TEXT, mode_of_payment TEXT, notes TEXT,
                signatory_id INTEGER, signatory_name TEXT, signatory_image TEXT,
                stamp_id INTEGER, stamp_name TEXT, stamp_image TEXT,
                include_signature INTEGER DEFAULT 1,
                include_stamp INTEGER DEFAULT 1,
                pdf_path TEXT, status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""",

            """CREATE TABLE IF NOT EXISTS invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                sr_no INTEGER, description TEXT,
                quantity REAL DEFAULT 1, amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0, tax_rate REAL DEFAULT 5,
                tax_amount REAL DEFAULT 0, total REAL DEFAULT 0)""",

            """CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER, username TEXT,
                action TEXT, details TEXT, ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""",
        ]
        for stmt in stmts:
            conn.execute(stmt, ())
        conn.commit()
    else:
        # SQLite
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            full_name TEXT, email TEXT, role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_login TEXT);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            address TEXT, address2 TEXT, address3 TEXT, address4 TEXT,
            telephone TEXT, email TEXT, trn TEXT, website TEXT,
            logo_path TEXT, stamp_path TEXT, letterhead_path TEXT,
            invoice_prefix TEXT, proforma_prefix TEXT,
            is_active INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, company_name TEXT, trn TEXT,
            address TEXT, country TEXT, telephone TEXT, email TEXT, notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS signatories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, position TEXT, image_path TEXT,
            is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS stamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, company_id INTEGER, image_path TEXT,
            is_active INTEGER DEFAULT 1, is_default INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            invoice_type TEXT DEFAULT 'TAX', company_id INTEGER,
            invoice_date TEXT NOT NULL, num_pages TEXT DEFAULT 'One (1)',
            purchase_order TEXT, client_id INTEGER,
            client_name TEXT, client_trn TEXT,
            client_address TEXT, client_country TEXT,
            client_telephone TEXT, client_email TEXT,
            bank_name TEXT, bank_iban TEXT, bank_account TEXT, bank_swift TEXT,
            currency TEXT DEFAULT 'AED',
            subtotal REAL DEFAULT 0, vat_amount REAL DEFAULT 0,
            net_payable REAL DEFAULT 0, amount_in_words TEXT,
            payment_terms TEXT, mode_of_payment TEXT, notes TEXT,
            signatory_id INTEGER, signatory_name TEXT, signatory_image TEXT,
            stamp_id INTEGER, stamp_name TEXT, stamp_image TEXT,
            include_signature INTEGER DEFAULT 1, include_stamp INTEGER DEFAULT 1,
            pdf_path TEXT, status TEXT DEFAULT 'active',
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL, sr_no INTEGER,
            description TEXT, quantity REAL DEFAULT 1, amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0, tax_rate REAL DEFAULT 5,
            tax_amount REAL DEFAULT 0, total REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, username TEXT,
            action TEXT, details TEXT, ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        # Safe column migrations for existing DBs
        for col in ['address2','address3','address4']:
            try:
                conn.execute(f"ALTER TABLE companies ADD COLUMN {col} TEXT DEFAULT ''", ())
            except Exception:
                pass
        conn.commit()

    # Seed default settings
    defaults = {
        'bank_name':'WIO BUSINESS',
        'bank_iban':'AE430860000009466073611',
        'bank_account':'9466073611',
        'bank_swift':'WIOBAEADXXX',
        'currency':'AED',
        'logo_path':'uploads/logos/GH_LOGO.jpg',
        'footer_path':'images/gh_footer_AE.png',
        'default_payment_terms':'100% Advance Payment',
        'default_mode_of_payment':'Bank Transfer',
        'default_vat_rate':'5',
        'default_company_id':'1',
    }
    for k, v in defaults.items():
        if USE_PG:
            conn.execute("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO NOTHING", (k,v))
        else:
            conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))

    # Admin user
    if USE_PG:
        row = conn.execute("SELECT id FROM users WHERE username=%s", ('admin',)).fetchone()
    else:
        row = conn.execute("SELECT id FROM users WHERE username=?", ('admin',)).fetchone()
    if not row:
        if USE_PG:
            conn.execute("INSERT INTO users(username,password_hash,full_name,role) VALUES(%s,%s,%s,%s)",
                        ('admin', generate_password_hash('admin123'), 'Administrator', 'admin'))
        else:
            conn.execute("INSERT INTO users(username,password_hash,full_name,role) VALUES(?,?,?,?)",
                        ('admin', generate_password_hash('admin123'), 'Administrator', 'admin'))

    # Seed companies
    companies_data = [
        ('GHM','Geometry Home Furniture Manufacturing L.L.C',
         'L06, L07, L08, WH Phase 3, Dubai Industrial City',
         'PO. Box: 16794,  Phone: +97145578898','','',
         '+97145578898','info@geometry-home.ae','104150505600003','www.geometry-home.ae',
         'uploads/logos/GH_LOGO.jpg','uploads/stamps/GHM_Seal_transparent.png','',
         'GHM-INV','GHM-PINV',1,1),
        ('GHT','Geometry Home for Furniture Trading Co. L.L.C',
         'Shop - GF - 11, Al Barsha Second, Art of Living Mall, Dubai',
         'PO. Box: 16794,  Phone: +97148834020','','',
         '+97148834020','info@geometry-home.ae','104150505600003','www.geometry-home.ae',
         'uploads/logos/GH_LOGO.jpg','uploads/stamps/GHT_Seal_transparent.png','',
         'GHT-INV','GHT-PINV',1,2),
        ('TRA','T R A Geometry Home Technical Services L.L.C S.O.C',
         'A25 \u2013 Hall No. 1, Al Nasr Central, Oud Metha, Dubai',
         'PO. Box: 16794,  Phone: +97145578898','','',
         '+97145578898','info@geometry-home.ae','1533428','www.geometry-home.ae',
         'uploads/logos/GH_LOGO.jpg','uploads/stamps/TRA_Seal_transparent.png','',
         'TRA-INV','TRA-PINV',1,3),
    ]
    for cd in companies_data:
        if USE_PG:
            row = conn.execute("SELECT id FROM companies WHERE code=%s", (cd[0],)).fetchone()
        else:
            row = conn.execute("SELECT id FROM companies WHERE code=?", (cd[0],)).fetchone()
        if not row:
            if USE_PG:
                conn.execute("""INSERT INTO companies(code,name,address,address2,address3,address4,
                    telephone,email,trn,website,logo_path,stamp_path,letterhead_path,
                    invoice_prefix,proforma_prefix,is_active,sort_order)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", cd)
            else:
                conn.execute("""INSERT INTO companies(code,name,address,address2,address3,address4,
                    telephone,email,trn,website,logo_path,stamp_path,letterhead_path,
                    invoice_prefix,proforma_prefix,is_active,sort_order)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", cd)

    # Default signatory
    if USE_PG:
        row = conn.execute("SELECT id FROM signatories WHERE name=%s", ('Rashid Khakimov',)).fetchone()
    else:
        row = conn.execute("SELECT id FROM signatories WHERE name=?", ('Rashid Khakimov',)).fetchone()
    if not row:
        if USE_PG:
            conn.execute("INSERT INTO signatories(name,position,image_path,is_active,is_default) VALUES(%s,%s,%s,1,1)",
                        ('Rashid Khakimov','General Manager','uploads/signatures/Rashid_Khakimov_Sign_transparent.png'))
        else:
            conn.execute("INSERT INTO signatories(name,position,image_path,is_active,is_default) VALUES(?,?,?,1,1)",
                        ('Rashid Khakimov','General Manager','uploads/signatures/Rashid_Khakimov_Sign_transparent.png'))

    # Stamps
    stamp_data = [
        ('GHM Official Seal','GHM','uploads/stamps/GHM_Seal_transparent.png',1),
        ('GHT Official Seal','GHT','uploads/stamps/GHT_Seal_transparent.png',0),
        ('TRA Seal',         'TRA','uploads/stamps/TRA_Seal_transparent.png',0),
    ]
    for sname, scode, spath, isdef in stamp_data:
        if USE_PG:
            co_row = conn.execute("SELECT id FROM companies WHERE code=%s", (scode,)).fetchone()
            s_row  = conn.execute("SELECT id FROM stamps WHERE name=%s", (sname,)).fetchone()
        else:
            co_row = conn.execute("SELECT id FROM companies WHERE code=?", (scode,)).fetchone()
            s_row  = conn.execute("SELECT id FROM stamps WHERE name=?", (sname,)).fetchone()
        if co_row and not s_row:
            co_id = co_row['id']
            if USE_PG:
                conn.execute("INSERT INTO stamps(name,company_id,image_path,is_active,is_default) VALUES(%s,%s,%s,1,%s)",
                            (sname, co_id, spath, isdef))
            else:
                conn.execute("INSERT INTO stamps(name,company_id,image_path,is_active,is_default) VALUES(?,?,?,1,?)",
                            (sname, co_id, spath, isdef))

    conn.commit()
    conn.close()

# ── HELPERS ────────────────────────────────────────────────────────────────
def gset(key, default=''):
    conn = get_db()
    if USE_PG:
        r = conn.execute("SELECT value FROM settings WHERE key=%s", (key,)).fetchone()
    else:
        r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return r['value'] if r else default

def gall():
    conn = get_db()
    rows = conn.execute("SELECT key,value FROM settings", ()).fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def sset(key, value):
    conn = get_db()
    if USE_PG:
        conn.execute("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value", (key, value))
    else:
        conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
    conn.commit()
    conn.close()

def get_companies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order,code", ()).fetchall()
    conn.close()
    return rows

def get_company(cid):
    conn = get_db()
    if USE_PG:
        row = conn.execute("SELECT * FROM companies WHERE id=%s", (cid,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM companies WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def audit(action, details=''):
    if 'user_id' in session:
        conn = get_db()
        if USE_PG:
            conn.execute("INSERT INTO audit_logs(user_id,username,action,details,ip_address) VALUES(%s,%s,%s,%s,%s)",
                        (session['user_id'], session.get('username'), action, details, request.remote_addr))
        else:
            conn.execute("INSERT INTO audit_logs(user_id,username,action,details,ip_address) VALUES(?,?,?,?,?)",
                        (session['user_id'], session.get('username'), action, details, request.remote_addr))
        conn.commit()
        conn.close()

def next_inv_num(company_id, inv_type='TAX'):
    conn = get_db()
    if USE_PG:
        co = conn.execute("SELECT * FROM companies WHERE id=%s", (company_id,)).fetchone()
        row = conn.execute(
            "SELECT invoice_number FROM invoices WHERE company_id=%s AND invoice_type=%s ORDER BY id DESC LIMIT 1",
            (company_id, inv_type)).fetchone()
    else:
        co = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        row = conn.execute(
            "SELECT invoice_number FROM invoices WHERE company_id=? AND invoice_type=? ORDER BY id DESC LIMIT 1",
            (company_id, inv_type)).fetchone()
    conn.close()
    year = datetime.now().year
    prefix = co['invoice_prefix'] if inv_type == 'TAX' else co['proforma_prefix']
    if row:
        try: num = int(row['invoice_number'].split('-')[-1]) + 1
        except: num = 1
    else:
        num = 1
    return f"{prefix}-{year}-{num:04d}"

def n2w(amount):
    if amount is None: return ''
    try: amount = float(amount)
    except: return ''
    if amount == 0: return 'Zero Dirhams Only'
    ones = ['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten',
            'Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen']
    tens_w = ['','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety']
    def sp(n):
        n = int(n)
        if n < 20: return ones[n]
        if n < 100: return tens_w[n//10] + (' ' + ones[n%10] if n%10 else '')
        if n < 1000: return ones[n//100] + ' Hundred' + (' and ' + sp(n%100) if n%100 else '')
        if n < 1000000: return sp(n//1000) + ' Thousand' + (' ' + sp(n%1000) if n%1000 else '')
        return sp(n//1000000) + ' Million' + (' ' + sp(n%1000000) if n%1000000 else '')
    aed = int(amount); fils = round((amount - aed) * 100)
    r = sp(aed) if aed else 'Zero'
    if fils: r += ' and ' + sp(fils) + ' Fils'
    return r + ' Dirhams Only'

def fmt_date(d):
    if not d: return ''
    try:
        if '-' in str(d) and len(str(d)) == 10:
            dt = datetime.strptime(str(d), '%Y-%m-%d')
            return dt.strftime('%d-%m-%Y')
    except: pass
    return str(d)

app.jinja_env.globals['fmt_date'] = fmt_date

def login_req(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*a, **k)
    return d

def admin_req(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session: return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*a, **k)
    return d



# ── AUTH ───────────────────────────────────────────────────────────────────
@app.route('/')
def index(): return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form.get('username','').strip(); p=request.form.get('password','')
        conn=get_db(); user=conn.execute("SELECT * FROM users WHERE username=? AND is_active=1",(u,)).fetchone(); conn.close()
        if user and check_password_hash(user['password_hash'],p):
            session.clear()
            session['user_id']=user['id']; session['username']=user['username']
            session['full_name']=user['full_name'] or user['username']; session['role']=user['role']
            session.permanent='remember' in request.form
            conn2=get_db(); conn2.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",(user['id'],)); conn2.commit(); conn2.close()
            audit('LOGIN'); return redirect(url_for('dashboard'))
        flash('Invalid username or password.','danger')
    return render_template('login.html', s=gall())

@app.route('/logout')
def logout(): audit('LOGOUT'); session.clear(); return redirect(url_for('login'))

@app.route('/change-password', methods=['GET','POST'])
@login_req
def change_password():
    if request.method=='POST':
        cur=request.form.get('current_password',''); nw=request.form.get('new_password',''); cn=request.form.get('confirm_password','')
        if nw!=cn: flash('Passwords do not match.','danger')
        elif len(nw)<6: flash('Minimum 6 characters.','danger')
        else:
            conn=get_db(); user=conn.execute("SELECT * FROM users WHERE id=?",(session['user_id'],)).fetchone()
            if user and check_password_hash(user['password_hash'],cur):
                conn.execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(nw),session['user_id'])); conn.commit()
                flash('Password changed.','success')
            else: flash('Current password incorrect.','danger')
            conn.close()
    return render_template('change_password.html', s=gall())

# ── DASHBOARD ──────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_req
def dashboard():
    conn=get_db()
    total_inv=conn.execute("SELECT COUNT(*) c FROM invoices WHERE status='active'").fetchone()['c']
    total_cl=conn.execute("SELECT COUNT(*) c FROM clients WHERE is_active=1").fetchone()['c']
    mo=datetime.now().strftime('%Y-%m')
    monthly=float(conn.execute("SELECT COALESCE(SUM(net_payable),0) s FROM invoices WHERE invoice_date LIKE ? AND status='active'",(f'{mo}%',)).fetchone()['s'])
    total_vat=float(conn.execute("SELECT COALESCE(SUM(vat_amount),0) s FROM invoices WHERE status='active'").fetchone()['s'])
    recent=conn.execute("SELECT i.*,c.name as co_name FROM invoices i LEFT JOIN companies c ON i.company_id=c.id WHERE i.status='active' ORDER BY i.id DESC LIMIT 10").fetchall()
    logs=conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 8").fetchall()
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    co_stats={}
    for co in companies:
        n=conn.execute("SELECT COUNT(*) c FROM invoices WHERE company_id=? AND status='active'",(co['id'],)).fetchone()['c']
        rev=float(conn.execute("SELECT COALESCE(SUM(net_payable),0) s FROM invoices WHERE company_id=? AND status='active'",(co['id'],)).fetchone()['s'])
        co_stats[co['id']]={'count':n,'revenue':rev}
    conn.close()
    return render_template('dashboard.html', s=gall(), companies=companies,
        total_inv=total_inv, total_cl=total_cl, monthly=monthly,
        total_vat=total_vat, recent=recent, logs=logs, co_stats=co_stats)

# ── INVOICES ───────────────────────────────────────────────────────────────
@app.route('/invoices')
@login_req
def invoices():
    q=request.args.get('q',''); co_id=request.args.get('co',''); inv_type=request.args.get('type','')
    conn=get_db()
    base="SELECT i.*,c.name as co_name,c.code as co_code FROM invoices i LEFT JOIN companies c ON i.company_id=c.id WHERE i.status='active'"
    params=[]
    if q: base+=" AND (i.invoice_number LIKE ? OR i.client_name LIKE ?)"; params+=[f'%{q}%',f'%{q}%']
    if co_id: base+=" AND i.company_id=?"; params.append(co_id)
    if inv_type: base+=" AND i.invoice_type=?"; params.append(inv_type)
    base+=" ORDER BY i.id DESC"
    rows=conn.execute(base,params).fetchall()
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    conn.close()
    return render_template('invoices.html', invoices=rows, q=q, co_id=co_id, inv_type=inv_type, companies=companies, s=gall())

@app.route('/invoices/new', methods=['GET','POST'])
@login_req
def new_invoice():
    s=gall(); conn=get_db()
    co_id=request.args.get('co', s.get('default_company_id','1'))
    inv_type=request.args.get('type','TAX')
    try: co_id=int(co_id)
    except: co_id=1
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    clients=conn.execute("SELECT * FROM clients WHERE is_active=1 ORDER BY name").fetchall()
    sigs=conn.execute("SELECT * FROM signatories WHERE is_active=1 ORDER BY is_default DESC,name").fetchall()
    stamps=conn.execute("SELECT * FROM stamps WHERE is_active=1 AND company_id=? ORDER BY is_default DESC,name",(co_id,)).fetchall()
    if not stamps: stamps=conn.execute("SELECT * FROM stamps WHERE is_active=1 ORDER BY is_default DESC").fetchall()
    def_sig=conn.execute("SELECT * FROM signatories WHERE is_default=1 AND is_active=1 LIMIT 1").fetchone()
    def_stamp=conn.execute("SELECT * FROM stamps WHERE is_default=1 AND is_active=1 AND company_id=? LIMIT 1",(co_id,)).fetchone()
    co=conn.execute("SELECT * FROM companies WHERE id=?",(co_id,)).fetchone()
    conn.close()
    if request.method=='POST': return _save_inv(None,s)
    return render_template('invoice_form.html', mode='new', inv=None, items=[],
        clients=clients, sigs=sigs, stamps=stamps, def_sig=def_sig, def_stamp=def_stamp,
        inv_num=next_inv_num(co_id,inv_type), s=s, companies=companies,
        selected_co_id=co_id, co=co, inv_type=inv_type)

@app.route('/invoices/<int:iid>/edit', methods=['GET','POST'])
@login_req
def edit_invoice(iid):
    s=gall(); conn=get_db()
    inv=conn.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
    if not inv: flash('Not found.','danger'); conn.close(); return redirect(url_for('invoices'))
    co_id=inv['company_id'] or 1
    items=conn.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sr_no",(iid,)).fetchall()
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    clients=conn.execute("SELECT * FROM clients WHERE is_active=1 ORDER BY name").fetchall()
    sigs=conn.execute("SELECT * FROM signatories WHERE is_active=1 ORDER BY is_default DESC,name").fetchall()
    stamps=conn.execute("SELECT * FROM stamps WHERE is_active=1 ORDER BY is_default DESC,name").fetchall()
    co=conn.execute("SELECT * FROM companies WHERE id=?",(co_id,)).fetchone()
    conn.close()
    if request.method=='POST': return _save_inv(iid,s)
    return render_template('invoice_form.html', mode='edit', inv=inv, items=items,
        clients=clients, sigs=sigs, stamps=stamps, def_sig=None, def_stamp=None,
        inv_num=inv['invoice_number'], s=s, companies=companies,
        selected_co_id=co_id, co=co, inv_type=inv['invoice_type'])

def _save_inv(iid,s):
    f=request.form; conn=get_db()
    co_id=int(f.get('company_id',1) or 1)
    inv_type=f.get('invoice_type','TAX')
    sid=f.get('signatory_id') or None; sn=''; si=''
    if sid:
        sg=conn.execute("SELECT * FROM signatories WHERE id=?",(sid,)).fetchone()
        if sg: sn=sg['name']; si=sg['image_path'] or ''
    stid=f.get('stamp_id') or None; stn=''; sti=''
    if stid:
        st=conn.execute("SELECT * FROM stamps WHERE id=?",(stid,)).fetchone()
        if st: stn=st['name']; sti=st['image_path'] or ''
    sub=float(f.get('subtotal',0) or 0)
    vat=float(f.get('vat_amount',0) or 0)
    net=float(f.get('net_payable',0) or 0)
    # Date: store as YYYY-MM-DD internally
    raw_date=f.get('invoice_date','')
    if raw_date:
        try:
            if '-' in raw_date and len(raw_date)==10:
                parts=raw_date.split('-')
                if len(parts[0])==2: raw_date=f"{parts[2]}-{parts[1]}-{parts[0]}"
        except: pass
    data={
        'invoice_number':f.get('invoice_number',''),
        'invoice_type':inv_type,
        'company_id':co_id,
        'invoice_date':raw_date,
        'num_pages':f.get('num_pages','One (1)'),
        'purchase_order':f.get('purchase_order',''),
        'client_id':f.get('client_id') or None,
        'client_name':f.get('client_name',''),
        'client_trn':f.get('client_trn',''),
        'client_address':f.get('client_address',''),
        'client_country':f.get('client_country',''),
        'client_telephone':f.get('client_telephone',''),
        'client_email':f.get('client_email',''),
        'bank_name':f.get('bank_name',s.get('bank_name','')),
        'bank_iban':f.get('bank_iban',s.get('bank_iban','')),
        'bank_account':f.get('bank_account',s.get('bank_account','')),
        'bank_swift':f.get('bank_swift',s.get('bank_swift','')),
        'currency':f.get('currency','AED'),
        'subtotal':sub,'vat_amount':vat,'net_payable':net,
        'amount_in_words':n2w(net),
        'payment_terms':f.get('payment_terms',''),
        'mode_of_payment':f.get('mode_of_payment',''),
        'notes':f.get('notes',''),
        'signatory_id':sid,'signatory_name':sn,'signatory_image':si,
        'stamp_id':stid,'stamp_name':stn,'stamp_image':sti,
        'include_signature':1 if f.get('include_signature') else 0,
        'include_stamp':1 if f.get('include_stamp') else 0,
        'created_by':session.get('user_id'),
    }
    if iid:
        _p='%s' if USE_PG else '?'
        sets=', '.join(f"{k}={_p}" for k in data if k!='created_by')
        vals=[v for k,v in data.items() if k!='created_by']+[iid]
        conn.execute(f"UPDATE invoices SET {sets},updated_at=CURRENT_TIMESTAMP WHERE id={_p}",vals)
        conn.execute("DELETE FROM invoice_items WHERE invoice_id=?",(iid,))
        lbl='INVOICE_EDITED'
    else:
        cols=','.join(data.keys()); ph=','.join('?'*len(data))
        conn.execute(f"INSERT INTO invoices({cols}) VALUES({ph})",list(data.values()))
        iid=last_insert_id(conn); lbl='INVOICE_CREATED'
    descs=request.form.getlist('description[]'); qtys=request.form.getlist('quantity[]')
    amts=request.form.getlist('amount[]'); rates=request.form.getlist('tax_rate[]')
    for i,desc in enumerate(descs):
        if not desc.strip(): continue
        qty=float(qtys[i] if i<len(qtys) else 1)
        amt=float(amts[i] if i<len(amts) else 0)
        rate=float(rates[i] if i<len(rates) else 5)
        ta=qty*amt; tx=ta*rate/100; tot=ta+tx
        conn.execute("INSERT INTO invoice_items(invoice_id,sr_no,description,quantity,amount,total_amount,tax_rate,tax_amount,total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "INSERT INTO invoice_items(invoice_id,sr_no,description,quantity,amount,total_amount,tax_rate,tax_amount,total) VALUES(?,?,?,?,?,?,?,?,?)",
                     (iid,i+1,desc,qty,amt,ta,rate,tx,tot))
    conn.commit()
    pdf=gen_pdf(iid)
    if pdf: conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?",(pdf,iid)); conn.commit()
    conn.close(); audit(lbl,data['invoice_number'])
    flash('Invoice saved successfully!','success')
    return redirect(url_for('view_invoice',iid=iid))

@app.route('/invoices/<int:iid>')
@login_req
def view_invoice(iid):
    conn=get_db()
    inv=conn.execute("SELECT i.*,c.name as co_name,c.code as co_code FROM invoices i LEFT JOIN companies c ON i.company_id=c.id WHERE i.id=?",(iid,)).fetchone()
    items=conn.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sr_no",(iid,)).fetchall()
    co=conn.execute("SELECT * FROM companies WHERE id=?",(inv['company_id'],)).fetchone() if inv else None
    conn.close()
    if not inv: flash('Not found.','danger'); return redirect(url_for('invoices'))
    return render_template('invoice_view.html', inv=inv, items=items, s=gall(), co=co)

@app.route('/invoices/<int:iid>/delete', methods=['POST'])
@login_req
def delete_invoice(iid):
    conn=get_db(); inv=conn.execute("SELECT invoice_number FROM invoices WHERE id=?",(iid,)).fetchone()
    conn.execute("UPDATE invoices SET status='deleted' WHERE id=?",(iid,)); conn.commit(); conn.close()
    if inv: audit('INVOICE_DELETED',inv['invoice_number'])
    flash('Invoice deleted.','success'); return redirect(url_for('invoices'))

@app.route('/invoices/<int:iid>/duplicate')
@login_req
def duplicate_invoice(iid):
    conn=get_db(); inv=conn.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone()
    items=conn.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sr_no",(iid,)).fetchall()
    if not inv: conn.close(); flash('Not found.','danger'); return redirect(url_for('invoices'))
    co_id=inv['company_id'] or 1; inv_type=inv['invoice_type'] or 'TAX'; nn=next_inv_num(co_id,inv_type)
    _ph = lambda n: ','.join(['%s']*n) if USE_PG else ','.join(['?']*n)
    _dup_sql = f"""INSERT INTO invoices(invoice_number,invoice_type,company_id,invoice_date,num_pages,
        purchase_order,client_id,client_name,client_trn,client_address,client_country,
        client_telephone,client_email,bank_name,bank_iban,bank_account,bank_swift,currency,
        subtotal,vat_amount,net_payable,amount_in_words,payment_terms,mode_of_payment,notes,
        signatory_id,signatory_name,signatory_image,stamp_id,stamp_name,stamp_image,
        include_signature,include_stamp,created_by)
        VALUES({_ph(34)})""" + (" RETURNING id" if USE_PG else "")
    conn.execute(_dup_sql,
        (nn,inv_type,co_id,datetime.now().strftime('%Y-%m-%d'),inv['num_pages'],inv['purchase_order'],
         inv['client_id'],inv['client_name'],inv['client_trn'],inv['client_address'],inv['client_country'],
         inv['client_telephone'],inv['client_email'],inv['bank_name'],inv['bank_iban'],inv['bank_account'],
         inv['bank_swift'],inv['currency'],inv['subtotal'],inv['vat_amount'],inv['net_payable'],
         inv['amount_in_words'],inv['payment_terms'],inv['mode_of_payment'],inv['notes'],
         inv['signatory_id'],inv['signatory_name'],inv['signatory_image'],inv['stamp_id'],
         inv['stamp_name'],inv['stamp_image'],inv['include_signature'],inv['include_stamp'],session.get('user_id')))
    nid=last_insert_id(conn)
    for item in items:
        conn.execute("INSERT INTO invoice_items(invoice_id,sr_no,description,quantity,amount,total_amount,tax_rate,tax_amount,total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)" if USE_PG else "INSERT INTO invoice_items(invoice_id,sr_no,description,quantity,amount,total_amount,tax_rate,tax_amount,total) VALUES(?,?,?,?,?,?,?,?,?)",
                     (nid,item['sr_no'],item['description'],item['quantity'],item['amount'],item['total_amount'],item['tax_rate'],item['tax_amount'],item['total']))
    conn.commit()
    pdf=gen_pdf(nid)
    if pdf: conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?",(pdf,nid)); conn.commit()
    conn.close(); audit('INVOICE_DUPLICATED',f'{inv["invoice_number"]} -> {nn}')
    flash(f'Duplicated as {nn}','success'); return redirect(url_for('edit_invoice',iid=nid))

@app.route('/invoices/<int:iid>/pdf')
@login_req
def download_pdf(iid):
    conn=get_db(); inv=conn.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone(); conn.close()
    if not inv: flash('Not found.','danger'); return redirect(url_for('invoices'))
    p=inv['pdf_path']
    if not p or not os.path.exists(p): p=gen_pdf(iid)
    if p and os.path.exists(p): return send_file(p,as_attachment=True,download_name=f"{inv['invoice_number']}.pdf")
    flash('PDF not available.','danger'); return redirect(url_for('view_invoice',iid=iid))

@app.route('/invoices/<int:iid>/preview')
@login_req
def preview_pdf(iid):
    conn=get_db(); inv=conn.execute("SELECT * FROM invoices WHERE id=?",(iid,)).fetchone(); conn.close()
    if not inv: return "Not found",404
    p=inv['pdf_path']
    if not p or not os.path.exists(p): p=gen_pdf(iid)
    if p and os.path.exists(p): return send_file(p,mimetype='application/pdf')
    return "PDF generation failed",500

# ── PDF GENERATION ─────────────────────────────────────────────────────────
def gen_pdf(iid):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                    Image as RLImg, HRFlowable, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

    conn = get_db()
    inv   = conn.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone()
    items = conn.execute(
        "SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sr_no", (iid,)).fetchall()
    conn.close()
    if not inv: return None

    s   = gall()
    co  = get_company(inv["company_id"])
    if not co: return None
    co  = dict(co)

    inv_type   = inv["invoice_type"] or "TAX"
    type_label = "PROFORMA INVOICE" if inv_type == "PROFORMA" else "TAX INVOICE"

    year     = inv["invoice_date"][:4] if inv["invoice_date"] else str(datetime.now().year)
    ydir     = os.path.join(ARCHIVE_DIR, year)
    os.makedirs(ydir, exist_ok=True)
    pdf_path = os.path.join(ydir, f"{inv['invoice_number']}.pdf")

    W, H     = A4
    SM       = 14 * mm
    TM       = 12 * mm
    FOOTER_H = 14 * mm
    FOOTER_GAP = 5 * mm
    CW       = W - 2 * SM
    content_bottom = FOOTER_H + FOOTER_GAP + 4 * mm

    BK   = colors.black
    WH   = colors.white
    DK   = colors.HexColor("#1a1a1a")
    DK2  = colors.HexColor("#2c2c2c")
    LG   = colors.HexColor("#f5f5f5")
    BGRD = colors.HexColor("#cccccc")
    HL   = colors.HexColor("#e8e8e8")
    ACC  = colors.HexColor("#c8a96e")

    def P(txt, sz=8, bold=False, align=TA_LEFT, col=BK):
        return Paragraph(str(txt or ""), ParagraphStyle("s",
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=sz, alignment=align, textColor=col,
            leading=sz * 1.35, spaceAfter=0, spaceBefore=0))

    dt = inv["invoice_date"] or ""
    try:
        if "-" in dt and len(dt) == 10:
            parts = dt.split("-")
            if len(parts[0]) == 4:
                dt = f"{parts[2]}-{parts[1]}-{parts[0]}"
    except: pass

    words_text = n2w(float(inv["net_payable"] or 0))

    logo_pdf  = os.path.join(BASE_DIR, "static", "uploads", "logos", "GH_LOGO_pdf.jpg")
    logo_main = os.path.join(BASE_DIR, "static", "uploads", "logos", "GH_LOGO.jpg")
    logo_src  = logo_pdf if os.path.exists(logo_pdf) else logo_main
    logo_img  = None
    if os.path.exists(logo_src):
        try: logo_img = RLImg(logo_src, width=33*mm, height=33*mm)
        except: pass

    footer_src = os.path.join(BASE_DIR, "static", "images", "gh_footer_AE.png")

    co_name  = co.get("name",  "")
    co_trn   = co.get("trn",   "")
    co_all_addr = [x for x in [
        co.get("address",""), co.get("address2",""),
        co.get("address3",""), co.get("address4","")
    ] if x and x.strip()]

    def on_page(canv, doc):
        canv.saveState()
        if os.path.exists(footer_src):
            canv.drawImage(footer_src, SM, FOOTER_GAP,
                           width=CW, height=FOOTER_H,
                           preserveAspectRatio=False)
        canv.restoreState()

    frame = Frame(SM, content_bottom, CW, H - TM - content_bottom,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    elems = []

    # ── LETTERHEAD ──────────────────────────────────────────────────────
    LOGO_W = 34*mm; GAP_W = 6*mm; INFO_W = CW - LOGO_W - GAP_W
    addr_rows = [P(co_name, 13, True, TA_LEFT, DK), Spacer(1, 1.5*mm)]
    for adr in co_all_addr:
        addr_rows.append(P(adr, 9, False, TA_LEFT, DK2))
    info_inner = Table([[item] for item in addr_rows], colWidths=[INFO_W])
    info_inner.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    lh = Table([[logo_img or P("GH",16,True,TA_CENTER,WH), info_inner]],
               colWidths=[LOGO_W+GAP_W, INFO_W])
    lh.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),DK),("ALIGN",(0,0),(0,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(0,-1),4),("BOTTOMPADDING",(0,0),(0,-1),4),
        ("LEFTPADDING",(0,0),(0,-1),4),("RIGHTPADDING",(0,0),(0,-1),4),
        ("LEFTPADDING",(1,0),(1,-1),8),("RIGHTPADDING",(1,0),(1,-1),0),
        ("TOPPADDING",(1,0),(1,-1),4),("BOTTOMPADDING",(1,0),(1,-1),4),
    ]))
    elems.append(lh)
    elems.append(Spacer(1,3*mm))
    elems.append(HRFlowable(width=CW, thickness=0.8, color=BGRD, spaceAfter=3*mm))

    # ── TITLE BAR ───────────────────────────────────────────────────────
    TITLE_W=CW*0.42; DET_L=28*mm; DET_C=5*mm; DET_V=CW-TITLE_W-DET_L-DET_C
    det = Table([
        [P("Invoice No",    8,False,TA_LEFT,WH),P(":",8,False,TA_CENTER,WH),P(inv["invoice_number"],         8,True,TA_LEFT,WH)],
        [P("Billing Date",  8,False,TA_LEFT,WH),P(":",8,False,TA_CENTER,WH),P(dt,                            8,False,TA_LEFT,WH)],
        [P("No. of Pages",  8,False,TA_LEFT,WH),P(":",8,False,TA_CENTER,WH),P(inv["num_pages"] or "One (1)", 8,False,TA_LEFT,WH)],
        [P("",6),P("",6),P("(Including this page)",                                                          6,False,TA_LEFT,WH)],
        [P("Purchase Order",8,False,TA_LEFT,WH),P(":",8,False,TA_CENTER,WH),P(inv["purchase_order"] or "",   8,False,TA_LEFT,WH)],
    ], colWidths=[DET_L,DET_C,DET_V])
    det.setStyle(TableStyle([
        ("TEXTCOLOR",(0,0),(-1,-1),WH),("FONTSIZE",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),4),
    ]))
    ti = Table([[P(type_label,20,True,TA_LEFT,WH)],[P(f"TRN : {co_trn}",8,False,TA_LEFT,ACC)]],
               colWidths=[TITLE_W])
    ti.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    tb = Table([[ti,det]], colWidths=[TITLE_W, CW-TITLE_W])
    tb.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DK),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(0,-1),10),("RIGHTPADDING",(0,0),(0,-1),6),
        ("LEFTPADDING",(1,0),(1,-1),6),("RIGHTPADDING",(1,0),(1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("BOX",(0,0),(-1,-1),0.5,BK),("LINEAFTER",(0,0),(0,-1),0.5,colors.HexColor("#444")),
    ]))
    elems.append(tb)
    elems.append(Spacer(1,2*mm))

    # ── CUSTOMER + BANK ─────────────────────────────────────────────────
    half=CW/2; cL=22*mm; cV=half-cL; bL=22*mm; bV=half-bL
    iban  = inv["bank_iban"]    or s.get("bank_iban","")
    acct  = str(inv["bank_account"] or s.get("bank_account",""))
    swift = inv["bank_swift"]   or s.get("bank_swift","")
    curr  = inv["currency"]     or "AED"
    bname = inv["bank_name"]    or s.get("bank_name","")
    def row(ll,lv,rl,rv): return [P(ll,7.5),P(lv,7.5),P(rl,7.5),P(rv,7.5)]
    # Truncate long company name so it fits in bank details value column
    co_name_short = co_name if len(co_name) <= 38 else co_name[:36]+"..."
    info = [
        [P("Customer Details",8,True),P(""),P("Our Bank Details",8,True),P("")],
        row("Name",   ": "+(inv["client_name"]      or ""),"Name",      ": "+co_name_short),
        row("TRN",    ": "+(inv["client_trn"]        or ""),"IBAN No",   ": "+iban),
        row("Address",": "+(inv["client_address"]    or ""),"Account No",": "+acct),
        row("Country",": "+(inv["client_country"]    or ""),"Swift Code",": "+swift),
        row("Tel No", ": "+(inv["client_telephone"]  or ""),"Currency",  ": "+curr),
        row("Email",  ": "+(inv["client_email"]      or ""),"Bank Name", ": "+bname),
    ]
    it2 = Table(info, colWidths=[cL,cV,bL,bV])
    it2.setStyle(TableStyle([
        ("FONTSIZE",(0,0),(-1,-1),7.5),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),1.5),("BOTTOMPADDING",(0,0),(-1,-1),1.5),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("FONTNAME",(0,0),(3,0),"Helvetica-Bold"),
        ("SPAN",(0,0),(1,0)),("SPAN",(2,0),(3,0)),
        ("LINEBELOW",(0,0),(1,0),0.5,BGRD),("LINEBELOW",(2,0),(3,0),0.5,BGRD),
        ("BOX",(0,0),(1,-1),0.5,BGRD),("BOX",(2,0),(3,-1),0.5,BGRD),
        ("LINEBEFORE",(2,0),(2,-1),1,BGRD),
    ]))
    elems.append(it2)
    elems.append(Spacer(1,2*mm))

    # ── ITEMS TABLE ─────────────────────────────────────────────────────
    c_sr=10*mm;c_qt=15*mm;c_am=22*mm;c_ta=22*mm;c_tr=12*mm;c_tx=19*mm;c_tt=22*mm
    c_ds=CW-c_sr-c_qt-c_am-c_ta-c_tr-c_tx-c_tt
    cws=[c_sr,c_ds,c_qt,c_am,c_ta,c_tr,c_tx,c_tt]
    def TH(t): return P(t,8,True,TA_CENTER,WH)
    hdr=[TH("Sr."),TH("Description"),TH("Qty"),TH("Amount (AED)"),
         TH("Total Amt (AED)"),TH("Tax %"),TH("Tax Amt"),TH("Total (AED)")]
    irows=[]
    for it in items:
        irows.append([
            P(str(it["sr_no"]),8,False,TA_CENTER),P(it["description"] or "",8),
            P(f"{it['quantity']:,.2f}",8,False,TA_CENTER),
            P(f"{it['amount']:,.2f}",8,False,TA_RIGHT),
            P(f"{it['total_amount']:,.2f}",8,False,TA_RIGHT),
            P(f"{it['tax_rate']:,.1f}%",8,False,TA_CENTER),
            P(f"{it['tax_amount']:,.2f}",8,False,TA_RIGHT),
            P(f"{it['total']:,.2f}",8,False,TA_RIGHT),
        ])
    # No forced empty rows - let content determine table height
    if not irows: irows.append([P("",8) for _ in range(8)])
    itbl=Table([hdr]+irows, colWidths=cws, repeatRows=1, splitByRow=1)
    itbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DK2),("TEXTCOLOR",(0,0),(-1,0),WH),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
        ("ALIGN",(0,0),(-1,0),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.5,BGRD),("ROWBACKGROUNDS",(0,1),(-1,-1),[WH,LG]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
    ]))
    elems.append(itbl)
    elems.append(Spacer(1,1.5*mm))

    # ── TOTALS ──────────────────────────────────────────────────────────
    wl=36*mm; wv=half-wl; tl=half-30*mm; tv=30*mm
    wt=Table([[P("Amount in Words (AED):",8,True)],[P(words_text,8)]], colWidths=[half])
    wt.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,BGRD),("LINEBELOW",(0,0),(0,0),0.5,BGRD),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    tr=Table([
        [P("SUB-TOTAL AMOUNT (AED)",8,True),  P(f"{inv['subtotal']:,.2f}",8,True,TA_RIGHT)],
        [P("TOTAL VAT AMOUNT (AED)",8,True),  P(f"{inv['vat_amount']:,.2f}",8,True,TA_RIGHT)],
        [P("NET PAYABLE AMOUNT (AED)",9,True),P(f"{inv['net_payable']:,.2f}",9,True,TA_RIGHT)],
    ], colWidths=[tl,tv])
    tr.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,BGRD),("LINEBELOW",(0,0),(-1,0),0.5,BGRD),
        ("LINEBELOW",(0,1),(-1,1),0.5,BGRD),("LINEAFTER",(0,0),(0,-1),0.5,BGRD),
        ("BACKGROUND",(0,2),(-1,2),HL),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    tot_row=Table([[wt,tr]], colWidths=[half,half])
    tot_row.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))

    # ── PAYMENT TERMS ───────────────────────────────────────────────────
    pr=[[P("Payment Terms & Instructions",8,True)],
        [P(f"Payment Terms  :  {inv['payment_terms'] or ''}",8)],
        [P(f"Mode of Payment  :  {inv['mode_of_payment'] or ''}",8)]]
    if inv["notes"]: pr.append([P(f"Notes  :  {inv['notes']}",8)])
    pt=Table(pr, colWidths=[CW])
    pt.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,BGRD),("LINEBELOW",(0,0),(0,0),0.5,BGRD),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))

    # ── SIGNATURE + STAMP ───────────────────────────────────────────────
    show_sig  = bool(inv["include_signature"] and inv["signatory_image"])
    show_stmp = bool(inv["include_stamp"]     and inv["stamp_image"])
    # Compact sig/stamp sizes - fits on same page as totals
    sig_w=36*mm; sig_h=16*mm; stmp_w=26*mm; stmp_h=26*mm
    sig_img=Spacer(1,sig_h); stmp_img=Spacer(1,stmp_h)
    if show_sig:
        sp=os.path.join(BASE_DIR,"static",inv["signatory_image"])
        if os.path.exists(sp):
            try: sig_img=RLImg(sp,width=sig_w,height=sig_h)
            except: pass
    if show_stmp:
        sp2=os.path.join(BASE_DIR,"static",inv["stamp_image"])
        if os.path.exists(sp2):
            try: stmp_img=RLImg(sp2,width=stmp_w,height=stmp_h)
            except: pass
    sw=CW*0.55; rw=CW-sw
    st=Table([
        [P(f"For {co_name}",8,True), P("Company Stamp",8,True,TA_CENTER) if show_stmp else P("")],
        [sig_img, stmp_img],
        [P("Authorised Signatory",7.5,True), P("")],
        [P(inv["signatory_name"] or "",7.5), P("")],
    ], colWidths=[sw,rw])
    st.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,BGRD),("LINEAFTER",(0,0),(0,-1),0.5,BGRD),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),5),
    ]))

    # KeepTogether ensures totals+terms+sig never split across pages
    elems.append(KeepTogether([
        tot_row, Spacer(1,2*mm),
        pt, Spacer(1,2.5*mm),
        st,
    ]))

    # ── BUILD ───────────────────────────────────────────────────────────
    doc=BaseDocTemplate(pdf_path, pagesize=A4,
        leftMargin=SM, rightMargin=SM,
        topMargin=TM, bottomMargin=content_bottom)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    doc.build(elems)
    return pdf_path


# ── COMPANIES CRUD ─────────────────────────────────────────────────────────
@app.route('/companies')
@admin_req
def companies():
    conn=get_db(); rows=conn.execute("SELECT * FROM companies ORDER BY sort_order,code").fetchall(); conn.close()
    return render_template('companies.html', companies=rows, s=gall())

@app.route('/companies/new', methods=['GET','POST'])
@admin_req
def new_company():
    if request.method=='POST':
        f=request.form; conn=get_db()
        logo_path='uploads/logos/GH_LOGO.jpg'; stamp_path=''; lh_path=''
        for field,subdir in [('logo','logos'),('stamp','stamps')]:
            if field in request.files:
                fi=request.files[field]
                if fi and allowed_file(fi.filename):
                    fn=secure_filename(fi.filename)
                    fi.save(os.path.join(UPLOAD_DIR,subdir,fn))
                    if field=='logo': logo_path=f'uploads/{subdir}/{fn}'
                    else: stamp_path=f'uploads/{subdir}/{fn}'
        code=f.get('code','').upper().strip()
        _coph = ','.join(['%s']*17) if USE_PG else ','.join(['?']*17)
        _co_sql = f"INSERT INTO companies(code,name,address,address2,address3,address4,telephone,email,trn,website,logo_path,stamp_path,letterhead_path,invoice_prefix,proforma_prefix,is_active,sort_order) VALUES({_coph})"
        conn.execute(_co_sql,
            (code,f.get('name'),f.get('address'),f.get('address2',''),
             f.get('address3',''),f.get('address4',''),
             f.get('telephone'),f.get('email'),
             f.get('trn'),f.get('website'),logo_path,stamp_path,lh_path,
             f.get('invoice_prefix',f'{code}-INV'),f.get('proforma_prefix',f'{code}-PINV'),
             int(f.get('sort_order',99))))
        conn.commit(); conn.close(); audit('COMPANY_ADDED',code); flash('Company added.','success')
        return redirect(url_for('companies'))
    return render_template('company_form.html', co=None, mode='new', s=gall())

@app.route('/companies/<int:cid>/edit', methods=['GET','POST'])
@admin_req
def edit_company(cid):
    conn=get_db(); co=conn.execute("SELECT * FROM companies WHERE id=?",(cid,)).fetchone()
    if request.method=='POST':
        f=request.form
        logo_path=co['logo_path']; stamp_path=co['stamp_path']
        for field,subdir in [('logo','logos'),('stamp','stamps')]:
            if field in request.files:
                fi=request.files[field]
                if fi and fi.filename and allowed_file(fi.filename):
                    fn=secure_filename(fi.filename)
                    fi.save(os.path.join(UPLOAD_DIR,subdir,fn))
                    if field=='logo': logo_path=f'uploads/{subdir}/{fn}'
                    else: stamp_path=f'uploads/{subdir}/{fn}'
        _p2='%s' if USE_PG else '?'
        _cu_sql=f"UPDATE companies SET name={_p2},address={_p2},address2={_p2},address3={_p2},address4={_p2},telephone={_p2},email={_p2},trn={_p2},website={_p2},logo_path={_p2},stamp_path={_p2},invoice_prefix={_p2},proforma_prefix={_p2},is_active={_p2},sort_order={_p2} WHERE id={_p2}"
        conn.execute(_cu_sql,
            (f.get('name'),f.get('address'),f.get('address2',''),
             f.get('address3',''),f.get('address4',''),
             f.get('telephone'),f.get('email'),
             f.get('trn'),f.get('website'),logo_path,stamp_path,
             f.get('invoice_prefix'),f.get('proforma_prefix'),
             1 if f.get('is_active') else 0,int(f.get('sort_order',99)),cid))
        conn.commit(); conn.close(); audit('COMPANY_EDITED',f.get('name')); flash('Company updated.','success')
        return redirect(url_for('companies'))
    conn.close()
    return render_template('company_form.html', co=co, mode='edit', s=gall())

@app.route('/companies/<int:cid>/delete', methods=['POST'])
@admin_req
def delete_company(cid):
    conn=get_db()
    inv_count=conn.execute("SELECT COUNT(*) c FROM invoices WHERE company_id=? AND status='active'",(cid,)).fetchone()['c']
    if inv_count>0: flash(f'Cannot delete: {inv_count} active invoices linked.','danger'); conn.close(); return redirect(url_for('companies'))
    conn.execute("DELETE FROM companies WHERE id=?",(cid,)); conn.commit(); conn.close()
    audit('COMPANY_DELETED',f'ID {cid}'); flash('Company deleted.','success'); return redirect(url_for('companies'))

@app.route('/companies/bulk-delete', methods=['POST'])
@admin_req
def bulk_delete_companies():
    ids=request.form.getlist('ids[]')
    conn=get_db()
    deleted=0
    for cid in ids:
        n=conn.execute("SELECT COUNT(*) c FROM invoices WHERE company_id=? AND status='active'",(cid,)).fetchone()['c']
        if n==0:
            conn.execute("DELETE FROM companies WHERE id=?",(cid,)); deleted+=1
    conn.commit(); conn.close()
    flash(f'Deleted {deleted} companies.','success'); return redirect(url_for('companies'))

# ── API ────────────────────────────────────────────────────────────────────
@app.route('/api/clients/search')
@login_req
def api_clients():
    q=request.args.get('q',''); conn=get_db()
    rows=conn.execute("SELECT * FROM clients WHERE is_active=1 AND (name LIKE ? OR company_name LIKE ?) LIMIT 10",(f'%{q}%',f'%{q}%')).fetchall()
    conn.close(); return jsonify([dict(r) for r in rows])

@app.route('/api/stamps/<int:company_id>')
@login_req
def api_stamps(company_id):
    conn=get_db()
    rows=conn.execute("SELECT * FROM stamps WHERE is_active=1 AND company_id=? ORDER BY is_default DESC,name",(company_id,)).fetchall()
    if not rows: rows=conn.execute("SELECT * FROM stamps WHERE is_active=1 ORDER BY is_default DESC").fetchall()
    conn.close(); return jsonify([dict(r) for r in rows])

@app.route('/api/company/<int:company_id>')
@login_req
def api_company(company_id):
    co=get_company(company_id)
    if co: return jsonify(dict(co))
    return jsonify({})

@app.route('/api/next-invoice-number')
@login_req
def api_next_inv_num():
    co_id=int(request.args.get('co_id',1))
    inv_type=request.args.get('type','TAX')
    return jsonify({'number':next_inv_num(co_id,inv_type)})

# ── CLIENTS ────────────────────────────────────────────────────────────────
@app.route('/clients')
@login_req
def clients():
    q=request.args.get('q',''); conn=get_db()
    if q: rows=conn.execute("SELECT * FROM clients WHERE is_active=1 AND (name LIKE ? OR company_name LIKE ? OR trn LIKE ?) ORDER BY name",(f'%{q}%',f'%{q}%',f'%{q}%')).fetchall()
    else: rows=conn.execute("SELECT * FROM clients WHERE is_active=1 ORDER BY name").fetchall()
    conn.close(); return render_template('clients.html', clients=rows, q=q, s=gall())

@app.route('/clients/new', methods=['GET','POST'])
@login_req
def new_client():
    if request.method=='POST':
        f=request.form; conn=get_db()
        conn.execute("INSERT INTO clients(name,company_name,trn,address,country,telephone,email,notes) VALUES(?,?,?,?,?,?,?,?)",
                     (f.get('name'),f.get('company_name'),f.get('trn'),f.get('address'),f.get('country'),f.get('telephone'),f.get('email'),f.get('notes')))
        conn.commit(); conn.close(); audit('CLIENT_ADDED',f.get('name')); flash('Client added.','success')
        return redirect(url_for('clients'))
    return render_template('client_form.html', cl=None, mode='new', s=gall())

@app.route('/clients/<int:cid>/edit', methods=['GET','POST'])
@login_req
def edit_client(cid):
    conn=get_db(); cl=conn.execute("SELECT * FROM clients WHERE id=?",(cid,)).fetchone()
    if request.method=='POST':
        f=request.form
        conn.execute("UPDATE clients SET name=?,company_name=?,trn=?,address=?,country=?,telephone=?,email=?,notes=? WHERE id=?",
                     (f.get('name'),f.get('company_name'),f.get('trn'),f.get('address'),f.get('country'),f.get('telephone'),f.get('email'),f.get('notes'),cid))
        conn.commit(); conn.close(); audit('CLIENT_EDITED',f.get('name')); flash('Updated.','success')
        return redirect(url_for('clients'))
    conn.close(); return render_template('client_form.html', cl=cl, mode='edit', s=gall())

@app.route('/clients/<int:cid>/delete', methods=['POST'])
@login_req
def delete_client(cid):
    conn=get_db(); conn.execute("UPDATE clients SET is_active=0 WHERE id=?",(cid,)); conn.commit(); conn.close()
    audit('CLIENT_DELETED',f'ID {cid}'); flash('Client archived.','success'); return redirect(url_for('clients'))

# ── SIGNATORIES & STAMPS ───────────────────────────────────────────────────
@app.route('/signatories')
@admin_req
def signatories():
    conn=get_db()
    sigs=conn.execute("SELECT * FROM signatories ORDER BY is_default DESC,name").fetchall()
    stamps=conn.execute("SELECT s.*,c.name as co_name,c.code as co_code FROM stamps s LEFT JOIN companies c ON s.company_id=c.id ORDER BY c.sort_order,s.is_default DESC,s.name").fetchall()
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    conn.close(); return render_template('signatories.html', sigs=sigs, stamps=stamps, companies=companies, s=gall())

@app.route('/signatories/add', methods=['POST'])
@admin_req
def add_signatory():
    name=request.form.get('name',''); pos=request.form.get('position','')
    isdef=1 if request.form.get('is_default') else 0; imgp=''
    if 'image' in request.files:
        fi=request.files['image']
        if fi and allowed_file(fi.filename):
            fn=secure_filename(fi.filename); fi.save(os.path.join(UPLOAD_DIR,'signatures',fn))
            imgp=f'uploads/signatures/{fn}'
    conn=get_db()
    if isdef: conn.execute("UPDATE signatories SET is_default=0")
    conn.execute("INSERT INTO signatories(name,position,image_path,is_default) VALUES(%s,%s,%s,%s)" if USE_PG else "INSERT INTO signatories(name,position,image_path,is_default) VALUES(?,?,?,?)",(name,pos,imgp,isdef))
    conn.commit(); conn.close(); audit('SIGNATORY_ADDED',name); flash('Signatory added.','success')
    return redirect(url_for('signatories'))

@app.route('/signatories/<int:sid>/delete', methods=['POST'])
@admin_req
def delete_signatory(sid):
    conn=get_db(); conn.execute("DELETE FROM signatories WHERE id=?",(sid,)); conn.commit(); conn.close()
    flash('Signatory deleted.','success'); return redirect(url_for('signatories'))

@app.route('/signatories/<int:sid>/toggle', methods=['POST'])
@admin_req
def toggle_signatory(sid):
    conn=get_db(); cur=conn.execute("SELECT is_active FROM signatories WHERE id=?",(sid,)).fetchone()
    if cur: conn.execute("UPDATE signatories SET is_active=? WHERE id=?",(0 if cur['is_active'] else 1,sid))
    conn.commit(); conn.close(); flash('Updated.','success'); return redirect(url_for('signatories'))

@app.route('/signatories/<int:sid>/set-default', methods=['POST'])
@admin_req
def set_default_sig(sid):
    conn=get_db(); conn.execute("UPDATE signatories SET is_default=0"); conn.execute("UPDATE signatories SET is_default=1 WHERE id=?",(sid,)); conn.commit(); conn.close()
    flash('Default set.','success'); return redirect(url_for('signatories'))

@app.route('/stamps/add', methods=['POST'])
@admin_req
def add_stamp():
    name=request.form.get('name',''); co_id=int(request.form.get('company_id',1))
    isdef=1 if request.form.get('is_default') else 0; imgp=''
    if 'image' in request.files:
        fi=request.files['image']
        if fi and allowed_file(fi.filename):
            fn=secure_filename(fi.filename); fi.save(os.path.join(UPLOAD_DIR,'stamps',fn))
            imgp=f'uploads/stamps/{fn}'
    conn=get_db()
    if isdef: conn.execute("UPDATE stamps SET is_default=0 WHERE company_id=?",(co_id,))
    conn.execute("INSERT INTO stamps(name,company_id,image_path,is_default) VALUES(%s,%s,%s,%s)" if USE_PG else "INSERT INTO stamps(name,company_id,image_path,is_default) VALUES(?,?,?,?)",(name,co_id,imgp,isdef))
    conn.commit(); conn.close(); audit('STAMP_ADDED',name); flash('Stamp added.','success')
    return redirect(url_for('signatories'))

@app.route('/stamps/<int:sid>/delete', methods=['POST'])
@admin_req
def delete_stamp(sid):
    conn=get_db(); conn.execute("DELETE FROM stamps WHERE id=?",(sid,)); conn.commit(); conn.close()
    flash('Stamp deleted.','success'); return redirect(url_for('signatories'))

@app.route('/stamps/<int:sid>/toggle', methods=['POST'])
@admin_req
def toggle_stamp(sid):
    conn=get_db(); cur=conn.execute("SELECT is_active FROM stamps WHERE id=?",(sid,)).fetchone()
    if cur: conn.execute("UPDATE stamps SET is_active=? WHERE id=?",(0 if cur['is_active'] else 1,sid))
    conn.commit(); conn.close(); flash('Updated.','success'); return redirect(url_for('signatories'))

@app.route('/stamps/<int:sid>/set-default', methods=['POST'])
@admin_req
def set_default_stamp(sid):
    conn=get_db()
    stmp=conn.execute("SELECT company_id FROM stamps WHERE id=?",(sid,)).fetchone()
    if stmp:
        conn.execute("UPDATE stamps SET is_default=0 WHERE company_id=?",(stmp['company_id'],))
        conn.execute("UPDATE stamps SET is_default=1 WHERE id=?",(sid,))
    conn.commit(); conn.close(); flash('Default stamp set.','success'); return redirect(url_for('signatories'))

# ── USERS ──────────────────────────────────────────────────────────────────
@app.route('/users')
@admin_req
def users():
    conn=get_db(); rows=conn.execute("SELECT * FROM users ORDER BY role,username").fetchall(); conn.close()
    return render_template('users.html', users=rows, s=gall())

@app.route('/users/new', methods=['GET','POST'])
@admin_req
def new_user():
    if request.method=='POST':
        f=request.form; conn=get_db()
        try:
            _u_sql = "INSERT INTO users(username,password_hash,full_name,email,role) VALUES(%s,%s,%s,%s,%s)" if USE_PG else "INSERT INTO users(username,password_hash,full_name,email,role) VALUES(?,?,?,?,?)"
            conn.execute(_u_sql,
                         (f.get('username'),generate_password_hash(f.get('password','')),f.get('full_name'),f.get('email'),f.get('role','user')))
            conn.commit(); audit('USER_CREATED',f.get('username')); flash('User created.','success')
        except Exception as e: flash(f'Error: {e}','danger')
        finally: conn.close()
        return redirect(url_for('users'))
    return render_template('user_form.html', u=None, mode='new', s=gall())

@app.route('/users/<int:uid>/edit', methods=['GET','POST'])
@admin_req
def edit_user(uid):
    conn=get_db(); u=conn.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if request.method=='POST':
        f=request.form
        conn.execute("UPDATE users SET full_name=?,email=?,role=?,is_active=? WHERE id=?",
                     (f.get('full_name'),f.get('email'),f.get('role'),1 if f.get('is_active') else 0,uid))
        if f.get('password'): conn.execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(f.get('password')),uid))
        conn.commit(); conn.close(); audit('USER_EDITED',f.get('full_name')); flash('Updated.','success')
        return redirect(url_for('users'))
    conn.close(); return render_template('user_form.html', u=u, mode='edit', s=gall())

@app.route('/users/<int:uid>/delete', methods=['POST'])
@admin_req
def delete_user(uid):
    if uid==session.get('user_id'): flash('Cannot delete yourself.','danger'); return redirect(url_for('users'))
    conn=get_db(); conn.execute("DELETE FROM users WHERE id=?",(uid,)); conn.commit(); conn.close()
    audit('USER_DELETED',f'ID {uid}'); flash('User deleted.','success'); return redirect(url_for('users'))

# ── SETTINGS ───────────────────────────────────────────────────────────────
@app.route('/settings', methods=['GET','POST'])
@admin_req
def company_settings():
    if request.method=='POST':
        f=request.form; conn=get_db()
        for k in ['bank_name','bank_iban','bank_account','bank_swift','currency',
                  'default_payment_terms','default_mode_of_payment','default_vat_rate','default_company_id']:
            if k in f:
                if USE_PG:
                    conn.execute("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",(k,f.get(k)))
                else:
                    conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,f.get(k)))
        if 'logo' in request.files:
            fi=request.files['logo']
            if fi and fi.filename and allowed_file(fi.filename):
                fn=secure_filename(fi.filename); fi.save(os.path.join(UPLOAD_DIR,'logos',fn))
                if USE_PG:
                    conn.execute("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",('logo_path',f'uploads/logos/{fn}'))
                else:
                    conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('logo_path',?)",(f'uploads/logos/{fn}',))
        conn.commit(); conn.close(); audit('SETTINGS_UPDATED'); flash('Settings saved.','success')
        return redirect(url_for('company_settings'))
    companies=get_companies()
    return render_template('settings.html', s=gall(), companies=companies)

# ── REPORTS ────────────────────────────────────────────────────────────────
@app.route('/reports')
@login_req
def reports():
    period=request.args.get('period','monthly'); year=request.args.get('year',str(datetime.now().year))
    month=request.args.get('month',str(datetime.now().month).zfill(2)); co_filter=request.args.get('co','')
    inv_type=request.args.get('type','')
    conn=get_db()
    base="SELECT i.*,c.name as co_name,c.code as co_code FROM invoices i LEFT JOIN companies c ON i.company_id=c.id WHERE i.status='active'"
    params=[]
    if co_filter: base+=" AND i.company_id=?"; params.append(co_filter)
    if inv_type: base+=" AND i.invoice_type=?"; params.append(inv_type)
    if period=='daily':
        today=datetime.now().strftime('%Y-%m-%d'); base+=" AND i.invoice_date=?"; params.append(today)
    elif period=='weekly':
        wa=(datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d'); base+=" AND i.invoice_date>=?"; params.append(wa)
    elif period=='monthly': base+=" AND i.invoice_date LIKE ?"; params.append(f'{year}-{month}%')
    elif period=='quarterly':
        q=(int(month)-1)//3; months=[f'{year}-{str(q*3+i+1).zfill(2)}%' for i in range(3)]
        base+=" AND (i.invoice_date LIKE ? OR i.invoice_date LIKE ? OR i.invoice_date LIKE ?)"; params+=months
    else: base+=" AND i.invoice_date LIKE ?"; params.append(f'{year}%')
    rows=conn.execute(base+" ORDER BY i.invoice_date DESC",params).fetchall()
    total_sales=sum(r['net_payable'] for r in rows); total_vat=sum(r['vat_amount'] for r in rows)
    chart_data=[]
    for m in range(1,13):
        ms=str(m).zfill(2)
        qry="SELECT COALESCE(SUM(net_payable),0) s FROM invoices WHERE status='active' AND invoice_date LIKE ?"
        qp=[f'{year}-{ms}%']
        if co_filter: qry+=" AND company_id=?"; qp.append(co_filter)
        chart_data.append(float(conn.execute(qry,qp).fetchone()['s']))
    companies=conn.execute("SELECT * FROM companies WHERE is_active=1 ORDER BY sort_order").fetchall()
    conn.close()
    return render_template('reports.html', invoices=rows, total_sales=total_sales, total_vat=total_vat,
        period=period, year=year, month=month, chart_data=json.dumps(chart_data),
        s=gall(), companies=companies, co_filter=co_filter, inv_type=inv_type)

@app.route('/audit-log')
@admin_req
def audit_log():
    conn=get_db(); logs=conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 500").fetchall(); conn.close()
    return render_template('audit_log.html', logs=logs, s=gall())

@app.route('/backup')
@admin_req
def backup():
    ts=datetime.now().strftime('%Y%m%d_%H%M%S'); bd=os.path.join(BASE_DIR,'backups'); os.makedirs(bd,exist_ok=True)
    bp=os.path.join(bd,f'backup_{ts}.zip')
    with zipfile.ZipFile(bp,'w',zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_PATH,'geometry_home.db')
        for root,dirs,files in os.walk(UPLOAD_DIR):
            for fn in files: fp=os.path.join(root,fn); zf.write(fp,os.path.relpath(fp,BASE_DIR))
    audit('BACKUP_CREATED',f'backup_{ts}.zip')
    return send_file(bp,as_attachment=True,download_name=f'backup_{ts}.zip')

@app.route('/archive')
@login_req
def archive():
    years=[]
    if os.path.exists(ARCHIVE_DIR):
        for y in sorted(os.listdir(ARCHIVE_DIR),reverse=True):
            yd=os.path.join(ARCHIVE_DIR,y)
            if os.path.isdir(yd):
                fls=sorted(os.listdir(yd),reverse=True)
                years.append({'year':y,'files':fls,'count':len(fls)})
    return render_template('archive.html', years=years, archive_dir=ARCHIVE_DIR, s=gall())

@app.route('/archive/<year>/<fn>')
@login_req
def dl_archive(year,fn):
    return send_from_directory(os.path.join(ARCHIVE_DIR,year),fn,as_attachment=True)

if __name__=='__main__':
    init_db()
    print("="*55)
    print("  Geometry Home Invoice System | http://localhost:5000")
    print("  Login: admin / admin123")
    print("="*55)
    app.run(debug=False,host='0.0.0.0',port=5000)
