from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import os
from passlib.hash import bcrypt  # Import bcrypt for password hashing

from dotenv import load_dotenv
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (CORS) for the frontend to connect

# Database Configuration
app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'your_host')  # Replace with Hostinger DB Host
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'your_username')  # Replace with your DB username
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', 'your_password')  # Replace with your DB password
app.config['MYSQL_DB'] = os.getenv('DB_NAME', 'your_database_name')  # Replace with your DB name

# Initialize MySQL
mysql = MySQL(app)

# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    # Get form data
    email = request.args.get('email')
    password = request.args.get('password')
    name = request.args.get('name')
    phone = request.args.get('phone')
    date_of_birth = request.args.get('dateOfBirth')
    resume_url = request.args.get('resumeUrl')
    
    # Check if the email already exists in the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        return jsonify({"error": "Email already registered."}), 400  # Return a 400 error if email exists
    
    # Hash the password using bcrypt
    hashed_password = bcrypt.hash(password)
    
    # If email doesn't exist, proceed to insert the new user
    query = "INSERT INTO Users (email, password, name, phone, date_of_birth, resume_url) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (email, hashed_password, name, phone, date_of_birth, resume_url))
    mysql.connection.commit()
    
    return jsonify({"message": "User registered successfully!"}), 200

# Profile Details Route (Retrieve user data)
@app.route('/profile/<email>', methods=['GET'])
def get_profile(email):
    cursor = mysql.connection.cursor()

    # Fetch user data from MySQL
    query = "SELECT (email, password, name, phone, date_of_birth, resume_url) FROM Users WHERE email = %s"
    cursor.execute(query, [email])

    user = cursor.fetchone()
    cursor.close()

    if user:
        # Return user data as JSON response
        return jsonify(
            {
                "email": user[0],
                "password": user[1],
                "name": user[2],
                "phone": user[3],
                "date_of_birth": user[4],
                "resume_url": user[5]
            }
        )
    else:
        return jsonify({"error": "User not found"}), 404

# Run the Flask application
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
