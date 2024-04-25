from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hackathon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super secret key'

db = SQLAlchemy()
db.init_app(app)

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)

class Message(db.Model):
    __tablename__ = 'Message'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/admin/users')
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('chat'))
        else:
            return 'Неверный логин или пароль'

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    all_messages = Message.query.filter_by(user_id=session['user_id']).order_by(Message.timestamp.desc()).all()

    if request.method == 'POST':
        user_text = request.form['text']

        new_user_message = Message(text=user_text, user_id=session['user_id'])
        db.session.add(new_user_message)
        db.session.commit()

        new_bot_message = Message(text=f"Вы сказали: {user_text}", user_id=session['user_id'])
        db.session.add(new_bot_message)
        db.session.commit()

        all_messages = Message.query.filter_by(user_id=session['user_id']).order_by(Message.timestamp.desc()).all()

    return render_template('chat.html', messages=all_messages)

if __name__ == '__main__':
    app.run(debug=True)