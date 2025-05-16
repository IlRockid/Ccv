from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, EqualTo

class GuestForm(FlaskForm):
    last_name = StringField('Cognome', validators=[DataRequired()])
    first_name = StringField('Nome', validators=[DataRequired()])
    gender = SelectField('Sesso', choices=[('M', 'Maschio'), ('F', 'Femmina')], validators=[DataRequired()])
    birth_place = StringField('Luogo di nascita', validators=[DataRequired()])
    province = StringField('Provincia (sigla)', validators=[Length(min=2, max=2, message='Inserire la sigla di 2 caratteri')])
    birth_date = DateField('Data di nascita', format='%Y-%m-%d', validators=[DataRequired()])
    fiscal_code = StringField('Codice Fiscale', validators=[Length(min=16, max=16)])
    country_code = StringField('Codice Paese (per stranieri)', validators=[Length(max=4)])
    permit_number = StringField('Numero permesso di soggiorno')
    permit_date = DateField('Data rilascio permesso', format='%Y-%m-%d', validators=[Optional()])
    health_card = StringField('Numero tessera sanitaria')
    health_card_expiry = DateField('Data scadenza tessera sanitaria', format='%Y-%m-%d', validators=[Optional()])
    entry_date = DateField('Data di inserimento nella struttura', format='%Y-%m-%d', validators=[Optional()])
    check_in_date = DateField('Data Check-in', format='%Y-%m-%d', validators=[Optional()])
    check_out_date = DateField('Data Check-out', format='%Y-%m-%d', validators=[Optional()])
    room_number = StringField('Numero stanza')
    floor = StringField('Piano')
    family_relations = TextAreaField('Relazioni familiari')
    submit = SubmitField('Salva')

class SettingsForm(FlaskForm):
    current_password = PasswordField('Password attuale')
    new_password = PasswordField('Nuova password')
    confirm_password = PasswordField('Conferma password', validators=[EqualTo('new_password', message='Le password devono coincidere')])
    submit = SubmitField('Salva impostazioni')
