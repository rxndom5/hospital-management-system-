-- Create the database
CREATE DATABASE IF NOT EXISTS hospital_management;
USE hospital_management;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS Appointments;
DROP TABLE IF EXISTS Doctors;
DROP TABLE IF EXISTS Patients;

-- Drop existing table if it exists
DROP TABLE IF EXISTS Users;

-- Create the Users table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE,
    Password VARCHAR(100),
    Role VARCHAR(20) DEFAULT 'user' -- Roles can be 'admin' or 'user'
);

-- Insert a sample admin user (use a hashed password)
INSERT INTO Users (Username, Password, Role)
VALUES 
('admin', '$2b$12$eU7vZmjDjCnAnvqlQ0PeQOVTlaQ5erGkvUtw5y5rMgC9KowR9CqUm', 'admin'); -- Password: admin123
-- Create the Patients table
CREATE TABLE Patients (
    PatientID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50),
    Age INT,
    Gender VARCHAR(10),
    Contact VARCHAR(20),
    Address VARCHAR(100)
);

-- Create the Doctors table
CREATE TABLE Doctors (
    DoctorID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50),
    Specialty VARCHAR(50),
    Contact VARCHAR(20)
);

-- Create the Appointments table
CREATE TABLE Appointments (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT,
    DoctorID INT,
    AppointmentDate DATE,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE RESTRICT,
    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID) ON DELETE CASCADE
);

-- Insert sample data into Patients table
INSERT INTO Patients (Name, Age, Gender, Contact, Address)
VALUES 
('Alice Smith', 30, 'Female', '1234567890', '123 Maple St.'),
('Bob Johnson', 45, 'Male', '9876543210', '456 Oak St.'),
('Cathy Brown', 28, 'Female', '5551234567', '789 Pine St.');

-- Insert sample data into Doctors table
INSERT INTO Doctors (Name, Specialty, Contact)
VALUES 
('Dr. John Doe', 'Cardiology', '1112223333'),
('Dr. Jane Roe', 'Neurology', '4445556666'),
('Dr. Sam White', 'Orthopedics', '7778889999');

-- Insert sample data into Appointments table
INSERT INTO Appointments (PatientID, DoctorID, AppointmentDate)
VALUES 
(1, 1, '2024-11-15'),
(2, 2, '2024-11-16'),
(3, 3, '2024-11-17');

-- Create a trigger to prevent deleting patients with existing appointments
DELIMITER //
CREATE TRIGGER prevent_patient_delete
BEFORE DELETE ON Patients
FOR EACH ROW
BEGIN
    DECLARE appointment_count INT;
    SELECT COUNT(*) INTO appointment_count FROM Appointments WHERE PatientID = OLD.PatientID;
    IF appointment_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete patient with existing appointments.';
    END IF;
END//
DELIMITER ;

-- Trigger to prevent deletion of doctors who have appointments
DELIMITER //
CREATE TRIGGER prevent_doctor_delete
BEFORE DELETE ON Doctors
FOR EACH ROW
BEGIN
    DECLARE doctor_appointments INT;
    SELECT COUNT(*) INTO doctor_appointments
    FROM Appointments
    WHERE DoctorID = OLD.DoctorID;
    
    IF doctor_appointments > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete doctor with existing appointments';
    END IF;
END//
DELIMITER ;

-- SQL query to find the doctor with the most appointments
SELECT d.Name AS DoctorName, 
       COUNT(a.AppointmentID) AS AppointmentCount 
FROM Appointments a
JOIN Doctors d ON a.DoctorID = d.DoctorID
GROUP BY d.Name
ORDER BY AppointmentCount DESC 
LIMIT 1; -- Returns the doctor with the most appointments

-- SQL query to find patients who have no appointments
SELECT * FROM Patients
WHERE PatientID NOT IN (SELECT PatientID FROM Appointments);
