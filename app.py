from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, delete
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv


# Configurations
app = Flask(__name__)
load_dotenv() 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.getenv('DEBUG', 'false') == 'true' #To convert from string to boolean

db = SQLAlchemy(app)

# Set up database models
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) #Already indexed because unique
    password = db.Column(db.String(80), nullable=False)
    firstName = db.Column(db.String(80), nullable=False)
    lastName = db.Column(db.String(80), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    sports = db.relationship('Sports', secondary='registrations', back_populates='users')

class Sports(db.Model):
    __tablename__ = 'sports'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) #Already indexed because unique
    users = db.relationship('Users', secondary='registrations', back_populates='sports')

registrations = db.Table('registrations',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), index=True),
    db.Column('sport_id', db.Integer, db.ForeignKey('sports.id'), index=True),
    db.PrimaryKeyConstraint('user_id', 'sport_id')
)

with app.app_context():
    db.create_all()

sports_list = ['Basketball', 'Bouldering', 'Swimming']

#Adds items from sports_list that are not in Sports table yet 
with app.app_context():
    sports = Sports.query.all()
    sports_list_current = list(set([sport.name for sport in sports]))

    for sport_name in sports_list:
        if sport_name not in sports_list_current:
            new_sport = Sports(name=sport_name)
            db.session.add(new_sport)
    db.session.commit()

@app.context_processor
def inject_logged_in():
    return {'logged_in': 'username' in session}

@app.route('/')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))

@app.route('/create_account', methods=["GET", "POST"])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            return "Username already taken, please choose another"
        password = generate_password_hash(request.form.get('password'))
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')

        new_user = Users(username=username, password=password, firstName=firstName, lastName=lastName, admin=0)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('create_account.html', login_link=url_for("login"))

@app.route('/admin')
def admin():
    sql_query = text(
        """
        SELECT 
            u.id AS student_id,
            u.firstName,
            u.lastName,
            s.name AS sport
        FROM 
            registrations r
        LEFT JOIN users u
            ON r.user_id = u.id
        LEFT JOIN sports s
            ON r.sport_id = s.id
        """
    )

    result = db.session.execute(sql_query)
    registrations = result.fetchall()
    print(registrations)
    return render_template('admin_dashboard.html', registrations=registrations)

# @app.route('/make_admin', methods=["POST"])
# def make_admin():
#     username = session.get('username')
#     user = Users.query.filter_by(username=username).first()
#     if not user.admin or not user:
#         return redirect(url_for('login'))
    
#     data = request.get_json()
#     new_admin_username = data.get('new_admin_username')
#     if not new_admin_username:
#         return jsonify({'success': False, 'message': 'Bad request'}), 400

#     new_admin = Users.query.filter_by(username=new_admin_username).first()
#     if not new_admin:
#         return jsonify({'success': False, 'message': 'User does not exist'}), 404

#     new_admin.admin = True
#     db.session.commit()

#     return jsonify({'success': True, 'message': f'{new_admin_username} is now admin'})

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password_to_check = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password_to_check):
                session["username"] = username
                return redirect(url_for('select_sports'))
            else:
                flash('Incorrect password')
        else:
            flash('Username not recognised')
            
    return render_template('login.html', create_account_link=url_for("create_account"))

@app.route('/logout')
def logout():
    if session.get('username'):
        session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/select_sports')
def select_sports():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    return render_template("select_sports.html", sports=sports_list)

@app.route('/get_sport_icon/<sport>/<colour>')
def get_sport_icon(sport, colour):
    filename = f'img/icons_{colour}/{sport}_icon.png'
    return url_for('static', filename=filename)

@app.route('/get_registered_sports')
def get_registered_sports():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = Users.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    registered_sports = db.session.query(Sports.name)\
                                  .join(registrations, Sports.id == registrations.c.sport_id)\
                                  .filter(registrations.c.user_id == user.id)\
                                  .all()

    sport_names = [sport_name for (sport_name,) in registered_sports]

    return jsonify(sport_names)

@app.route('/register_for_sport', methods=["POST"])
def register_for_sport():
    data = request.get_json()
    sport_name = data.get('sportName')
    if not sport_name:
        return jsonify({'success': False, 'message': 'Missing sport name'}), 400
    
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'}), 400
    
    user = Users.query.filter_by(username=username).first()
    sport = Sports.query.filter_by(name=sport_name).first()
    if not user or not sport:
        return jsonify({'success': False, 'message': 'User or sport not found'}), 404
    
    registered = db.session.query(registrations).filter_by(user_id=user.id, sport_id=sport.id).first()
    if registered:
        return jsonify({'success': True, 'message': f'{user.username} already registered for {sport.name}'}), 200
    
    try:
        new_registration = registrations.insert().values(user_id=user.id, sport_id=sport.id)
        db.session.execute(new_registration)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{user.username} registered for {sport.name}'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f'Registration failed: {e}')
        return jsonify({'success': False, 'message': 'Registration failed due to an internal error'}), 500
    
@app.route('/deregister_for_sport', methods=["POST"])
def deregister_for_sport():
    data = request.get_json()
    sport_name = data.get('sportName')
    if not sport_name:
        return jsonify({'success': False, 'message': 'Missing sport name'}), 400
    
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'}), 400
    
    user = Users.query.filter_by(username=username).first()
    sport = Sports.query.filter_by(name=sport_name).first()
    if not user or not sport:
        return jsonify({'success': False, 'message': 'User or sport not found'}), 404
    
    registered = db.session.query(registrations).filter_by(user_id=user.id, sport_id=sport.id).first()
    if not registered:
        return jsonify({'success': True, 'message': f'{user.username} already deregistered for {sport.name}'}), 200
    
    try:
        sql_query = delete(registrations).where(
            registrations.c.user_id == user.id,
            registrations.c.sport_id == sport.id
        )
        db.session.execute(sql_query)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{user.username} deregistered for {sport.name}'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f'Deregistration failed: {e}')
        return jsonify({'success': False, 'message': 'Deregistration failed due to an internal error'}), 500
