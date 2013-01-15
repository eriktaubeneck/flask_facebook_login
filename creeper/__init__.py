from flask import Flask, redirect, url_for, render_template, request, jsonify, session
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
import sys

app = Flask(__name__)

app.config.update(
  SECRET_KEY = 'dev key',
  DEBUG = True,
  SQLALCHEMY_DATABASE_URI = 'sqlite://' #in memory db. or use sqlite:////absolute/path/to/creeper.db,
  )
db = SQLAlchemy(app)
from models import Users

@app.route('/channel')
def channel():
  return render_template('channel.html')

@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('landing'))

@app.route('/')
def landing():
  return render_template('index.html', user=session.get('user', None))

@app.route('/_get_facebook_login')
def get_facebook_login():
  facebook_id = request.args.get('facebook_id', False, type=int)
  name = request.args.get('name', '', type=str)
  if facebook_id:
    user = Users.query.filter_by(facebook_id=facebook_id).first()
    if not user:
      user = Users(facebook_id,name)
      db.session.add(user)
      db.session.commit()
    session['user'] = user
  return jsonify(result=1)