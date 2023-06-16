from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

#----------------------------------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'veryshhhhhkey'
db = SQLAlchemy(app)
app.app_context().push()

#----------------------------------------------------------------------------------------------------------------------------------------------

manager = LoginManager(app)
manager.init_app
manager.login_view = "login"

@manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#----------------------------------------------------------------------------------------------------------------------------------------------

# Define User model for the database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    cars = db.relationship('Car', backref='user', lazy=True)

# Define Car Model
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


#db.create_all()
#----------------------------------------------------------------------------------------------------------------------------------------------
# Registration text-boxes
class Regisration(FlaskForm):
    # Username field is stringfield, thus the characters input can be seen by the user
    username = StringField(validators=[InputRequired(), Length(min=4, max=15)], render_kw={'placeholder': "Username"})
    # Password field is a passwordfield, cannot be seen. Max here is different to the one in db.String() above because once the password is hashed, the length stored on the .db will be different
    password = PasswordField(validators=[InputRequired(), Length(min=5, max=30)], render_kw={'placeholder': "Password"})
    submit = SubmitField("Register")

    # Checks for existing username
    def check_username(self, username):
        existing_username = User.query.filter_by(username=username.data).first()
        if existing_username:
            raise ValidationError(
                "This username already exists. Please choose a different username or log in.")



# Log-in text-boxes
class Login(FlaskForm):
    # Username field is stringfield, thus the characters input can be seen by the user
    username = StringField(validators=[InputRequired(), Length(min=4, max=15)], render_kw={'placeholder': "Username"})
    # Password field is a passwordfield, cannot be seen. Max here is different to the one in db.String() above because once the password is hashed, the length stored on the .db will be different
    password = PasswordField(validators=[InputRequired(), Length(min=5, max=30)], render_kw={'placeholder': "Password"})
    submit = SubmitField("Login")


#----------------------------------------------------------------------------------------------------------------------------------------------
# Home page
@app.route('/')
def home():
    return render_template('home.html')
#----------------------------------------------------------------------------------------------------------------------------------------------
# Login page
@app.route('/login,', methods = ['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)
#----------------------------------------------------------------------------------------------------------------------------------------------
# Register page
@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = Regisration()

    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hash_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)
#----------------------------------------------------------------------------------------------------------------------------------------------
# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user_cars = current_user.cars
    total_cost = sum(float(car.cost) for car in user_cars)
    return render_template('dashboard.html', user_cars=user_cars, total_cost=total_cost)

#----------------------------------------------------------------------------------------------------------------------------------------------
# Make cost
@app.route('/car/create', methods=['POST'])
@login_required
def create_car():
    date = request.form.get('date')
    cost = request.form.get('cost')

    car = Car(date=date, cost=cost, user=current_user)
    db.session.add(car)
    db.session.commit()

    return redirect(url_for('dashboard'))
#----------------------------------------------------------------------------------------------------------------------------------------------
# Delete button
@app.route('/car/delete/<int:car_id>', methods=['POST'])
@login_required
def delete_car(car_id):
    car = Car.query.get(car_id)
    if car:
        db.session.delete(car)
        db.session.commit()
        flash('Car deleted successfully.', 'success')
    else:
        flash('Car not found.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
