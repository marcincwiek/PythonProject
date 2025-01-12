import os
from flask import Flask, request, render_template, redirect, url_for
from flask_security import Security, UserMixin, RoleMixin, \
    SQLAlchemyUserDatastore, current_user, login_required
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

db = SQLAlchemy(app)

roles_user = db.Table(
    'roles_users',
    db.Column('user_id', db.ForeignKey('user.id')),
    db.Column('role_id', db.ForeignKey('role.id')),
)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.String(255), db.ForeignKey('user.fs_uniquifier'))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    description = db.Column(db.String(128))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)  # Wyamagane od wersji 4.0.0
    roles = db.relationship('Role', secondary=roles_user, backref=db.backref('users'))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.fs_uniquifier:
            import uuid
            self.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route("/")
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.get_id())
    return render_template("index.html", todo_list=tasks)

@app.route("/add-task", methods=["POST"])
@login_required
def add():
    new_task = Task(
        title=request.form["item_text"],
        user_id=current_user.get_id()
    )
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("index"))
   
if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()    
    app.run(host='0.0.0.0', port=5001, debug=True)
