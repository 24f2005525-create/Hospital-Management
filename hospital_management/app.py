from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template,request,redirect,url_for,session



app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)


from datetime import datetime,timezone

class User(db.Model):
    __tablename__='user_accounts'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),unique=True,nullable=False)
    role=db.Column(db.String(50),nullable=False)
    gender=db.Column(db.String(10),nullable=True)
    dob=db.Column(db.Date,nullable=False)
    dept_ref_id=db.Column(db.Integer,db.ForeignKey('medical_departments.id'),nullable=True)
    contact=db.Column(db.String(15),nullable=False)
    registered_on=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
    email_address=db.Column(db.String(100),unique=True,nullable=False)
    password=db.Column(db.String(100),nullable=False)
    department=db.relationship("Department",back_populates="doctors")
    
    

    
class Department(db.Model):
    __tablename__='medical_departments' 
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),unique=True,nullable=False)
    description=db.Column(db.Text)

    doctors=db.relationship("User",back_populates="department")

class Appointment(db.Model):
    __tablename__='user_appointment'
    id=db.Column(db.Integer,primary_key=True)
    date=db.Column(db.String(30))
    time=db.Column(db.String(30))
    user_status=db.Column(db.String(20),default='Booked')


class Treatment(db.Model):
    __tablename__='treatments'
    appointment_id=db.Column(db.Integer,primary_key=True)
    diagnosis=db.Column(db.String(150),nullable=False)
    treatment_name=db.Column(db.String(100))
    prescription=db.Column(db.String(150))
    status=db.Column(db.String(100),default='ongoing')


@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/registration',methods=["POST","GET"])
def registration():
    if request.method=="POST":
        username=request.form['username']
        role=request.form['role']
        department_name=request.form['department']
        dob=request.form['dob']
        gender=request.form['gender']
        contact=request.form['contact']
        email_address=request.form['email_address']
        password=request.form['password']
        confirm_password=request.form['confirm_password']

        if password != confirm_password:
            return render_template('registration.html',error='Passwords do not match')
        

        user=User.query.filter_by(username=username,email_address=email_address).first()
        if user:
            return redirect(url_for('login'))
        
        department = Department.query.filter_by(name=department_name).first()
        if not department:
            department = Department(name=department_name)
            db.session.add(department)
            db.session.commit()
        new_user=User(username=username,
                      role=role,
                      dept_ref_id=department.id,
                      dob=datetime.strptime(dob, "%Y-%m-%d").date(),
                      gender=gender,
                      contact=contact,
                      email_address=email_address,
                      password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registration.html')
        

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        user=User.query.filter_by(username=username,password=password).first()
        if user and user.role=="patient":
            return redirect(url_for('patient_dashboard'))
        elif user and user.role=="doctor":
            return redirect(url_for('doctor_dashboard'))
        elif user and user.role=="admin":
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html',error_message="You are a new user. Please Register Yourself.")

     
    return render_template('login.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/patient_dashboard')
def patient_dashboard():
    return render_template('patient_dashboard.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashoard.html')

@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    err_msg=None
    if request.method=="POST":
        email_address=request.form['email_address']
        user=User.query.filter_by(email_address=email_address).first()
        if user:
            err_msg="A Confirmation link has been sent to your Email Address."
        else:
            err_msg="No account found with that email.Try again"
    return render_template('forgot_password.html',err_msg=err_msg)

    
    return render_template('forgot_password.html')

if __name__== "__main__":
    with app.app_context():
        db.create_all()
        admin_user=User.query.filter_by(username="admin").first()

        if not admin_user:
            admin_user=User(
                username="admin",
                password="ad_min",
                email_address="123hosp@gmail.com",
                role="admin",
                dob=datetime(2002, 1, 1).date(),
                contact="0000000000"
                
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin account created")
        else:
            print("Admin already exists")
    app.run(debug=True)
