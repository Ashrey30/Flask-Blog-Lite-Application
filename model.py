from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Users(UserMixin, db.Model):
    __tablename__ = 'User_Details'
    username = db.Column(db.String, unique = True, primary_key = True)
    email = db.Column(db.String, unique = True)
    password = db.Column(db.String, unique = True)
    pfpname = db.Column(db.String, unique = True)

    user_followers = db.relationship('Followers', foreign_keys = 'Followers.follower', cascade = 'delete')
    user_following = db.relationship('Followers', foreign_keys = 'Followers.following', cascade = 'delete')
    user_by = db.relationship('Posts', foreign_keys = 'Posts.by', cascade = 'delete')
    
    def get_id(self):
        return self.username
    
class Posts(db.Model):
    __tablename__ = 'Posts'
    id = db.Column(db.Integer, primary_key = True, autoincrement= True)
    filename = db.Column(db.String, unique = True)
    by = db.Column(db.String, db.ForeignKey('User_Details.username'))
    title = db.Column(db.String)
    desc = db.Column(db.String(200))
    date = db.Column(db.String)

class Followers(db.Model):
    __tablename__ = 'Followers'
    follow_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    follower = db.Column(db.String, db.ForeignKey('User_Details.username'))
    following = db.Column(db.String, db.ForeignKey('User_Details.username'))