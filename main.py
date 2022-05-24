from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from sqlalchemy.orm import relationship
import datetime

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CREATE TABLE IN DB
class User(UserMixin, db.Model):
    #__tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("Blogpost")
    comments = relationship("Comment")

class Blogpost(db.Model):
    #__tablename__ = "blog_posts"
    blog_id = db.Column(db.Integer, primary_key=True)    
    #author = db.column(db.String, db.ForeignKey("user.name"))  
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), default=datetime.datetime.utcnow())
    body = db.Column(db.Text, nullable=False)
    #img_url = db.Column(db.String(250), nullable=True)   
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = relationship("Comment")


class Comment(db.Model):
    #__tablename__ = "comments"
    comment_id = db.Column(db.Integer, primary_key=True)   
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #comment_author = db.Column(db.String, db.ForeignKey("user.name"))
    parent_post = db.Column(db.Text, db.ForeignKey('blogpost.blog_id'))



@app.route('/')
def home():
    # Every render_template has a logged_in variable set.
    return render_template("index.html", user=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for("secrets"))

        login_user(new_user)
    return render_template("register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
    
        user = User.query.filter_by(email=email).first()
        #Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('content'))

    return render_template("login.html", logged_in=current_user.is_authenticated)

@app.route("/post-upload", methods=["GET", "POST"])
def post_upload():
    if request.method == "POST":
        #user = request.user.is_authenticated
        new_post = Blogpost(
            title = request.form.get('title'),
            subtitle = request.form.get('subtitle'),
            body = request.form.get('body'),
        )
        db.session.add(new_post)
        db.session.commit() 
        return render_template('post.html')
    return render_template("post.html")

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    #form = CommentForm()
    requested_post = Blogpost.query.get(post_id)

    #if form.validate_on_submit():
    if request.method == "POST":
    
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

            new_comment = Comment(
                text = request.form.get('text'),
                author = request.form.get('comment_author'),
                post = request.form.get('parent_post')
            )

            db.session.add(new_comment)
            db.session.commit()

    return render_template("post.html", post=requested_post, current_user=current_user)
  
@app.route('/content')
@login_required
def content():
    print(current_user.name)
    requested_content = Blogpost.query.all()
    print(requested_content)
    return render_template("content.html", 
        all_posts=requested_content,
        )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/download')
def download():
    return send_from_directory('static', filename="files/cheat_sheet.pdf")

if __name__ == "__main__":
    app.run(debug=True)
