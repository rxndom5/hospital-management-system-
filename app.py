from flask import Flask, render_template, request, redirect, flash, url_for, session
import mysql.connector
from functools import wraps
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Connection
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="shashank",
    database="hospital_management"
)
cursor = db.cursor()

# Utility Function: Check if User is Admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access this page.", "error")
            return redirect('/login')
        elif session.get('role') != 'admin':
            flash("Access denied. Admins only.", "error")
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


# Route: Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Route: Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        role = request.form.get('role', 'user')
        
        try:
            cursor.execute("INSERT INTO Users (Username, Password, Role) VALUES (%s, %s, %s)", 
                           (username, hashed_password, role))
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect('/login')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "error")
    
    return render_template('signup.html')

# Route: Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM Users WHERE Username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['logged_in'] = True
            session['username'] = user[1]
            session['role'] = user[3]
            flash("Logged in successfully.", "success")
            return redirect('/')
        else:
            flash("Invalid username or password.", "error")
    
    return render_template('login.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/login')

# Route: Patients Page (accessible to all logged-in users)
@app.route('/patients')
def patients():
    if 'logged_in' not in session:
        flash("Please log in to view this page.", "error")
        return redirect('/login')

    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    return render_template('patients.html', patients=patients)

# Route: Add New Patient (accessible to admins)
@app.route('/add_patient', methods=['POST'])
@admin_required
def add_patient():
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    contact = request.form['contact']
    address = request.form['address']
    cursor.execute("INSERT INTO Patients (Name, Age, Gender, Contact, Address) VALUES (%s, %s, %s, %s, %s)",
                   (name, age, gender, contact, address))
    db.commit()
    return redirect('/patients')

# Route: Edit Patient
@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@admin_required
def edit_patient(patient_id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']
        cursor.execute("UPDATE Patients SET Name=%s, Age=%s, Gender=%s, Contact=%s, Address=%s WHERE PatientID=%s",
                       (name, age, gender, contact, address, patient_id))
        db.commit()
        return redirect('/patients')
    cursor.execute("SELECT * FROM Patients WHERE PatientID=%s", (patient_id,))
    patient = cursor.fetchone()
    return render_template('edit_patient.html', patient=patient)

# Route: Delete Patient
@app.route('/delete_patient/<int:patient_id>')
@admin_required
def delete_patient(patient_id):
    try:
        cursor.execute("DELETE FROM Patients WHERE PatientID=%s", (patient_id,))
        db.commit()
        flash("Patient deleted successfully.", "success")
    except mysql.connector.Error as e:
        flash(str(e), "error")  # Display the trigger error message here
    return redirect('/patients')


# Route: Doctors Page (with most popular doctor)
@app.route('/doctors')
def doctors():
    if 'logged_in' not in session:
        flash("Please log in to view this page.", "error")
        return redirect('/login')


    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()

    # Query to find the doctor with the most appointments
    cursor.execute("""
    SELECT d.Name, COUNT(a.AppointmentID) 
    FROM Appointments a
    JOIN Doctors d ON a.DoctorID = d.DoctorID
    GROUP BY d.Name
    ORDER BY COUNT(a.AppointmentID) DESC 
    LIMIT 1;
    """)
    most_popular_doctor = cursor.fetchone()

    return render_template('doctors.html', doctors=doctors, most_popular_doctor=most_popular_doctor)

# Route: View Appointments for a Doctor
@app.route('/doctor_appointments/<int:doctor_id>')
def doctor_appointments(doctor_id):
    cursor.execute("""
    SELECT p.Name AS PatientName, a.AppointmentDate 
    FROM Appointments a
    JOIN Patients p ON a.PatientID = p.PatientID
    WHERE a.DoctorID = %s;
    """, (doctor_id,))
    appointments = cursor.fetchall()
    return render_template('doctor_appointments.html', appointments=appointments)


# Route: Appointments Page
@app.route('/appointments')
def appointments():
    if 'logged_in' not in session:
        flash("Please log in to view this page.", "error")
        return redirect('/login')

    cursor.execute("""
    SELECT Appointments.AppointmentID, Patients.Name AS Patient, Doctors.Name AS Doctor, AppointmentDate
    FROM Appointments
    JOIN Patients ON Appointments.PatientID = Patients.PatientID
    JOIN Doctors ON Appointments.DoctorID = Doctors.DoctorID
    """)
    appointments = cursor.fetchall()
    return render_template('appointments.html', appointments=appointments)

# Route: Add Appointment Page
@app.route('/add_appointment', methods=['GET', 'POST'])
@admin_required
def add_appointment():
    if request.method == 'POST':
        patient_id = request.form['patient']
        doctor_id = request.form['doctor']
        appointment_date = request.form['appointment_date']
        cursor.execute("""
            INSERT INTO Appointments (PatientID, DoctorID, AppointmentDate)
            VALUES (%s, %s, %s)
        """, (patient_id, doctor_id, appointment_date))
        db.commit()
        flash("Appointment added successfully!", "success")
        return redirect('/appointments')
    
    # Fetch Patients and Doctors to populate the dropdowns
    cursor.execute("SELECT * FROM Patients")
    patients = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()
    
    return render_template('add_appointment.html', patients=patients, doctors=doctors)

# Route: Delete Appointment
@app.route('/delete_appointment/<int:appointment_id>', methods=['GET'])
@admin_required
def delete_appointment(appointment_id):
    try:
        # Delete appointment from database
        cursor.execute("DELETE FROM Appointments WHERE AppointmentID = %s", (appointment_id,))
        db.commit()
        flash("Appointment deleted successfully.", "success")
    except mysql.connector.Error as e:
        flash(f"Error deleting appointment: {e}", "error")  # Error handling for any issues
    return redirect('/appointments')

# Route: Fetch Appointments for a Specific Patient
@app.route('/patient_appointments/<int:patient_id>')
def patient_appointments(patient_id):
    cursor.execute("""
    SELECT 
        p.Name AS PatientName, 
        a.AppointmentDate, 
        d.Name AS DoctorName
    FROM Appointments a
    JOIN Patients p ON a.PatientID = p.PatientID
    JOIN Doctors d ON a.DoctorID = d.DoctorID
    WHERE p.PatientID = %s;
    """, (patient_id,))
    appointments = cursor.fetchall()
    return render_template('patient_appointments.html', appointments=appointments, patient_id=patient_id)


# Route: Add Doctor
@app.route('/add_doctor', methods=['POST'])
@admin_required
def add_doctor():
    if request.method == 'POST':
        name = request.form['name']
        specialty = request.form['specialty']
        contact = request.form['contact']
        cursor.execute("INSERT INTO Doctors (Name, Specialty, Contact) VALUES (%s, %s, %s)", (name, specialty, contact))
        db.commit()
        return redirect('/doctors')

# Route: Edit Doctor
@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@admin_required
def edit_doctor(doctor_id):
    if request.method == 'POST':
        name = request.form['name']
        specialty = request.form['specialty']
        contact = request.form['contact']
        cursor.execute("UPDATE Doctors SET Name = %s, Specialty = %s, Contact = %s WHERE DoctorID = %s", 
                       (name, specialty, contact, doctor_id))
        db.commit()
        return redirect('/doctors')
    
    cursor.execute("SELECT * FROM Doctors WHERE DoctorID = %s", (doctor_id,))
    doctor = cursor.fetchone()
    return render_template('edit_doctor.html', doctor=doctor)

# Route: Delete Doctor
@app.route('/delete_doctor/<int:doctor_id>', methods=['GET'])
@admin_required
def delete_doctor(doctor_id):
    try:
        cursor.execute("DELETE FROM Doctors WHERE DoctorID = %s", (doctor_id,))
        db.commit()
        flash("Doctor deleted successfully.", "success")
    except mysql.connector.Error as e:
        flash(str(e), "error")  # Display the trigger error message here
    return redirect('/doctors')

# Route: View Patients with No Appointments
@app.route('/patients_without_appointments')
def patients_without_appointments():
    cursor.execute("""
    SELECT * FROM Patients
    WHERE PatientID NOT IN (SELECT PatientID FROM Appointments);
    """)
    patients_without_appointments = cursor.fetchall()
    return render_template('patients_without_appointments.html', patients=patients_without_appointments)


if __name__ == '__main__':
    app.run(debug=True)
