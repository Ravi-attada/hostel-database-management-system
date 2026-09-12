import sqlite3
import os
import calendar
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), 'hostel.db')
ADVANCE_DEFAULT = 10400.0


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id        TEXT PRIMARY KEY,
            floor     INTEGER NOT NULL,
            label     TEXT NOT NULL,
            capacity  INTEGER NOT NULL,
            room_type TEXT DEFAULT 'standard',
            custom_rent REAL DEFAULT NULL,
            custom_advance REAL DEFAULT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL,
            father_name      TEXT,
            village          TEXT,
            mandalam         TEXT,
            district         TEXT,
            college          TEXT,
            study_year       TEXT,
            branch           TEXT,
            aadhar_no        TEXT,
            phone            TEXT,
            parent_phone     TEXT,
            email            TEXT,
            room_id          TEXT NOT NULL REFERENCES rooms(id),
            join_date        TEXT NOT NULL,
            food_start_date  TEXT,
            advance_paid     REAL DEFAULT 0,
            advance_total    REAL DEFAULT 10400,
            notes            TEXT,
            is_active        INTEGER DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rent_config (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            effective_from TEXT NOT NULL,
            room_rent      REAL NOT NULL,
            food_rent      REAL NOT NULL,
            advance_amount REAL DEFAULT 10400,
            label          TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rent_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL REFERENCES tenants(id),
            rent_month TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date TEXT NOT NULL,
            payment_timestamp TEXT
        )
    ''')

    # Migrate existing tenants table columns
    existing = [row[1] for row in c.execute('PRAGMA table_info(tenants)').fetchall()]
    new_cols = {
        'father_name':    'TEXT',
        'village':        'TEXT',
        'mandalam':       'TEXT',
        'district':       'TEXT',
        'college':        'TEXT',
        'study_year':     'TEXT',
        'branch':         'TEXT',
        'aadhar_no':      'TEXT',
        'parent_phone':   'TEXT',
        'food_start_date':'TEXT',
        'advance_paid':   'REAL DEFAULT 0',
        'advance_total':  'REAL DEFAULT 10400',
    }
    for col, col_type in new_cols.items():
        if col not in existing:
            c.execute(f'ALTER TABLE tenants ADD COLUMN {col} {col_type}')

    # Seed rooms if empty
    c.execute('SELECT COUNT(*) FROM rooms')
    if c.fetchone()[0] == 0:
        _seed_rooms(c)

    # Seed rent_config if empty
    c.execute('SELECT COUNT(*) FROM rent_config')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO rent_config (effective_from,room_rent,food_rent,advance_amount,label) VALUES (?,?,?,?,?)',
                  ('2026-08-01', 2000, 3200, 10400, 'August 2026'))
        c.execute('INSERT INTO rent_config (effective_from,room_rent,food_rent,advance_amount,label) VALUES (?,?,?,?,?)',
                  ('2026-09-01', 1800, 3000, 10400, 'September 2026 onwards'))

    conn.commit()
    conn.close()


def _seed_rooms(c):
    caps = [6, 5, 6, 5, 6, 5, 6, 5, 6]
    for i, cap in enumerate(caps, 1):
        rid = f"10{i}"
        c.execute('INSERT INTO rooms VALUES (?,?,?,?,?)',
                  (rid, 1, f"Room {rid}", cap, 'standard'))
    for i, cap in enumerate(caps, 1):
        rid = f"20{i}"
        c.execute('INSERT INTO rooms VALUES (?,?,?,?,?)',
                  (rid, 2, f"Room {rid}", cap, 'standard'))
    floor3 = [
        ('308', 3, 'Kitchen (308)', 2, 'kitchen', None, None),
        ('309', 3, 'Bedroom A - AC (309)', 6, 'bedroom', 6300.0, 12600.0),
        ('310', 3, 'Bedroom B (310)', 6, 'bedroom', None, None),
        ('306', 3, 'Living Hall (306)', 10, 'hall', None, None),
    ]
    for row in floor3:
        c.execute('INSERT INTO rooms (id, floor, label, capacity, room_type, custom_rent, custom_advance) VALUES (?,?,?,?,?,?,?)', row)


# ── Room queries ─────────────────────────────────────────────────

def get_all_rooms():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM rooms ORDER BY floor, id').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rooms_by_floor(floor):
    conn = get_connection()
    rows = conn.execute('SELECT * FROM rooms WHERE floor=? ORDER BY id', (floor,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_room(room_id):
    conn = get_connection()
    row = conn.execute('SELECT * FROM rooms WHERE id=?', (room_id,)).fetchone()
    if not row:
        row = conn.execute('SELECT * FROM rent_config ORDER BY effective_from ASC LIMIT 1').fetchone()
    conn.close()
    return dict(row) if row else None


# ── Rent Config queries ───────────────────────────────────────────

def get_all_rent_configs():
    conn = get_connection()
    rows = conn.execute('SELECT * FROM rent_config ORDER BY effective_from DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_applicable_rent(ref_date_str):
    """Return rent config applicable on ref_date_str (YYYY-MM-DD)."""
    if not ref_date_str:
        ref_date_str = date.today().isoformat()
    conn = get_connection()
    row = conn.execute('''
        SELECT * FROM rent_config
        WHERE effective_from <= ?
        ORDER BY effective_from DESC
        LIMIT 1
    ''', (ref_date_str,)).fetchone()
    if not row:
        row = conn.execute('SELECT * FROM rent_config ORDER BY effective_from ASC LIMIT 1').fetchone()
    conn.close()
    return dict(row) if row else None


def add_rent_config(effective_from, room_rent, food_rent, advance_amount, label):
    conn = get_connection()
    conn.execute(
        'INSERT INTO rent_config (effective_from,room_rent,food_rent,advance_amount,label) VALUES (?,?,?,?,?)',
        (effective_from, room_rent, food_rent, advance_amount, label)
    )
    conn.commit()
    conn.close()


def delete_rent_config(config_id):
    conn = get_connection()
    conn.execute('DELETE FROM rent_config WHERE id=?', (config_id,))
    conn.commit()
    conn.close()


def calc_prorated_rent(food_start_date_str, rent_config, custom_total_rent=None):
    """
    Both room and food are pro-rated from food_start_date to end of that month.
    Returns a dict with full breakdown.
    """
    if not food_start_date_str or not rent_config:
        return None
    try:
        food_date = datetime.strptime(food_start_date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

    _, days_in_month = calendar.monthrange(food_date.year, food_date.month)
    days_charged = days_in_month - food_date.day + 1

    food_full  = float(rent_config['food_rent'])
    if custom_total_rent is not None:
        total_full = float(custom_total_rent)
        room_full = total_full - food_full
    else:
        room_full  = float(rent_config['room_rent'])
        total_full = room_full + food_full

    room_pro  = round(room_full * days_charged / days_in_month, 2)
    food_pro  = round(food_full * days_charged / days_in_month, 2)
    total_pro = round(total_full * days_charged / days_in_month, 2)

    return {
        'month_label':    food_date.strftime('%B %Y'),
        'food_start':     food_start_date_str,
        'days_in_month':  days_in_month,
        'days_charged':   days_charged,
        'room_rent_full': room_full,
        'food_rent_full': food_full,
        'total_full':     total_full,
        'room_prorated':  room_pro,
        'food_prorated':  food_pro,
        'total_prorated': total_pro,
        'config_label':   rent_config.get('label', ''),
    }


# ── Tenant queries ────────────────────────────────────────────────

def get_all_active_tenants():
    conn = get_connection()
    rows = conn.execute('''
        SELECT t.*, r.floor, r.label AS room_label
        FROM tenants t
        JOIN rooms r ON t.room_id = r.id
        WHERE t.is_active = 1
        ORDER BY r.floor, t.room_id, t.name
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tenants_by_room(room_id):
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM tenants WHERE room_id=? AND is_active=1 ORDER BY name',
        (room_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tenant(tenant_id):
    conn = get_connection()
    row = conn.execute('SELECT * FROM tenants WHERE id=?', (tenant_id,)).fetchone()
    if not row:
        row = conn.execute('SELECT * FROM rent_config ORDER BY effective_from ASC LIMIT 1').fetchone()
    conn.close()
    return dict(row) if row else None


def get_tenant_count_by_room(room_id):
    conn = get_connection()
    count = conn.execute(
        'SELECT COUNT(*) FROM tenants WHERE room_id=? AND is_active=1', (room_id,)
    ).fetchone()[0]
    conn.close()
    return count



def add_tenant(data):
    adv_paid  = float(data.get('advance_paid') or 0)
    adv_total = float(data.get('advance_total') or ADVANCE_DEFAULT)
    conn = get_connection()
    try:
        conn.execute('''
            INSERT INTO tenants
              (name, father_name, village, mandalam, district,
               college, study_year, branch, aadhar_no,
               phone, parent_phone, email,
               room_id, join_date, food_start_date,
               advance_paid, advance_total, notes, password_hash)
            VALUES (?,?,?,?,?, ?,?,?,?, ?,?,?, ?,?,?, ?,?,?,?)
        ''', (
            data['name'],           data.get('father_name',''),
            data.get('village',''), data.get('mandalam',''),
            data.get('district',''),
            data.get('college',''), data.get('study_year',''),
            data.get('branch',''),  data.get('aadhar_no',''),
            data.get('phone',''),   data.get('parent_phone',''),
            data.get('email', ''),
            data['room_id'],        data.get('join_date',''),
            data.get('food_start_date',''),
            adv_paid,               adv_total,
            data.get('notes',''), data.get('password_hash')
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise ValueError("Email already exists!")
    finally:
        conn.close()



def update_tenant(tenant_id, data):
    adv_paid  = float(data.get('advance_paid') or 0)
    adv_total = float(data.get('advance_total') or ADVANCE_DEFAULT)
    conn = get_connection()
    conn.execute('''
        UPDATE tenants SET
          name=?, father_name=?, village=?, mandalam=?, district=?,
          college=?, study_year=?, branch=?, aadhar_no=?,
          phone=?, parent_phone=?, email=?,
          room_id=?, join_date=?, food_start_date=?,
          advance_paid=?, advance_total=?, notes=?
        WHERE id=?
    ''', (
        data['name'],           data.get('father_name',''),
        data.get('village',''), data.get('mandalam',''),
        data.get('district',''),
        data.get('college',''), data.get('study_year',''),
        data.get('branch',''),  data.get('aadhar_no',''),
        data.get('phone',''),   data.get('parent_phone',''),
        data.get('email',''),
        data['room_id'],        data['join_date'],
        data.get('food_start_date',''),
        adv_paid, adv_total,
        data.get('notes',''),
        tenant_id,
    ))
    conn.commit()
    conn.close()


def deactivate_tenant(tenant_id):
    conn = get_connection()
    conn.execute('UPDATE tenants SET is_active=0 WHERE id=?', (tenant_id,))
    conn.commit()
    conn.close()


def search_tenants(query):
    conn = get_connection()
    like = f'%{query}%'
    rows = conn.execute('''
        SELECT t.*, r.floor, r.label AS room_label
        FROM tenants t
        JOIN rooms r ON t.room_id = r.id
        WHERE t.is_active = 1
          AND (t.name LIKE ? OR t.room_id LIKE ? OR t.phone LIKE ?
               OR t.college LIKE ? OR t.village LIKE ?)
        ORDER BY t.name
    ''', (like, like, like, like, like)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_connection()
    total_cap = conn.execute('SELECT SUM(capacity) FROM rooms').fetchone()[0] or 0
    total_occ = conn.execute('SELECT COUNT(*) FROM tenants WHERE is_active=1').fetchone()[0]
    adv_paid  = conn.execute('SELECT COALESCE(SUM(advance_paid),0) FROM tenants WHERE is_active=1').fetchone()[0]
    adv_total = conn.execute('SELECT COALESCE(SUM(advance_total),0) FROM tenants WHERE is_active=1').fetchone()[0]
    floors = []
    for fl in [1, 2, 3]:
        cap = conn.execute('SELECT SUM(capacity) FROM rooms WHERE floor=?', (fl,)).fetchone()[0] or 0
        occ = conn.execute('''
            SELECT COUNT(*) FROM tenants t
            JOIN rooms r ON t.room_id = r.id
            WHERE r.floor=? AND t.is_active=1
        ''', (fl,)).fetchone()[0]
        floors.append({'floor': fl, 'capacity': cap, 'occupied': occ, 'vacant': cap - occ})
    conn.close()
    return {
        'total_capacity':  total_cap,
        'total_occupied':  total_occ,
        'total_vacant':    total_cap - total_occ,
        'advance_paid':    adv_paid,
        'advance_pending': adv_total - adv_paid,
        'floors': floors,
    }

# ?? Monthly Rent Collection ??????????????????????????????????????

def calculate_rent_for_month(tenant, yyyy_mm):
    start_date_str = tenant.get('food_start_date') or tenant.get('join_date')
    if not start_date_str: return 0
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        target_year, target_month = map(int, yyyy_mm.split('-'))
    except ValueError:
        return 0

    if (target_year < start_date.year) or (target_year == start_date.year and target_month < start_date.month):
        return 0

    rc = get_applicable_rent(f"{yyyy_mm}-01")
    if not rc: return 0

    room = get_room(tenant['room_id'])
    custom_rent = room.get('custom_rent') if room else None

    if target_year == start_date.year and target_month == start_date.month:
        breakdown = calc_prorated_rent(start_date_str, rc, custom_rent)
        return breakdown['total_prorated'] if breakdown else 0

    if custom_rent is not None:
        return custom_rent
    return float(rc['room_rent']) + float(rc['food_rent'])

def get_monthly_collection(yyyy_mm):
    conn = get_connection()
    tenants = get_all_active_tenants()
    
    rows = conn.execute('SELECT tenant_id, SUM(amount_paid) as paid FROM rent_payments WHERE rent_month=? GROUP BY tenant_id', (yyyy_mm,)).fetchall()
    paid_map = {r['tenant_id']: r['paid'] for r in rows}
    conn.close()

    results = []
    for t in tenants:
        due = calculate_rent_for_month(t, yyyy_mm)
        if due <= 0: continue
        
        paid = paid_map.get(t['id'], 0)
        balance = due - paid
        results.append({
            'tenant': t,
            'due': due,
            'paid': paid,
            'balance': balance
        })
    return results

def add_rent_payment(tenant_id, rent_month, amount_paid, payment_date):
    conn = get_connection()
    conn.execute(
        'INSERT INTO rent_payments (tenant_id, rent_month, amount_paid, payment_date) VALUES (?,?,?,?)',
        (tenant_id, rent_month, amount_paid, payment_date)
    )
    conn.commit()
    conn.close()

def get_tenant_payments(tenant_id):
    conn = get_connection()
    rows = conn.execute('SELECT * FROM rent_payments WHERE tenant_id=? ORDER BY rent_month DESC, payment_date DESC', (tenant_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_admin(email, password_hash):
    conn = get_connection()
    try:
        conn.execute('INSERT INTO admins (email, password_hash) VALUES (?, ?)', (email, password_hash))
        conn.commit()
    finally:
        conn.close()

def get_admin_by_email(email):
    conn = get_connection()
    row = conn.execute('SELECT * FROM admins WHERE email=?', (email,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_tenant_by_email(email):
    conn = get_connection()
    row = conn.execute('SELECT * FROM tenants WHERE email=? AND is_active=1', (email,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_payment(payment_id):
    conn = get_connection()
    row = conn.execute('SELECT p.*, t.name as tenant_name, t.phone, r.label as room_label, r.floor FROM rent_payments p JOIN tenants t ON p.tenant_id = t.id JOIN rooms r ON t.room_id = r.id WHERE p.id=?', (payment_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
