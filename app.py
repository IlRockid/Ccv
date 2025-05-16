import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd
from io import BytesIO
import sqlite3
import tempfile
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "ancoracas25_default_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
# Usa PostgreSQL per evitare errori di database in sola lettura
database_url = os.environ.get('DATABASE_URL')
if database_url:
    print(f"Usando database PostgreSQL")
else:
    # Fallback a SQLite solo se necessario
    database_url = "sqlite:///database.db"
    print(f"Usando database SQLite: {database_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Import models (after db is defined)
from models import Guest, CustomField, Setting

# Create database tables
with app.app_context():
    db.create_all()
    
    # Add default password setting if not exists
    if not Setting.query.filter_by(key='password').first():
        default_password = Setting(key='password', value='ancoracas25')
        db.session.add(default_password)
        db.session.commit()

# Import utility functions
from utils import check_expiring_permits
from fiscal_code import calculate_fiscal_code

# Import forms
from forms import GuestForm, SettingsForm

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Accesso richiesto', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Get stored password from settings or use default
        with app.app_context():
            setting = Setting.query.filter_by(key='password').first()
            stored_password = setting.value if setting else 'ancoracas25'
        
        if password == stored_password:
            session['logged_in'] = True
            flash('Accesso effettuato con successo', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Password non corretta', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Disconnessione effettuata', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get count of guests
    total_guests = Guest.query.count()
    
    # Get count of expiring permits (within 7 days)
    expiring_permits = check_expiring_permits()
    
    # Get latest added guests
    latest_guests = Guest.query.order_by(Guest.entry_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          total_guests=total_guests, 
                          expiring_permits=len(expiring_permits),
                          latest_guests=latest_guests,
                          expiring_list=expiring_permits)

@app.route('/new_guest', methods=['GET', 'POST'])
@login_required
def new_guest():
    form = GuestForm()
    
    # Get all existing guests for family relations selector
    all_guests = Guest.query.all()
    
    if request.method == 'POST':
        try:
            # Create new guest from form data
            new_guest = Guest(
                last_name=request.form['last_name'],
                first_name=request.form['first_name'],
                gender=request.form['gender'],
                birth_place=request.form['birth_place'],
                province=request.form['province'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d'),
                permit_number=request.form['permit_number'],
                permit_date=datetime.strptime(request.form['permit_date'], '%Y-%m-%d') if request.form['permit_date'] else None,
                permit_expiry=datetime.strptime(request.form['permit_date'], '%Y-%m-%d') + timedelta(days=180) if request.form['permit_date'] else None,
                health_card=request.form['health_card'],
                health_card_expiry=datetime.strptime(request.form['health_card_expiry'], '%Y-%m-%d') if request.form['health_card_expiry'] else None,
                entry_date=datetime.strptime(request.form['entry_date'], '%Y-%m-%d') if request.form['entry_date'] else datetime.now(),
                check_in_date=datetime.strptime(request.form['check_in_date'], '%Y-%m-%d') if request.form.get('check_in_date') else None,
                check_out_date=datetime.strptime(request.form['check_out_date'], '%Y-%m-%d') if request.form.get('check_out_date') else None,
                room_number=request.form['room_number'],
                floor=request.form['floor'],
                family_relations=request.form['family_relations'],
                fiscal_code=request.form['fiscal_code'],
                country_code=request.form['country_code']
            )
            
            # Save to database
            db.session.add(new_guest)
            db.session.commit()
            
            # Handle custom fields
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_name = request.form.get(f'custom_field_name_{key.split("_")[-1]}')
                    if field_name and value:
                        custom_field = CustomField(
                            guest_id=new_guest.id,
                            field_name=field_name,
                            field_value=value
                        )
                        db.session.add(custom_field)
            
            db.session.commit()
            flash('Ospite aggiunto con successo', 'success')
            return redirect(url_for('archive'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il salvataggio: {str(e)}', 'danger')
    
    return render_template('new_guest.html', form=form, all_guests=all_guests)

@app.route('/archive')
@login_required
def archive():
    guests = Guest.query.all()
    return render_template('archive.html', guests=guests)

@app.route('/guest/<int:guest_id>')
@login_required
def guest_detail(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    custom_fields = CustomField.query.filter_by(guest_id=guest_id).all()
    return render_template('guest_detail.html', guest=guest, custom_fields=custom_fields)

@app.route('/guest/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_guest(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    custom_fields = CustomField.query.filter_by(guest_id=guest_id).all()
    
    # Get all existing guests for family relations selector
    all_guests = Guest.query.all()
    
    if request.method == 'POST':
        try:
            # Update guest data
            guest.last_name = request.form['last_name']
            guest.first_name = request.form['first_name']
            guest.gender = request.form['gender']
            guest.birth_place = request.form['birth_place']
            guest.province = request.form['province']
            guest.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d')
            guest.permit_number = request.form['permit_number']
            
            if request.form['permit_date']:
                guest.permit_date = datetime.strptime(request.form['permit_date'], '%Y-%m-%d')
                guest.permit_expiry = guest.permit_date + timedelta(days=180)
            
            guest.health_card = request.form['health_card']
            
            if request.form['health_card_expiry']:
                guest.health_card_expiry = datetime.strptime(request.form['health_card_expiry'], '%Y-%m-%d')
            
            if request.form['entry_date']:
                guest.entry_date = datetime.strptime(request.form['entry_date'], '%Y-%m-%d')
            
            if request.form.get('check_in_date'):
                guest.check_in_date = datetime.strptime(request.form['check_in_date'], '%Y-%m-%d')
                
            if request.form.get('check_out_date'):
                guest.check_out_date = datetime.strptime(request.form['check_out_date'], '%Y-%m-%d')
                
            guest.room_number = request.form['room_number']
            guest.floor = request.form['floor']
            guest.family_relations = request.form['family_relations']
            guest.fiscal_code = request.form['fiscal_code']
            guest.country_code = request.form['country_code']
            
            # Handle custom fields
            # First, delete existing custom fields
            CustomField.query.filter_by(guest_id=guest_id).delete()
            
            # Then add new custom fields
            for key, value in request.form.items():
                if key.startswith('custom_field_'):
                    field_name = request.form.get(f'custom_field_name_{key.split("_")[-1]}')
                    if field_name and value:
                        custom_field = CustomField(
                            guest_id=guest.id,
                            field_name=field_name,
                            field_value=value
                        )
                        db.session.add(custom_field)
            
            db.session.commit()
            flash('Ospite aggiornato con successo', 'success')
            return redirect(url_for('guest_detail', guest_id=guest_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'danger')
    
    return render_template('new_guest.html', guest=guest, custom_fields=custom_fields, edit_mode=True, all_guests=all_guests)

@app.route('/guest/<int:guest_id>/delete', methods=['POST'])
@login_required
def delete_guest(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    
    try:
        # Delete custom fields first
        CustomField.query.filter_by(guest_id=guest_id).delete()
        
        # Delete guest
        db.session.delete(guest)
        db.session.commit()
        flash('Ospite eliminato con successo', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
    
    return redirect(url_for('archive'))

@app.route('/import_data', methods=['POST'])
@login_required
def import_data():
    if 'import_file' not in request.files:
        flash('Nessun file selezionato', 'danger')
        return redirect(url_for('export'))
    
    file = request.files['import_file']
    if file.filename == '':
        flash('Nessun file selezionato', 'danger')
        return redirect(url_for('export'))
    
    # Verifica se la checkbox di conferma è spuntata
    if 'confirm_import' not in request.form:
        flash('È necessario confermare l\'importazione', 'danger')
        return redirect(url_for('export'))
    
    try:
        # Controlla l'estensione del file
        if file.filename.endswith('.xlsx'):
            # Importa da Excel
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            # Importa da CSV
            df = pd.read_csv(file)
        else:
            flash('Formato file non supportato. Usa Excel (.xlsx) o CSV (.csv)', 'danger')
            return redirect(url_for('export'))
        
        # Verifica se il DataFrame contiene le colonne necessarie
        required_columns = ['last_name', 'first_name', 'gender', 'birth_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'File non valido. Mancano le colonne: {", ".join(missing_columns)}', 'danger')
            return redirect(url_for('export'))
        
        # Inizia una transazione per assicurarsi che tutte le operazioni vadano a buon fine
        db.session.begin_nested()
        
        # Opzionale: svuota la tabella degli ospiti esistenti
        # Guest.query.delete()
        
        # Importa ogni riga nel database
        guests_imported = 0
        for _, row in df.iterrows():
            try:
                # Crea un nuovo ospite con i dati dal file
                guest = Guest(
                    last_name=row.get('last_name', ''),
                    first_name=row.get('first_name', ''),
                    gender=row.get('gender', ''),
                    birth_place=row.get('birth_place', ''),
                    province=row.get('province', ''),
                    birth_date=pd.to_datetime(row.get('birth_date')).date() if pd.notna(row.get('birth_date')) else None,
                    fiscal_code=row.get('fiscal_code', ''),
                    country_code=row.get('country_code', ''),
                    permit_number=row.get('permit_number', ''),
                    permit_date=pd.to_datetime(row.get('permit_date')).date() if pd.notna(row.get('permit_date')) else None,
                    permit_expiry=pd.to_datetime(row.get('permit_expiry')).date() if pd.notna(row.get('permit_expiry')) else None,
                    health_card=row.get('health_card', ''),
                    health_card_expiry=pd.to_datetime(row.get('health_card_expiry')).date() if pd.notna(row.get('health_card_expiry')) else None,
                    entry_date=pd.to_datetime(row.get('entry_date')).date() if pd.notna(row.get('entry_date')) else None,
                    exit_date=pd.to_datetime(row.get('exit_date')).date() if pd.notna(row.get('exit_date')) else None,
                    check_in_date=pd.to_datetime(row.get('check_in_date')).date() if pd.notna(row.get('check_in_date')) else None,
                    check_out_date=pd.to_datetime(row.get('check_out_date')).date() if pd.notna(row.get('check_out_date')) else None,
                    room_number=row.get('room_number', ''),
                    floor=row.get('floor', ''),
                    family_relations=row.get('family_relations', '')
                )
                
                db.session.add(guest)
                guests_imported += 1
                
                # Commit ogni 100 record per evitare problemi di memoria
                if guests_imported % 100 == 0:
                    db.session.commit()
                
            except Exception as e:
                app.logger.error(f"Errore importando riga {_}: {str(e)}")
                # Continua con la prossima riga se c'è un errore
                continue
        
        # Commit finale
        db.session.commit()
        flash(f'Importazione completata con successo! {guests_imported} ospiti importati.', 'success')
        
    except Exception as e:
        # In caso di errore, annulla tutte le modifiche
        db.session.rollback()
        app.logger.error(f"Errore durante l'importazione: {str(e)}")
        flash(f'Errore durante l\'importazione: {str(e)}', 'danger')
    
    return redirect(url_for('export'))

@app.route('/export', methods=['GET', 'POST'])
@login_required
def export_data():
    if request.method == 'POST':
        # Get filter parameters
        nationality = request.form.get('nationality')
        age_filter = request.form.get('age_filter')
        room = request.form.get('room')
        entry_date_from = request.form.get('entry_date_from')
        entry_date_to = request.form.get('entry_date_to')
        
        # Build query with filters
        query = Guest.query
        
        if nationality:
            query = query.filter(Guest.birth_place == nationality)
        
        if age_filter:
            today = datetime.now()
            adult_date = today - timedelta(days=365.25 * 18)  # 18 years ago
            
            if age_filter == 'adult':
                query = query.filter(Guest.birth_date <= adult_date)
            elif age_filter == 'minor':
                query = query.filter(Guest.birth_date > adult_date)
        
        if room:
            query = query.filter(Guest.room_number == room)
        
        if entry_date_from:
            date_from = datetime.strptime(entry_date_from, '%Y-%m-%d')
            query = query.filter(Guest.entry_date >= date_from)
        
        if entry_date_to:
            date_to = datetime.strptime(entry_date_to, '%Y-%m-%d')
            query = query.filter(Guest.entry_date <= date_to)
        
        # Execute query
        guests = query.all()
        
        # Prepare data for export
        data = []
        for guest in guests:
            row = {
                'ID': guest.id,
                'Cognome': guest.last_name,
                'Nome': guest.first_name,
                'Sesso': guest.gender,
                'Luogo di nascita': guest.birth_place,
                'Provincia': guest.province,
                'Data di nascita': guest.birth_date.strftime('%d/%m/%Y') if guest.birth_date else '',
                'Codice Fiscale': guest.fiscal_code,
                'Permesso di soggiorno': guest.permit_number,
                'Data rilascio': guest.permit_date.strftime('%d/%m/%Y') if guest.permit_date else '',
                'Scadenza': guest.permit_expiry.strftime('%d/%m/%Y') if guest.permit_expiry else '',
                'Tessera sanitaria': guest.health_card,
                'Scadenza tessera': guest.health_card_expiry.strftime('%d/%m/%Y') if guest.health_card_expiry else '',
                'Data ingresso': guest.entry_date.strftime('%d/%m/%Y') if guest.entry_date else '',
                'Stanza': guest.room_number,
                'Piano': guest.floor,
                'Relazioni familiari': guest.family_relations
            }
            
            # Add custom fields
            custom_fields = CustomField.query.filter_by(guest_id=guest.id).all()
            for cf in custom_fields:
                row[cf.field_name] = cf.field_value
                
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Current date for the export
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        # Choose export format
        export_format = request.form.get('export_format', 'excel')
        
        if export_format == 'excel':
            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Ospiti', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Ospiti']
                
                # Add footer with current date
                worksheet.set_footer(f'File aggiornato al {current_date}')
                
                # Format header
                header_format = workbook.add_format({
                    'bold': True,
                    'border': 1,
                    'bg_color': '#D9E1F2',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # Apply header format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)
            
            output.seek(0)
            return send_file(
                output,
                as_attachment=True,
                download_name=f'Ancora_CAS_Export_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        elif export_format == 'pdf':
            # Generate PDF using a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Ancora CAS - Export</title>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                        .footer { margin-top: 20px; font-style: italic; }
                    </style>
                </head>
                <body>
                    <h1>Ancora CAS - Elenco Ospiti</h1>
                    {df.to_html(index=False)}
                    <div class="footer">File aggiornato al {current_date}</div>
                </body>
                </html>
                """
                f.write(html_content.encode('utf-8'))
                temp_filename = f.name
            
            try:
                # Create PDF from HTML (we'll use a simple approach with the weasyprint package)
                # Note: In a real implementation, you would need to install weasyprint
                from weasyprint import HTML
                pdf_bytes = HTML(temp_filename).write_pdf()
                
                # Create BytesIO object and write PDF content to it
                output = BytesIO()
                output.write(pdf_bytes)
                output.seek(0)
                
                # Remove temporary HTML file
                os.unlink(temp_filename)
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=f'Ancora_CAS_Export_{datetime.now().strftime("%Y%m%d")}.pdf',
                    mimetype='application/pdf'
                )
            except Exception as e:
                flash(f'Errore durante la generazione del PDF: {str(e)}', 'danger')
                return redirect(url_for('export_data'))
    
    # Get unique values for filters
    nationalities = db.session.query(Guest.birth_place).distinct().all()
    rooms = db.session.query(Guest.room_number).distinct().all()
    
    return render_template('export.html', 
                          nationalities=[n[0] for n in nationalities if n[0]],
                          rooms=[r[0] for r in rooms if r[0]])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    
    if request.method == 'POST':
        try:
            # Update password if provided
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password:
                if new_password != confirm_password:
                    flash('Le password non corrispondono', 'danger')
                    return redirect(url_for('settings'))
                
                # Update password in settings
                password_setting = Setting.query.filter_by(key='password').first()
                if not password_setting:
                    password_setting = Setting(key='password', value='ancoracas25')
                    db.session.add(password_setting)
                
                password_setting.value = new_password
                db.session.commit()
                flash('Password aggiornata con successo', 'success')
                
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il salvataggio delle impostazioni: {str(e)}', 'danger')
    
    return render_template('settings.html', form=form)

@app.route('/calculate_fiscal_code', methods=['POST'])
def calc_fiscal_code():
    data = request.get_json()
    
    last_name = data.get('last_name', '')
    first_name = data.get('first_name', '')
    gender = data.get('gender', '')
    birth_date = data.get('birth_date', '')
    birth_place = data.get('birth_place', '')
    
    if not all([last_name, first_name, gender, birth_date, birth_place]):
        return jsonify({'error': 'Dati mancanti per il calcolo del codice fiscale'})
    
    try:
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
        fiscal_code = calculate_fiscal_code(last_name, first_name, gender, birth_date, birth_place)
        return jsonify({'fiscal_code': fiscal_code})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.context_processor
def utility_processor():
    def calculate_age(birth_date):
        if birth_date:
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        return None
    
    return dict(calculate_age=calculate_age)

# Create tables and run app
with app.app_context():
    db.create_all()
    
    # Create default password setting if it doesn't exist
    if not Setting.query.filter_by(key='password').first():
        default_password = Setting(key='password', value='ancoracas25')
        db.session.add(default_password)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
