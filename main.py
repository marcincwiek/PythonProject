import os
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_security import Security, UserMixin, RoleMixin, \
    SQLAlchemyUserDatastore, current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy

# Konfiguracja aplikacji
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'developerskie')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'jakas-sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_LOGIN_URL'] = '/login'  # URL strony logowania
app.config['SECURITY_LOGOUT_URL'] = '/logout'  # URL wylogowania
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/login'  # Gdzie przekierować po wylogowaniu
app.config['SECURITY_POST_LOGIN_VIEW'] = '/'  # Gdzie przekierować po zalogowaniu
app.config['SECURITY_POST_REGISTER_VIEW'] = '/'  # Gdzie przekierować po rejestracji

# Formularz
class TestForm(FlaskForm):
    name = StringField("Jak masz na imię?", validators=[DataRequired()])
    submit = SubmitField("Zatwierdź")

# Inicjalizacja bazy danych
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
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)  # Wymagane od wersji 4.0.0
    roles = db.relationship('Role', secondary=roles_user, backref=db.backref('users'))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.fs_uniquifier:
            import uuid
            self.fs_uniquifier = str(uuid.uuid4())

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(255), db.ForeignKey('user.fs_uniquifier'))

# Utworzenie obiektu UserDatastore
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

# Niestandardowy renderer formularzy
def custom_security_render_template(template, **context):
    if 'form' not in context:
        from flask_security.forms import LoginForm  # Import domyślnego formularza logowania
        context['form'] = LoginForm()  # Upewnij się, że obiekt `form` jest dostępny
    return render_template(template, **context)

# Rejestracja obiektu Security z niestandardowym rendererem
security = Security(app, user_datastore, render_template=custom_security_render_template)

# Widoki
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

@app.route("/logout")
@login_required
def logout():
    logout_user()  # Wylogowuje użytkownika
    return redirect(url_for('security.login'))  # Przekierowuje na stronę logowania

@app.route("/toggle-status/<int:task_id>", methods=["POST"])
@login_required
def toggle_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.get_id():
        task.completed = 'completed' in request.form
        db.session.commit()
    return redirect(url_for('index'))

@app.route("/delete-task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.get_id():
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route("/delete-note/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id == current_user.get_id():
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for("notatnik"))

@app.route('/user/<name>')
@login_required
def user(name):
    return render_template("user.html", user_name=name)

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

@app.route('/kot')
@login_required
def kot():
    return render_template("kot.html")

@app.route("/notatnik", methods=["GET", "POST"])
@login_required
def notatnik():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            new_note = Note(content=content, user_id=current_user.get_id())
            db.session.add(new_note)
            db.session.commit()
            flash("Notatka zapisana!", "success")
        else:
            flash("Treść notatki nie może być pusta!", "danger")

    notes = Note.query.filter_by(user_id=current_user.get_id()).all()
    return render_template("notatnik.html", notes=notes)




if __name__ == "__main__":
    # Jeśli baza danych jeszcze nie istnieje, odkomentuj poniższą linię
    # with app.app_context():
    #     db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
