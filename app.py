from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from os import path
from model import Users, db, Posts, Followers
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'panda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
login_manager.login_view = '/'


UPLOAD_FOLDER = '/static/blog_posts/'
UPLOAD_PFP = '/static/profile_pics/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_PFP'] = UPLOAD_PFP


db.init_app(app)
app.app_context().push()
db.create_all()


@login_manager.user_loader
def load_user(username):
    return Users.query.filter_by(username = username).first()


@app.route('/')
def mainpage():
    return render_template("homepage.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Users.query.filter_by(username = username).first()
        
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                print('Log-In Successful')
                return redirect(url_for('posts'))
            else:
                print('Wrong Password')
        else:
            print('Username does not exist')

    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pfp = request.files['pfp']
        username = request.form['username']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']

        username_exists = Users.query.filter_by(username = username).first()
        email_exists = Users.query.filter_by(email = email).first()
        
        if password1 != password2:
            error = "Passwords don\'t match"
            return render_template("register.html", error = error)
        elif username_exists or email_exists:
            error = "User already exists"
            return render_template("register.html", error = error)
        elif len(password1) < 5:
            error = "Length of password must be more than 5 letters."
            return render_template("register.html", error = error)
        else:
            if pfp.filename == '':
                print('No selected file')
                return redirect(request.url)

            if pfp and allowed_file(pfp.filename):
                okay = secure_filename(pfp.filename)
                pfpname = username + email + okay
                basedir = os.path.abspath(os.path.dirname(__file__))
                pfp.save(basedir + UPLOAD_PFP + pfpname)

            new_user = Users(username = username, pfpname = pfpname, email = email, password = generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('posts'))

    return render_template("register.html")


@login_required
@app.route('/posts', methods=['GET', 'POST'])
def posts():
    following_list = Followers.query.filter_by(follower = current_user.username).all()
    following_list_ = [x.following for x in following_list]
    persons = Users.query.all()
    posts = Posts.query.all()
    posts = sorted(posts, key=lambda d: d.date, reverse= True) 
    for post in posts:
        post.date = datetime.strptime(post.date,"%Y_%m_%d_%H_%M_%S").strftime("%b %d, %Y %I:%M %p")
    empty_list = []
    for i in posts:
        if i.by in following_list_:
            empty_list.append(i)
    return render_template("blog.html", following_list_ = following_list_, posts = empty_list, persons = persons)


@login_required
@app.route('/profile/<string:user>', methods=['GET', 'POST'])
@app.route('/profile', methods=['GET', 'POST'])
def profile(user = None):
    if user:
        username = user
    else:
        username = current_user.username

    following_list = Followers.query.filter_by(follower = username).all()
    following_list_ = [x.following for x in following_list]

    follower_list = Followers.query.filter_by(following = username).all()
    follower_list_ = [x.follower for x in follower_list]

    posts = Posts.query.filter_by(by = username).all()
    for post in posts:
        post.date = datetime.strptime(post.date,"%Y_%m_%d_%H_%M_%S").strftime("%b %d, %Y %I:%M %p")

    users = Users.query.filter_by(username = username).first()
    return render_template("profile_page.html", user = username, users = users, posts = posts[::-1], follower_list_ = follower_list_, following_list_ = following_list_)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('mainpage'))


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_required
@app.route('/create-new-blog', methods=['GET', 'POST'])
def new_blog():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)

        file = request.files['file']
        title = request.form['title']
        desc = request.form['desc']
        date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        user = current_user.get_id()
        
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            okay = secure_filename(file.filename)
            filename = user + date + okay
            basedir = os.path.abspath(os.path.dirname(__file__))
            file.save(basedir + UPLOAD_FOLDER + filename)
        
        data = Posts(by = current_user.username, filename = filename, title = title, desc = desc, date = date)
        db.session.add(data)
        db.session.commit()

        return redirect(url_for('profile'))
    return render_template("new_blog.html")


@login_required
@app.route('/update-blog/<int:id>', methods=['GET', 'POST'])
def update_blog(id):
    if request.method == 'GET':
        blog = Posts.query.filter_by(id = id).first()
        return render_template("update_blog.html", id = id, blog = blog)
    else:
        post = Posts.query.filter_by(id = id).first()
        post.title = request.form['title']
        post.desc = request.form['desc']
        db.session.commit()
        return redirect(url_for('profile'))


@login_required
@app.route('/delete-blog/<int:id>', methods=['GET', 'POST'])
def delete_blog(id):
    post_to_delete = Posts.query.get(id)
    image_to_delete = post_to_delete.filename
    db.session.delete(post_to_delete)
    db.session.commit()

    basedir = os.path.abspath(os.path.dirname(__file__))
    os.remove(os.path.join(basedir + UPLOAD_FOLDER + image_to_delete))

    print("Blog Deleted Successfully!!!")

    posts = Posts.query.all()
    return redirect(url_for('profile'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    people = Users.query.all()
    username = request.form['search']
    people_list_ = [x.username for x in people]
    print(people_list_)
    if username not in people_list_:
        error = "Specified user does not exist!!"
        return render_template("blog.html", error = error)
    else:
        return redirect(url_for('profile', user = username))


@login_required
@app.route('/update-account/<string:user>', methods=['GET', 'POST'])
def update_account(user):
    if request.method == 'GET':
        person = Users.query.filter_by(username = user).first()
        return render_template("update_profile.html", user = user, person = person)
    else:
        people = Users.query.filter_by(username = user).first()
        people.email = request.form['email']
        people.password = generate_password_hash(request.form['password1'])
        db.session.commit()
        print("Account Updated Successfully!!!")
        return redirect(url_for('profile'))


@login_required
@app.route('/delete-account/<string:user>', methods=['GET', 'POST'])
def delete_account(user):
    post_to_delete = Posts.query.filter_by(by = user).all()
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    for post in post_to_delete:
        image_to_delete = post.filename
        os.remove(os.path.join(basedir + UPLOAD_FOLDER + image_to_delete))

    user_to_delete = Users.query.filter_by(username = user).first()
    pfp_to_delete = user_to_delete.pfpname
    os.remove(os.path.join(basedir + UPLOAD_PFP + pfp_to_delete))
    db.session.delete(user_to_delete)

    db.session.commit()
    print("Account Deleted Successfully!!!")
    return redirect(url_for('mainpage'))

    
@login_required
@app.route('/follow/<string:following>', methods=['GET', 'POST'])
def user_follow(following):
    obj = Followers(follower = current_user.username, following = following)
    db.session.add(obj)
    db.session.commit()
    return redirect(request.referrer)


@login_required
@app.route('/unfollow/<string:following>', methods=['GET', 'POST'])
def user_unfollow(following):
    fll = Followers.query.filter_by(following = following, follower = current_user.username).first()
    db.session.delete(fll)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/follow-unfollow-list/<string:user>', methods=['GET', 'POST'])
def follow_unfollow(user):
    following_list = Followers.query.filter_by(follower = user).all()
    following_list_ = [x.following for x in following_list]

    follower_list = Followers.query.filter_by(following = user).all()
    follower_list_ = [x.follower for x in follower_list]

    posts = Posts.query.filter_by(by = user).all()    
    users = Users.query.filter_by(username = user).first()
    return render_template('follow_unfollow.html', user = user, users = users, posts = posts[::-1], follower_list_ = follower_list_, following_list_ = following_list_)

if __name__ == "__main__":
    app.run(debug = True, port = 5000)