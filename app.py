from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, Flask, render_template, request, redirect, url_for, flash, Response, jsonify
import database as db
import csv
import io
from datetime import date

app = Flask(__name__)
CORS(app)
app.secret_key = 'bhavani_residency_2024'

@app.context_processor
def inject_user():
    user = None
    if session.get('admin_id'):
        conn = db.get_connection()
        admin = conn.execute('SELECT email FROM admins WHERE id=?', (session['admin_id'],)).fetchone()
        conn.close()
        if admin:
            user = {'role': 'Admin', 'email': admin['email'], 'name': 'Admin'}
    elif session.get('tenant_id'):
        conn = db.get_connection()
        tenant = conn.execute('SELECT email, name FROM tenants WHERE id=?', (session['tenant_id'],)).fetchone()
        conn.close()
        if tenant:
            user = {'role': 'Student', 'email': tenant['email'], 'name': tenant['name']}
    return dict(current_user=user)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('tenant_id') and not session.get('admin_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/dashboard')
@admin_required
def dashboard():
    import datetime
    from dateutil.relativedelta import relativedelta
    
    stats = db.get_stats()
    today = date.today()
    today_rent = db.get_applicable_rent(today.isoformat())
    
    month_arg = request.args.get('month')
    current_yyyy_mm = month_arg if month_arg else today.strftime('%Y-%m')
    
    collection = db.get_monthly_collection(current_yyyy_mm)
    
    # Get all months for the dropdown
    conn = db.get_connection()
    row = conn.execute("SELECT MIN(food_start_date) as start FROM tenants WHERE food_start_date != ''").fetchone()
    conn.close()
    
    start_str = row['start'] if row and row['start'] else today.isoformat()
    start_date = datetime.date.fromisoformat(start_str[:10]).replace(day=1)
    curr_date = today.replace(day=1)
    
    all_months = []
    curr = start_date
    while curr <= curr_date:
        m_val = curr.strftime('%Y-%m')
        m_label = curr.strftime('%B %Y')
        all_months.append({'value': m_val, 'label': m_label})
        curr += relativedelta(months=1)
    
    all_months.reverse() # Newest first
    
    summary = {
        'expected': sum(c['due'] for c in collection),
        'collected': sum(c['paid'] for c in collection),
        'pending': sum(c['balance'] for c in collection)
    }
    
    # Rent Pending List
    rent_pending_list = [c for c in collection if c['balance'] > 0]
    
    # Advance Pending List
    tenants = db.get_all_active_tenants()
    advance_pending_list = []
    for t in tenants:
        adv_total = t.get('advance_total') or 10000
        adv_paid = t.get('advance_paid') or 0
        if (adv_total - adv_paid) > 0:
            advance_pending_list.append({
                'tenant': t,
                'pending': adv_total - adv_paid
            })

    return render_template('dashboard.html', 
                           stats=stats, 
                           today_rent=today_rent,
                           current_yyyy_mm=current_yyyy_mm,
                           summary=summary,
                           rent_pending_list=rent_pending_list,
                           advance_pending_list=advance_pending_list,
                           all_months=all_months)


@app.route('/floor/<int:floor_num>')
@admin_required
def floor_view(floor_num):
    rooms = db.get_rooms_by_floor(floor_num)
    for room in rooms:
        room['tenants']   = db.get_tenants_by_room(room['id'])
        room['occupancy'] = len(room['tenants'])
    return render_template('floor.html', floor_num=floor_num, rooms=rooms)


@app.route('/room/<room_id>')
def room_detail(room_id):
    room = db.get_room(room_id)
    if not room:
        flash('Room not found.', 'danger')
        return redirect(url_for('dashboard'))
    tenants   = db.get_tenants_by_room(room_id)
    occupancy = len(tenants)
    # Attach rent breakdown per tenant
    for t in tenants:
        rc = db.get_applicable_rent(t.get('food_start_date') or t.get('join_date'))
        t['rent_breakdown'] = db.calc_prorated_rent(t.get('food_start_date'), rc, room.get('custom_rent'))
        t['monthly_rent']   = room['custom_rent'] if room.get('custom_rent') else ((rc['room_rent'] + rc['food_rent']) if rc else 0)
        t['payments'] = db.get_tenant_payments(t['id'])
    return render_template('room.html', room=room, tenants=tenants, occupancy=occupancy)


def _form_data(form):
    return {
        'name':            form.get('name','').strip(),
        'father_name':     form.get('father_name','').strip(),
        'village':         form.get('village','').strip(),
        'mandalam':        form.get('mandalam','').strip(),
        'district':        form.get('district','').strip(),
        'college':         form.get('college','').strip(),
        'study_year':      form.get('study_year','').strip(),
        'branch':          form.get('branch','').strip(),
        'aadhar_no':       form.get('aadhar_no','').strip(),
        'phone':           form.get('phone','').strip(),
        'parent_phone':    form.get('parent_phone','').strip(),
        'email':           form.get('email','').strip(),
        'room_id':         form.get('room_id','').strip(),
        'join_date':       form.get('join_date','').strip(),
        'food_start_date': form.get('food_start_date','').strip(),
        'advance_paid':    form.get('advance_paid','0').strip(),
        'advance_total':   form.get('advance_total','10400').strip(),
        'notes':           form.get('notes','').strip(),
    }


@app.route('/tenant/add', methods=['GET', 'POST'])
def add_tenant():
    rooms       = db.get_all_rooms()
    preselected = request.args.get('room_id', '')
    today       = date.today().isoformat()
    rent_configs = db.get_all_rent_configs()

    if request.method == 'POST':
        data = _form_data(request.form)

        if not data['name']:
            flash('Student name is required.', 'danger')
            return render_template('add_tenant.html', rooms=rooms,
                                   preselected=preselected, today=today,
                                   rent_configs=rent_configs)

        room    = db.get_room(data['room_id'])
        current = db.get_tenant_count_by_room(data['room_id'])
        if current >= room['capacity']:
            flash(f"{room['label']} is full! Capacity: {room['capacity']}", 'danger')
            return render_template('add_tenant.html', rooms=rooms,
                                   preselected=data['room_id'], today=today,
                                   rent_configs=rent_configs)

        if request.form.get('password'):
            data['password_hash'] = generate_password_hash(request.form.get('password'))
        try:
            db.add_tenant(data)
            if session.get('admin_id'):
                flash(f"Student '{data['name']}' added to {room['label']}!", 'success')
                return redirect(url_for('floor_view', floor_num=room['floor']))
            else:
                flash(f"Registration successful! You have been assigned to {room['label']}. Please login.", 'success')
                return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('add_tenant.html', rooms=rooms, preselected=data['room_id'], today=today, rent_configs=rent_configs)

    return render_template('add_tenant.html', rooms=rooms,
                           preselected=preselected, today=today,
                           rent_configs=rent_configs)



@app.route('/tenant/view/<int:tenant_id>')
def view_tenant(tenant_id):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    room = db.get_room(tenant['room_id'])
    
    # Financials
    today = date.today()
    current_month = today.strftime("%Y-%m")
    due = db.calculate_rent_for_month(tenant, current_month)
    
    conn = db.get_connection()
    paid_row = conn.execute('SELECT SUM(amount_paid) as paid FROM rent_payments WHERE tenant_id=? AND rent_month=?', (tenant_id, current_month)).fetchone()
    paid = paid_row['paid'] if paid_row['paid'] else 0
    conn.close()
    
    balance = due - paid
    
    return render_template('view_tenant.html', tenant=tenant, room=room, 
                           current_month=current_month, due=due, paid=paid, balance=balance)

@app.route('/tenant/edit/<int:tenant_id>', methods=['GET', 'POST'])

@admin_required
def edit_tenant(tenant_id):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('dashboard'))
    rooms = db.get_all_rooms()
    rent_configs = db.get_all_rent_configs()

    if request.method == 'POST':
        data = _form_data(request.form)

        if data['room_id'] != tenant['room_id']:
            room    = db.get_room(data['room_id'])
            current = db.get_tenant_count_by_room(data['room_id'])
            if current >= room['capacity']:
                flash(f"{room['label']} is full!", 'danger')
                return render_template('edit_tenant.html', tenant=tenant,
                                       rooms=rooms, rent_configs=rent_configs)

        db.update_tenant(tenant_id, data)
        flash(f"Student '{data['name']}' updated!", 'success')
        room = db.get_room(data['room_id'])
        return redirect(url_for('floor_view', floor_num=room['floor'])) if room else redirect(url_for('dashboard'))

    return render_template('edit_tenant.html', tenant=tenant,
                           rooms=rooms, rent_configs=rent_configs)


@app.route('/tenant/delete/<int:tenant_id>', methods=['POST'])
@admin_required
def delete_tenant(tenant_id):
    tenant = db.get_tenant(tenant_id)
    if tenant:
        room = db.get_room(tenant['room_id'])
        db.deactivate_tenant(tenant_id)
        flash(f"Student '{tenant['name']}' has been removed.", 'info')
        if room:
            return redirect(url_for('floor_view', floor_num=room['floor']))
    return redirect(url_for('dashboard'))


# ── Rent preview API (called by JS) ─────────────────────────────
@app.route('/api/rent-preview')
def rent_preview():
    food_date = request.args.get('food_date', '')
    room_id = request.args.get('room_id', '')
    if not food_date:
        return jsonify({'error': 'no date'}), 400
    rc = db.get_applicable_rent(food_date)
    if not rc:
        return jsonify({'error': 'no config'}), 404

    custom_rent = None
    custom_adv = None
    if room_id:
        room = db.get_room(room_id)
        if room:
            custom_rent = room.get('custom_rent')
            custom_adv = room.get('custom_advance')

    breakdown = db.calc_prorated_rent(food_date, rc, custom_rent)
    if not breakdown:
        return jsonify({'error': 'calc failed'}), 500
    breakdown['advance_amount'] = custom_adv if custom_adv is not None else rc['advance_amount']
    return jsonify(breakdown)


# ── Rent Config management ───────────────────────────────────────
@app.route('/rent-config', methods=['GET', 'POST'])
@admin_required
def rent_config():
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            db.add_rent_config(
                request.form.get('start_date', request.form.get('effective_from', '')),
                float(request.form['room_rent']),
                float(request.form['food_rent']),
                float(request.form.get('advance_amount', 10400)),
                request.form.get('notes', request.form.get('label', '')).strip()
            )
            flash('New rent rate added!', 'success')
        elif action == 'delete':
            db.delete_rent_config(int(request.form['config_id']))
            flash('Rent rate deleted.', 'info')
        return redirect(url_for('rent_config'))

    configs = db.get_all_rent_configs()
    today = date.today().isoformat()
    return render_template('rent_config.html', configs=configs, today=today)


# ── Search ───────────────────────────────────────────────────────
@app.route('/search')
def search():
    query   = request.args.get('q', '').strip()
    results = db.search_tenants(query) if query else []
    return render_template('search.html', query=query, results=results)


# ── Export CSV ───────────────────────────────────────────────────
@app.route('/export')
@admin_required
def export_excel():
    import pandas as pd
    import io
    from dateutil.relativedelta import relativedelta
    from flask import send_file
    
    tenants = db.get_all_active_tenants()
    
    # Determine all months
    conn = db.get_connection()
    row = conn.execute("SELECT MIN(food_start_date) as start FROM tenants WHERE food_start_date != ''").fetchone()
    start_str = row['start'] if row and row['start'] else date.today().isoformat()
    start_date = date.fromisoformat(start_str[:10]).replace(day=1)
    today = date.today().replace(day=1)
    
    months = []
    curr = start_date
    while curr <= today:
        months.append(curr.strftime('%Y-%m'))
        curr += relativedelta(months=1)
        
    data = []
    for t in tenants:
        adv_rem = (t.get('advance_total') or 10000) - (t.get('advance_paid') or 0)
        
        row_data = {
            'ID': t['id'],
            'Name': t['name'],
            'Email': t.get('email', ''),
            'Father/Mother Name': t.get('father_name', ''),
            'Village': t.get('village', ''),
            'Mandalam': t.get('mandalam', ''),
            'District': t.get('district', ''),
            'College': t.get('college', ''),
            'Year': t.get('study_year', ''),
            'Branch': t.get('branch', ''),
            'Aadhar No': str(t.get('aadhar_no', '')),
            'Student Phone': str(t.get('phone', '')),
            'Parent Phone': str(t.get('parent_phone', '')),
            'Room': t['room_id'],
            'Floor': t['floor'],
            'Join Date': t['join_date'],
            'Food Start Date': t.get('food_start_date', ''),
            'Advance Total': t.get('advance_total', 10000),
            'Advance Paid': t.get('advance_paid', 0),
            'Advance Remaining': adv_rem
        }
        
        # Monthly data
        for m in months:
            due = db.calculate_rent_for_month(t, m)
            paid_row = conn.execute('SELECT SUM(amount_paid) as paid FROM rent_payments WHERE tenant_id=? AND rent_month=?', (t['id'], m)).fetchone()
            paid = paid_row['paid'] if paid_row and paid_row['paid'] else 0
            balance = due - paid
            
            # Format 'YYYY-MM' into 'Month YYYY' (e.g., 'July 2026')
            import datetime
            month_name = datetime.datetime.strptime(m, "%Y-%m").strftime("%B %Y")
            
            row_data[f"{month_name} Rent Due"] = due
            row_data[f"{month_name} Rent Paid"] = paid
            row_data[f"{month_name} Balance"] = balance
            
        row_data['Notes'] = t.get('notes', '')
        data.append(row_data)
        
    conn.close()
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Tenants', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Tenants']
        
        # Set column widths to make everything visible
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(idx, idx, max_len)
            
    output.seek(0)
    return send_file(output, download_name='bhavani_residency_export.xlsx', as_attachment=True)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=bhavani_residency_tenants.csv'}
    )



# ?? Monthly Rent Collection ??????????????????????????????????????
@app.route('/rent')
@admin_required
def rent_collection():
    req_month = request.args.get('month')
    if not req_month:
        req_month = date.today().strftime('%Y-%m')
    
    collection = db.get_monthly_collection(req_month)
    collection.sort(key=lambda x: (x['balance'] <= 0, x['tenant']['name']))
    
    total_due = sum(c['due'] for c in collection)
    total_paid = sum(c['paid'] for c in collection)
    total_balance = sum(c['balance'] for c in collection)
    
    return render_template('rent.html', collection=collection, 
                           month=req_month, today=date.today().isoformat(),
                           total_due=total_due, total_paid=total_paid, total_balance=total_balance)

@app.route('/rent/pay', methods=['POST'])
@admin_required
def pay_rent():
    tenant_id = request.form['tenant_id']
    rent_month = request.form['rent_month']
    amount = float(request.form['amount'])
    payment_date = request.form['payment_date']
    
    db.add_rent_payment(tenant_id, rent_month, amount, payment_date)
    return redirect(url_for('rent_collection', month=rent_month))


# ?? API ENDPOINTS (For React Frontend) ???????????????????????????

@app.route('/api/dashboard-stats')
def api_dashboard_stats():
    stats = db.get_stats()
    today = date.today()
    today_rent = db.get_applicable_rent(today.isoformat())
    current_yyyy_mm = today.strftime('%Y-%m')
    collection = db.get_monthly_collection(current_yyyy_mm)
    
    total_due = sum(c['due'] for c in collection)
    total_paid = sum(c['paid'] for c in collection)
    total_balance = sum(c['balance'] for c in collection)
    pending_count = sum(1 for c in collection if c['balance'] > 0)
    
    return jsonify({
        'stats': stats,
        'rent': {
            'period': today_rent.get('label', '') if today_rent else '',
            'room': today_rent.get('room_rent', 0) if today_rent else 0,
            'food': today_rent.get('food_rent', 0) if today_rent else 0,
            'total': (today_rent.get('room_rent', 0) + today_rent.get('food_rent', 0)) if today_rent else 0,
            'advance': today_rent.get('advance_amount', 0) if today_rent else 0
        },
        'collection': {
            'month': today.strftime('%B %Y'),
            'pending_count': pending_count,
            'total_due': total_due,
            'total_paid': total_paid,
            'total_balance': total_balance
        }
    })


@app.route('/api/rent-collection')
def api_rent_collection():
    req_month = request.args.get('month')
    if not req_month:
        req_month = date.today().strftime('%Y-%m')
    
    collection = db.get_monthly_collection(req_month)
    total_expected = sum(c['due'] for c in collection)
    total_collected = sum(c['paid'] for c in collection)
    total_pending = sum(c['balance'] for c in collection)
    
    return jsonify({
        'month': req_month,
        'collection': collection,
        'summary': {
            'expected': total_expected,
            'collected': total_collected,
            'pending': total_pending
        }
    })

@app.route('/api/pay-rent', methods=['POST'])
def api_pay_rent():
    data = request.json
    tenant_id = data.get('tenant_id')
    rent_month = data.get('rent_month')
    amount = float(data.get('amount'))
    payment_date = data.get('payment_date', date.today().isoformat())
    
    db.add_rent_payment(tenant_id, rent_month, amount, payment_date)
    return jsonify({'success': True})


@app.route('/api/floors')
def api_floors():
    return jsonify([{'id': 1, 'name': 'Floor 1'}, {'id': 2, 'name': 'Floor 2'}, {'id': 3, 'name': 'Floor 3'}])

@app.route('/api/floor/<int:floor_id>')
def api_floor(floor_id):
    rooms = db.get_rooms_by_floor(floor_id)
    for room in rooms:
        room['tenants'] = db.get_tenants_by_room(room['id'])
    return jsonify({'floor': {'id': floor_id, 'name': f'Floor {floor_id}'}, 'rooms': rooms})

@app.route('/api/rooms/available')
def api_available_rooms():
    rooms = []
    for floor_id in [1, 2, 3]:
        for r in db.get_rooms_by_floor(floor_id):
            tenants = db.get_tenants_by_room(r['id'])
            if len(tenants) < r['capacity']:
                r['floor_name'] = str(floor_id)
                r['available_beds'] = r['capacity'] - len(tenants)
                rooms.append(r)
    return jsonify(rooms)

@app.route('/api/tenant/add', methods=['POST'])
def api_tenant_add_post():
    data = request.json
    try:
        db.add_tenant(
            name=data['name'],
            phone=data['phone'],
            room_id=data['room_id'],
            join_date=data['join_date'],
            food_start_date=data['food_start_date'],
            rent_start_date=data['rent_start_date'],
            advance_paid=data['advance_paid']
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/rent-config/latest')
def api_rent_config_latest():
    configs = db.get_all_rent_configs()
    if configs:
        return jsonify(configs[0])  # Assuming ordered by start_date DESC or we grab the latest
    return jsonify({'room_rent': 0, 'food_rent': 0})




@app.route('/')
def index():
    if session.get('admin_id'):
        return redirect(url_for('dashboard'))
    if session.get('tenant_id'):
        return redirect(url_for('tenant_dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check Admin first
        admin = db.get_admin_by_email(email)
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            return redirect(url_for('dashboard'))
            
        # Check Tenant
        tenant = db.get_tenant_by_email(email)
        if tenant and tenant['password_hash'] and check_password_hash(tenant['password_hash'], password):
            session['tenant_id'] = tenant['id']
            return redirect(url_for('tenant_dashboard'))
            
        flash('Invalid email or password', 'danger')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    # Only allow if no admins exist, OR if an admin is already logged in
    conn = db.get_connection()
    count = conn.execute('SELECT COUNT(*) FROM admins').fetchone()[0]
    conn.close()
    
    if count > 0 and not session.get('admin_id'):
        flash('Admin already exists. Please login.', 'danger')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            db.add_admin(email, generate_password_hash(password))
            flash('Admin registered successfully. You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error registering admin', 'danger')
            
    return render_template('register_admin.html')

@app.route('/tenant/dashboard')
@login_required
def tenant_dashboard():
    tenant_id = session.get('tenant_id')
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        session.clear()
        return redirect(url_for('login'))
        
    room = db.get_room(tenant['room_id'])
    today = date.today()
    current_month = today.strftime("%Y-%m")
    due = db.calculate_rent_for_month(tenant, current_month)
    
    conn = db.get_connection()
    paid_row = conn.execute('SELECT SUM(amount_paid) as paid FROM rent_payments WHERE tenant_id=? AND rent_month=?', (tenant_id, current_month)).fetchone()
    paid = paid_row['paid'] if paid_row['paid'] else 0
    conn.close()
    
    balance = due - paid
    
    return render_template('view_tenant.html', tenant=tenant, room=room, 
                           current_month=current_month, due=due, paid=paid, balance=balance, is_tenant=True)




from datetime import datetime

@app.route('/api/tenant/pay-rent', methods=['POST'])
@login_required
def api_tenant_pay_rent():
    data = request.json
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'Not logged in'}), 401
        
    rent_month = data.get('rent_month')
    amount = float(data.get('amount'))
    payment_date = date.today().isoformat()
    payment_timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    db.add_rent_payment(tenant_id, rent_month, amount, payment_date, payment_timestamp)
    
    # Get the latest payment id for this tenant
    conn = db.get_connection()
    payment_id = conn.execute('SELECT id FROM rent_payments WHERE tenant_id=? ORDER BY id DESC LIMIT 1', (tenant_id,)).fetchone()[0]
    conn.close()
    
    return jsonify({'success': True, 'payment_id': payment_id})

@app.route('/receipt/<int:payment_id>')
@login_required
def receipt(payment_id):
    payment = db.get_payment(payment_id)
    if not payment:
        flash('Receipt not found.', 'danger')
        return redirect(url_for('index'))
        
    # Ensure they can only see their own receipt, unless they are admin
    if not session.get('admin_id') and session.get('tenant_id') != payment['tenant_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    return render_template('receipt.html', payment=payment)

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)