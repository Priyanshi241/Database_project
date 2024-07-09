from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error
from prettytable import PrettyTable
import os
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@server/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Student(db.Model):
    __tablename__ = 'students'
    StudentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50), nullable=False)
    DateOfBirth = db.Column(db.Date)
    Gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    Email = db.Column(db.String(100), unique=True)
    PhoneNumber = db.Column(db.String(10))
    EnrollmentDate = db.Column(db.Date)

# Database connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("host"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        if connection.is_connected():
            print("Connection to MySQL DB successful")
            return connection
        else:
            print("Failed to connect to MySQL DB")
            return None
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

# Create Students table if not exists
def create_students_table(connection, cursor):
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS Students (
            StudentID INT AUTO_INCREMENT PRIMARY KEY,
            FirstName VARCHAR(50) NOT NULL,
            LastName VARCHAR(50) NOT NULL,
            DateOfBirth DATE,
            Gender ENUM('Male', 'Female', 'Other'),
            Email VARCHAR(100) UNIQUE,
            PhoneNumber CHAR(10),
            EnrollmentDate DATE 
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
        print("Students table created successfully.")
    except Error as e:
        print(f"Error creating Students table: {e}")

# Validate phone number format
def is_valid_phone_number(phone_number):
    pattern = r'^[9876]\d{9}$'
    return bool(re.match(pattern, phone_number))

# Validate name format
def validate_name(name):
    pattern = r'^[a-zA-Z]{1,50}$'
    return bool(re.match(pattern, name))

# Validate email format
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Route for the home page
@app.route("/")
def home():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.close()
    connection.close()
    return render_template("index.html")

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    
    if request.method == "POST":
        errors = []

        first_name = request.form["first_name"]
        if not validate_name(first_name):
            errors.append("Invalid first name")

        last_name = request.form["last_name"]
        if not validate_name(last_name):
            errors.append("Invalid last name")

        date_of_birth = request.form["date_of_birth"]
        gender = request.form["gender"]

        email = request.form["email"]
        if not validate_email(email):
            errors.append("Invalid email")

        phone_number = request.form["phone_number"]
        if not is_valid_phone_number(phone_number):
            errors.append("Invalid phone number")

        if errors:
            return render_template("add_student.html", errors=errors)

        connection = create_connection()
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO Students (FirstName, LastName, DateOfBirth, Gender, Email, PhoneNumber)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (first_name, last_name, date_of_birth, gender, email, phone_number))
        connection.commit()

        cursor.close()
        connection.close()
        return render_template("sucess.html")

    return render_template("add_student.html")



@app.route('/show_students_route')
def show_students_route():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    show_students_query = "SELECT * FROM Students"
    cursor.execute(show_students_query)
    students = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('show_students_route.html', students=students)


@app.route("/delete",methods=["GET","POST"])
def delete():
    if request.method == "POST":
        student_id = request.form["student_id"]
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        delete_query = "DELETE FROM Students WHERE StudentID = %s"
        cursor.execute(delete_query, (student_id,))
        connection.commit()
        print("Student deleted successfully.")
        cursor.close()
        connection.close()
        return render_template("sucess.html")
    return render_template("delete.html")


@app.route('/update_student', methods=["GET", "POST"])
def update_student():
    if request.method == "POST":
        if 'search' in request.form:
            student_id = request.form.get("student_id")
            connection = create_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Students WHERE StudentID = %s", (student_id,))
            student = cursor.fetchone()
            cursor.close()
            connection.close()
            if student:
                return render_template("update_student.html", student=student)
            else:
                return render_template("update_student.html", error="Student not found", student=None)

        elif 'update' in request.form:
            student_id = request.form.get("student_id")
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            date_of_birth = request.form.get("date_of_birth")
            gender = request.form.get("gender")
            email = request.form.get("email")
            phone_number = request.form.get("phone_number")
            enrollment_date = request.form.get("enrollment_date")

            update_fields = []
            update_values = []

            if first_name:
                update_fields.append("FirstName = %s")
                update_values.append(first_name)
            if last_name:
                update_fields.append("LastName = %s")
                update_values.append(last_name)
            if date_of_birth:
                update_fields.append("DateOfBirth = %s")
                update_values.append(date_of_birth)
            if gender and gender != "Select":
                update_fields.append("Gender = %s")
                update_values.append(gender)
            if email:
                update_fields.append("Email = %s")
                update_values.append(email)
            if phone_number:
                update_fields.append("PhoneNumber = %s")
                update_values.append(phone_number)
            if enrollment_date:
                update_fields.append("EnrollmentDate = %s")
                update_values.append(enrollment_date)

            if not update_fields:
                return "No fields to update", 400

            update_query = "UPDATE Students SET "
            update_query += ", ".join(update_fields)
            update_query += " WHERE StudentID = %s"
            update_values.append(student_id)

            connection = create_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(update_query, update_values)
            connection.commit()
            cursor.close()
            connection.close()
            
            return render_template("sucess.html")

    return render_template("update_student.html", student=None)

@app.route("/search_student", methods=["GET", "POST"])
def search_student():
    students = []
    if request.method == "POST":
        column = request.form.get("column")
        value = request.form.get("value")
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        search_query = f"SELECT * FROM Students WHERE {column} = %s"
        cursor.execute(search_query, (value,))
        students = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template("search_student.html", students=students)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        create_students_table(connection, cursor)
        cursor.close()
        connection.close()
    app.run(debug=True,port=3000)