from flask import Flask, json, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import os
import boto3
import bcrypt
from werkzeug.utils import secure_filename

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_NAME')

mysql = MySQL(app)

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024
SALT = bcrypt.gensalt()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/getuser/<email>', methods=['GET'])
def getuser(email):
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT email, password, name, phone, date_of_birth, resume_url FROM Users WHERE email = %s', (email,))
    user = cursor.fetchone()

    cursor.close()

    if user:
        return jsonify({"error": "User found"}), 404
    else:
        return jsonify({"success": "User not found"}), 201

@app.route('/signup', methods=['POST'])
def signup():
    data = request.form.get('data')
    if data:
        data = json.loads(data)

    print(data)

    name = data['name']
    email = data['email']
    phone = data['phone']
    dob = data['dob']
    password = data['password']
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), SALT)

    resume = request.files.get('file')

    if resume and allowed_file(resume.filename):
        filename = secure_filename(resume.filename)
        try:
            s3.upload_fileobj(resume, AWS_BUCKET_NAME, f'resumes/{filename}')
            file_url = f'https://{AWS_BUCKET_NAME}.s3.ap-south-1.amazonaws.com/resumes/{filename}'
        except Exception as e:
            return jsonify({"error": "File upload to S3 failed", "message": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type or file size exceeded the limit"}), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            '''INSERT INTO Users (name, email, phone, date_of_birth, password, resume_url) 
               VALUES (%s, %s, %s, %s, %s, %s)''', 
            (name, email, phone, dob, hashed_password, file_url)
        )
        mysql.connection.commit()
        return jsonify({
            'name': name,
            'email': email,
            'phone': phone,
            'dob': dob,
            'resume': file_url
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500

    finally:
        cursor.close()

@app.route('/check-creds', methods=['POST'])
def check_creds():
    email = request.form['email']
    password = request.form['password']

    print(email, password)
    
    cursor = mysql.connection.cursor()

    # Query to select user based on both email and password
    cursor.execute('SELECT email, password, name, phone, date_of_birth, resume_url FROM Users WHERE email = %s', (email,))
    user = cursor.fetchone()
    
    cursor.close()

    if user:
        u_password = user[1]
        if bcrypt.checkpw(password.encode("utf-8"), u_password.encode("utf-8")):
            print("Hogyaaaaaaa")
            return jsonify(
                {
                    "email": user[0],
                    "name": user[2],
                    "phone": user[3],
                    "date_of_birth": user[4],
                    "resume_url": user[5]
                }
            )
        else:
            return jsonify({"error": "Invalid password"}), 403
    else:
        return jsonify({"error": "Email not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
