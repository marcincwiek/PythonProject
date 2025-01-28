import os
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_security import Security, UserMixin, RoleMixin, \
    SQLAlchemyUserDatastore, current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False


# Formularz
class TestForm(FlaskForm):
    name = StringField("Jak masz na imię?", validators=[DataRequired()])
    submit = SubmitField("Zatwierdź")

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

#klasa note
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(255), db.ForeignKey('user.fs_uniquifier'))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.route("/lista")
@login_required
def index():
        # Filtrujemy zadania na podstawie statusu
    tasks_to_do = Task.query.filter_by(user_id=current_user.get_id(), completed=False).all()
    completed_tasks = Task.query.filter_by(user_id=current_user.get_id(), completed=True).all()
    return render_template("index.html", tasks_to_do=tasks_to_do, completed_tasks=completed_tasks)


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

@app.route("/logout")
@login_required
def logout():
    logout_user()  # Wylogowuje użytkownika
    return redirect(url_for('login'))  # Przekierowuje na stronę logowania

#przycisk do zmiany ukończenie/nieukończenia czynności
@app.route("/toggle-status/<int:task_id>", methods=["POST"])
@login_required
def toggle_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.get_id():
        task.completed = 'completed' in request.form
        db.session.commit()  
    return redirect(url_for('index'))  

#przycisk do usuwania 
@app.route("/delete-task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.get_id():
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

# Profil użytkownika
@app.route('/user/<name>')
@login_required
def user(name):
    return render_template("user.html", user_name = name)

# Testowy formularz
@app.route('/form', methods=['GET', 'POST'])
@login_required
def form():
    name = None
    form = TestForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''    
        flash("Form Submitted Successfully")
    return render_template("form.html", name=name, form=form)

# Koty, koty, koty, koty
@app.route('/kot')
@login_required
def kot():
    return render_template("kot.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def notatnik():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            new_note = Note(content=content, user_id=current_user.get_id())
            db.session.add(new_note)
            db.session.commit()
    notes = Note.query.filter_by(user_id=current_user.get_id()).all()
    return render_template("notatnik.html", notes=notes)

@app.route("/delete-note/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id == current_user.get_id():
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for("notatnik"))


if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()    
    app.run(host='0.0.0.0', port=5001, debug=True) 