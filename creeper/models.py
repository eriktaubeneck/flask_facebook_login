from creeper import db
from sqlalchemy.sql.expression import func

class Users(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  facebook_id = db.Column(db.Integer)
  name = db.Column(db.String(50))
  
  def __init__(self,facebook_id, name):
    self.facebook_id = facebook_id
    self.name = name
    
db.create_all()