from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template,request,redirect,url_for,session
import secrets

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)
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
    doctor_id = db.Column(db.Integer)

    appointments_as_patient=db.relationship('Appointment',foreign_keys='Appointment.patient_id',backref='patient_details')
    appointments_as_doctors=db.relationship('Appointment',foreign_keys='Appointment.doctor_id',backref='doctor_details')

    
class Department(db.Model):
    __tablename__='medical_departments' 
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),unique=True,nullable=False)
    description=db.Column(db.Text)

    doctors=db.relationship("User",back_populates="department")

class Appointment(db.Model):
    __tablename__='user_appointment'
    id=db.Column(db.Integer,primary_key=True)
    patient_id=db.Column(db.Integer,db.ForeignKey('user_accounts.id'),nullable=False)
    doctor_id=db.Column(db.Integer,db.ForeignKey('user_accounts.id'),nullable=False)
    date=db.Column(db.String(30))
    time=db.Column(db.String(30))
    reason=db.Column(db.String(200))
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
            department = Department(name=department_name.strip().title())
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
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
            return redirect(url_for('patient_dashboard'))
        elif user and user.role=="doctor":
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
            return redirect(url_for('doctor_dashboard'))
        elif user and user.role=="admin":
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
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
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    doctors=User.query.filter_by(role='doctor').all()
    patients=User.query.filter_by(role='patient').all()
    departments=Department.query.all()
    return render_template('admin_dashboard.html',doctors=doctors,patients=patients,departments=departments)

@app.route('/admin_search')
def admin_search():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    all_doctors = User.query.filter_by(role='doctor').all()
    all_patients = User.query.filter_by(role='patient').all()
    doctors = [d for d in all_doctors if q in d.username.lower()]
    patients = [p for p in all_patients if q in p.username.lower() or q in p.contact]
    return render_template("search_results.html",query=q,doctors=doctors,patients=patients)

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



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/doctors')
def doctors_page():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('doctors.html', doctors=doctors)

@app.route('/delete_doctor/<int:doc_id>',methods=['POST'])
def delete_doctor(doc_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    doctor=User.query.get(doc_id)
    if doctor and doctor.role=='doctor':
        db.session.delete(doctor)
        db.session.commit()
    return redirect(url_for('doctors_page'))

@app.route('/add_doctor',methods=['POST'])
def add_doctor():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    username = request.form['username']
    email = request.form['email']
    contact = request.form['contact']
    dob = datetime.strptime(request.form['dob'], "%Y-%m-%d").date()
    dept_name = request.form['department'].strip().title()
    password = request.form['password']

    curr_doc=User.query.filter_by(username=username).first()
    if curr_doc:
        return redirect(url_for('doctors_page'))
    department = Department.query.filter_by(name=dept_name).first()
    if not department:
        department = Department(name=dept_name.strip().title())
        db.session.add(department)
        db.session.commit()
    new_doctor = User(
        username=username,
        email_address=email,
        contact=contact,
        password=password,
        role='doctor',
        dob=dob,
        dept_ref_id=department.id
    )
    db.session.add(new_doctor)
    db.session.commit()
    return redirect(url_for('doctors_page'))

@app.route('/update_doctor/<int:doc_id>',methods=['POST'])
def update_doctor(doc_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    doctor=User.query.get(doc_id)
    if not doctor or doctor.role!='doctor':
        return redirect(url_for('doctors_page'))
    doctor.username = request.form['username']
    doctor.email_address = request.form['email']
    doctor.contact = request.form['contact']
    doctor.dob = datetime.strptime(request.form['dob'], "%Y-%m-%d").date()

    dept_name = request.form['department'].strip().title()
    department = Department.query.filter_by(name=dept_name).first()
    if not department:
        department = Department(name=dept_name)
        db.session.add(department)
        db.session.commit()

    doctor.dept_ref_id = department.id

    db.session.commit()

    return redirect(url_for('doctors_page'))



@app.route('/edit_doctor/<int:doc_id>')
def edit_doctor(doc_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    doctor = User.query.get_or_404(doc_id)

    if doctor.role != 'doctor':
        return redirect(url_for('doctors_page'))

    return render_template("edit_doctors.html", doctor=doctor)

@app.route('/doctor_details/<int:doc_id>')
def doctor_details(doc_id):
    if 'role' not in session or session['role'] !='admin':
        return redirect(url_for('login'))
    doctor = User.query.get(doc_id)
    if not doctor or doctor.role != 'doctor':
        return redirect(url_for('admin_dashboard'))
    
    return render_template('doctor_details.html', doctor=doctor)

@app.route('/departments')
def departments_page():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))

    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/edit_department/<int:dept_id>')
def edit_department(dept_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    department=Department.query.get(dept_id)
    if not department:
        return redirect(url_for('departments_page'))
    return render_template('edit_department.html', department=department)

@app.route('/update_department/<int:dept_id>',methods=['POST'])
def update_department(dept_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    department=Department.query.get(dept_id)
    if not department:
        return redirect(url_for('departments_page'))
    new_name = request.form['dept_name'].strip().title()

    existing_dept=Department.query.filter_by(name=new_name).first()
    if existing_dept and existing_dept.id!=dept_id:
        return redirect(url_for('departments_page'))
    department.name = new_name
    db.session.commit()

    return redirect(url_for('departments_page'))



@app.route('/add_department',methods=['POST'])
def add_department():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    dept_name=request.form['dept_name'].strip().title()
    if not dept_name:
        return redirect(url_for('admin_dashboard'))
    department_name=Department.query.filter_by(name=dept_name).first()
    if not department_name:
        new_dept=Department(name=dept_name)
        db.session.add(new_dept)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_department/<int:dept_id>',methods=['POST'])
def delete_department(dept_id):
    if 'role' not in session or session['role'] !='admin':
        return redirect(url_for('login'))
    dept=Department.query.get(dept_id)
    if dept:
        db.session.delete(dept)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/patients')
def patients_page():
    patients=User.query.filter_by(role='patient').all()
    doctors=User.query.filter_by(role='doctor').all()
    return render_template('patients.html',patients=patients,doctors=doctors)

@app.route('/add_patients',methods=['POST'])
def add_patient():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    username = request.form['username']
    email = request.form['email']
    contact = request.form['contact']
    dob = datetime.strptime(request.form['dob'], "%Y-%m-%d").date()
    assigned_doctor_id = request.form.get('assigned_doctor')
    existing_patient = User.query.filter_by(username=username).first()
    if existing_patient:
        return redirect(url_for('patients_page'))

    new_patient = User(
        username = username,
        email_address = email,
        contact = contact,
        dob = dob,
        role = 'patient',
        doctor_id = assigned_doctor_id,
        password='patient123')
    

    db.session.add(new_patient)
    db.session.commit()

    return redirect(url_for('patients_page'))

@app.route('/delete_patient/<int:patient_id>',methods=['POST'])
def delete_patient(patient_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    patient = User.query.get(patient_id)

    if patient and patient.role == 'patient':
        db.session.delete(patient)
        db.session.commit()

    return redirect(url_for('patients_page'))

@app.route('/edit_patient/<int:patient_id>')
def edit_patient(patient_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    patient = User.query.get(patient_id)
    doctors = User.query.filter_by(role='doctor').all()

    if not patient or patient.role != 'patient':
        return redirect(url_for('patients_page'))

    return render_template('edit_patient.html', patient=patient, doctors=doctors)

@app.route('/update_patients/<int:patient_id>',methods=['POST'])
def update_patients(patient_id):
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    patient = User.query.get(patient_id)
    if not patient or patient.role != 'patient':
        return redirect(url_for('patients_page'))

    patient.username = request.form['username']
    patient.email_address = request.form['email']
    patient.contact = request.form['contact']
    patient.dob = datetime.strptime(request.form['dob'], "%Y-%m-%d").date()
    patient.dept_ref_id = request.form['assigned_doctor']

    db.session.commit()

    return redirect(url_for('patients_page'))

@app.route('/appointments')
def view_appointments():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    
    appointments=Appointment.query.all()
    patients = User.query.filter_by(role='patient').all()
    doctors = User.query.filter_by(role='doctor').all()

    return render_template('appointments.html', appointments=appointments,patients=patients,doctors=doctors)


@app.route('/book_appointments',methods=['POST','GET'])
def book_appointments():
    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason')

        new_app = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date,
            time=time,
            reason=reason,
            user_status='Booked'
        )

        db.session.add(new_app)
        db.session.commit()

        return redirect(url_for('view_appointments'))
    patients = User.query.filter_by(role='patient').all()
    doctors = User.query.filter_by(role='doctor').all()

    return render_template('book_appointments.html', patients=patients, doctors=doctors)
                









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
