from flask import Flask, json, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import boto3
import pyotp
import bcrypt
import traceback
import redis

from my_ats import evaluate_resume_content

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

redis_client = redis.StrictRedis(host='redis://red-ctgv29u8ii6s73bghet0', port=6379, db=0, decode_responses=True)

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

SECRET_BASE = pyotp.random_base32()
totp = pyotp.TOTP(SECRET_BASE, digits=6)

app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

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

@app.route('/evaluate-resume/<email>', methods=['GET'])
def evaluate_resume(email):
    """
    Flask endpoint to evaluate a resume's ATS score.
    :param email: User email to fetch the resume link from the database.
    """
    try:
        # 1. Retrieve Resume URL from MySQL Database
        cursor = mysql.connection.cursor()
        query = "SELECT resume_url FROM Users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({
                "email": email,
                "message": "No resume found for the provided email."
            }), 404
        
        resume_url = result[0]  # Extract resume_url
        cursor.close()

        # 2. Extract S3 Bucket and Key from the Resume URL
        if not resume_url.startswith("https://"):
            return jsonify({"message": "Invalid S3 URL format."}), 400
        
        # Assuming the S3 URL format is: https://<bucket-name>.s3.<region>.amazonaws.com/<file-key>
        parts = resume_url.split('/')
        bucket_name = parts[2].split('.')[0]  # Extract bucket name
        file_key = '/'.join(parts[3:])  # Extract the file path (key)

        # 3. Fetch Resume from S3
        try:
            s3_object = s3.get_object(Bucket=bucket_name, Key=file_key)
            resume_content = s3_object['Body'].read()  # File content in bytes
        except Exception as s3_error:
            print(f"S3 Error: {s3_error}")
            return jsonify({
                "email": email,
                "message": "Failed to fetch resume from S3."
            }), 500

        # 4. Evaluate ATS Score
        ats_score = evaluate_resume_content(resume_content)

        # 5. Respond with ATS Score
        return jsonify({
            "email": email,
            "ats_score": ats_score,
            "message": "Resume evaluated successfully."
        }), 200

    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return jsonify({
            "email": email,
            "message": "An unexpected error occurred. Please try again later."
        }), 500
    
@app.route('/send-otp/<email>', methods=['GET'])
def send_otp(email):
    try:
        if not email or '@' not in email:
            return jsonify({"error": "Valid email is required"}), 400

        otp = totp.now()
        redis_client.setex(f"otp:{email}", 120, otp)

        subject = "Your OTP Code"
        body = f"Your OTP for registration is: {otp}. This OTP is valid for 2 minutes."
        sender = os.getenv('MAIL_USERNAME')
        message = Message(subject=subject, recipients=[email], body=body, sender=sender)
        mail.send(message)

        return jsonify({"message": "OTP sent successfully"}), 200

    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        return jsonify({"error": "Failed to send OTP"}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        email = request.form['email']
        otp = request.form['otp']

        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        stored_otp = redis_client.get(f"otp:{email}")

        if not stored_otp:
            return jsonify({"message": "OTP expired or invalid"}), 403

        if otp == stored_otp:
            redis_client.delete(f"otp:{email}")
            return jsonify({"message": "OTP verified successfully"}), 200
        else:
            return jsonify({"message": "Incorrect OTP"}), 403

    except Exception as e:
        print(f"Error verifying OTP: {str(e)}")
        return jsonify({"error": "Failed to verify OTP"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
