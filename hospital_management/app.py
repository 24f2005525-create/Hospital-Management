from flask import Flask
from flask_sqlalchemy import SQLAlchemy




app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)


from datetime import datetime,timezone

class User(db.Model):
    __tablename__='user_accounts'
    id=db.Column(db.Integer,primary_key=True)
    role=db.Column(db.String(50),nullable=False)
    gender=db.Column(db.String(10),nullable=True)
    dept_ref_id=db.Column(db.Integer,db.ForeignKey('medical_departments.id'),nullable=True)
    username=db.Column(db.String(100),unique=True,nullable=False)
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
                
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin account created")
        else:
            print("Admin already exists")
    app.run(debug=True)
