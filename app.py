from io import BytesIO
import uuid
from flask import Flask, jsonify, render_template, request, make_response,redirect, send_file, url_for, session, abort
import requests
from transcript import uploadAudioRoute
import os
import pymongo
from flask_pymongo import PyMongo
from datetime import timedelta
import secrets
from flask_mail import Mail
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from google.cloud import storage
from models import User
from flask_cors import CORS
import requests
from google.oauth2 import id_token
from models import User  
from google.auth.transport import requests as google_requests
import jwt  # Make sure to import jwt library
import logging
import datetime
from dotenv import load_dotenv
import pdfkit

app = Flask(__name__)
# Load environment variables from .env file
load_dotenv()

CORS(app)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'your_secret_key_here' with your actual secret key
app.secret_key = os.getenv('SECRET_KEY')



@app.route('/search-by-date', methods=['POST'])
def search_by_date():
    # Your server-side code for searching by date
    pass

@app.route('/search-by-title', methods=['POST'])
def search_by_title():
    # Your server-side code for searching by title
    pass

@app.route('/search-meeting', methods=['POST'])
def search_meeting():
    if 'username' not in session:
        abort(401)  # Unauthorized

    try:
        currently_logged_in_user = session["username"]
        search_date = request.json.get('meeting_date')
        search_title = request.json.get('meeting_title')

        # Query the database based on the search criteria
        MONGODB_URI = os.getenv('MONGO_URI')
        myclient = pymongo.MongoClient(MONGODB_URI)
        mydb = myclient["TranscriptForge"]
        mycol = mydb["Meeting_details"]

        search_results = []
        for x in mycol.find({"UserEmail": currently_logged_in_user, "Date": search_date, "Meeting_Name": search_title}):
            summary = x['Summary']
            meeting_name = x['Meeting_Name']
            date = x['Date']
            recording_url = x['RecordingURL']
            recording_name = os.path.basename(recording_url)
            search_results.append({
                "summary": summary,
                "Meeting_Name": meeting_name,
                "Date": date,
                "recording_name": recording_name
            })

        return jsonify(search_results)

    except Exception as e:
        print(f"Error searching: {e}")
        return jsonify({'error': 'An error occurred during search'}), 500


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    # Get transcript data from the request
    transcript_data = request.json['transcript']

    # Create HTML content for the PDF
    html_content = '<html><body>'
    for entry in transcript_data:
        html_content += f'<p><strong>{entry["speaker"]}:</strong> [{entry["start_time"]}] {entry["transcription"]}</p>'
    html_content += '</body></html>'

    # Configure PDF options
    pdf_options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'no-outline': None
    }

    # Generate PDF from HTML content
    pdf = pdfkit.from_string(html_content, False, options=pdf_options)

    # Create BytesIO buffer to hold PDF content
    pdf_buffer = BytesIO(pdf)

    # Seek to the beginning of the buffer
    pdf_buffer.seek(0)

    # Send the PDF file as a response
    response = send_file(pdf_buffer, attachment_filename='meeting_transcript.pdf', as_attachment=True)
    return response

def create_new_user_in_database(user_id):
    # Create a new user object
    new_user = User(user_id=user_id)
    
    # Add the user to the session and commit the transaction
    db.session.add(new_user)
    db.session.commit()
    
# Register the blueprint from abc.py
app.register_blueprint(uploadAudioRoute, url_prefix='/uploadAudioRoute_prefix')

# Access Google OAuth Configuration variables
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')

# Flask-Mail configuration for Gmail
# Setting up Flask-Mail to use Gmail SMTP server for sending emails.
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)


# Secret key for session management
app.secret_key = os.getenv('SECRET_KEY')

# Setting session lifetime to 30 days
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.permanent_session_lifetime = timedelta(days=30)

# Configure MongoDB connection
# Connecting to MongoDB database named 'posts'
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

@app.route('/validate_token', methods=['POST'])
def validate_token():
    try:
        # Extract token from the request
        token = request.json.get('token')

        # Validate the token using Google's token info endpoint
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # If token is valid, return success response
        return jsonify({'message': 'Token validation successful', 'token': token}), 200
    except ValueError:
        # Invalid token
        return jsonify({'error': 'Invalid token'}), 400
    except Exception as e:
        # Handle other exceptions
        return jsonify({'error': str(e)}), 500


@app.route('/google_signin', methods=['POST'])
def google_signin():
    try:
        # Get the Google ID token from the request
        token = request.json.get('idtoken')

        # Validate the token
        if not token:
            return jsonify({'error': 'Token not provided'}), 400

        # Validate the token using Google's token info endpoint
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

                # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        
        # Additional validation steps can be added here
        
        
        # Store the user's identity information in the session
        session['user_id'] = userid
        session['username'] = idinfo['email']  # Assuming you want to use the email as the username
        
        # Redirect the user to the dashboard
        return jsonify({
    'message': 'Sign-in successful',
    'redirect_url': url_for('dashboard')
}), 200


    except ValueError:
        # Invalid token
        return jsonify({'error': 'Invalid token'}), 400
    except Exception as e:
        # Handle other exceptions
        return jsonify({'error': 'An error occurred during sign-in'}), 500


def generate_session_id():
    # Generate a unique session ID (example using UUID)
    return str(uuid.uuid4())

# This is the callback route that Google will redirect to after authentication
@app.route('/auth/google/callback')
def callback():
    try:
        # Get authorization code Google sent back to you
        code = request.args.get("code")

        # Find out what URL to hit for the token
        google_provider_cfg = requests.get('https://accounts.google.com/.well-known/openid-configuration').json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! This will get us our access token and ID token
        token_url = token_endpoint
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": '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',
            "redirect_uri": request.base_url,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        tokens = token_response.json()

        # Verify the token
        idinfo = id_token.verify_oauth2_token(tokens["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        
        # Additional validation steps can be added here

        # Store the user's identity information in the session
        session['user_id'] = userid
        session['username'] = idinfo['email']  # Assuming you want to use the email as the username

        # Redirect the user to the dashboard
        return redirect(url_for("dashboard"))

    except ValueError as ve:
        # Token verification failed
        print(f"Token verification failed: {ve}")
        return "Token verification failed", 401
    except Exception as e:
        # Handle other exceptions
        return jsonify({'error': 'An error occurred during authentication'}), 500

# ///////////////////////////////////

# Function to generate a random token for password reset
def generate_token():
    return secrets.token_urlsafe(16)




# Initialize the scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

# Define the job function
def generate_tokens():
    global global_id_token
    # Get REFRESH_TOKEN from request data
    refresh_token = os.getenv('REFRESH_TOKEN')
    # Make request to generate token
    url = "https://dev.botlhale.xyz/generateAuthToken"
    payload={'REFRESH_TOKEN': refresh_token,}
    files=[]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    if response.status_code == 200:
        # Parse response JSON
        auth_result = response.json().get('AuthenticationResult')
        access_token = auth_result.get('AccessToken')
        id_token = auth_result.get('IdToken')
        
        # Update the global variable
        global_id_token = id_token
        
        print({'access_token': access_token, 'id_token': id_token})
    else:
        print({'error': 'Failed to generate token'})


initialized = False

def initialize():
    global initialized
    # Perform initialization logic here
    generate_tokens()
    # Schedule the job to run every 23 hours
    scheduler.add_job(generate_tokens, 'interval', hours=23)
    print("Server initialization complete")
    initialized = True

@app.before_request
def before_request():
    global initialized
    if not initialized:
        initialize()


@app.route('/')
def home():
    global global_id_token
    if 'username' in session:
        session['id_token'] = global_id_token
        return render_template('dashboard.html', username=session["username"])
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'username' in session:
        session['id_token'] = global_id_token
        return render_template('dashboard.html', username=session["username"])
    return render_template('login.html')

# Define the path where you want to save the recordings
UPLOAD_FOLDER = 'TranscriptForge/recording'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/retrieve-meeting-summaries', methods=['GET'])
def get_summary():
    if 'username' not in session:
        abort(401)  # Unauthorized

    try:
        currently_logged_in_user = session["username"]
    except KeyError as e:
        print(f"Error extracting username from session: {e}")
        return "Error extracting username from session"

    try:
        MONGODB_URI = os.getenv('MONGO_URI')
        myclient = pymongo.MongoClient(MONGODB_URI)

        mydb = myclient["TranscriptForge"]
        mycol = mydb["Meeting_details"]

        summaryList = []

        for x in mycol.find({"UserEmail": currently_logged_in_user}):
            summary = x['Summary']
            meeting_name = x['Meeting_Name']
            date = x['Date']
            recording_url = x['RecordingURL']

            # Extract the recording name from the URL
            recording_name = os.path.basename(recording_url)

            print("Recording Name:", recording_name)

            summaryList.append({
                "summary": summary,
                "Meeting_Name": meeting_name,
                "Date": date,
                "recording_name": recording_name
            })

        print(summaryList)
        return render_template('summary.html', summaryList=summaryList)

    except Exception as e:
        print(f"Error accessing MongoDB: {e}")
        return "Error accessing MongoDB"

# @app.route('/getdata', methods=['GET'])
# def get_data():
#     if 'username' not in session:
#         abort(401)  # Unauthorized
        
#     currently_logged_in_user = session["username"]
    
#     try:
#         MONGODB_URI= os.getenv('MONGO_URI')
#         myclient = pymongo.MongoClient(MONGODB_URI)

#         mydb = myclient["TranscriptForge"]
#         # print(myclient.list_database_names())
                
#         mycol = mydb["Meeting_details"]
        
#         transcriptList = []

#         for x in mycol.find({"UserEmail": currently_logged_in_user}):
#             # Replace these variables with your actual values
#             org_id = x['OrgId']
#             presigned_url_data = x['Filename']
#             bearer_token = session.get('id_token')
#             headers = {'Authorization': f'Bearer {bearer_token}'}
            
#             # Get status using the ASR Async get status GET endpoint
#             status_url = "https://dev.botlhale.xyz/asr/async/status"
#             status_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
#             status_response = requests.get(status_url, params=status_params, headers=headers)
#             if status_response.status_code != 200:
#                 return f"Error getting status: {status_response.status_code}"
            
#             status_data = status_response.json()
#             print('status_data', status_data)
            
#             # Get data using the ASR Async get data GET endpoint
#             data_url = "https://dev.botlhale.xyz/asr/async/data"
#             data_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
#             data_response = requests.get(data_url, params=data_params, headers=headers)
#             if data_response.status_code != 200:
#                 return f"Error getting data: {data_response.status_code}"
#             print('-------------------------------------')
#             data = data_response.json()
#             print('filename', data)
            
#             summary = x['Summary']
            

#             print("Recognition Time:", formatted_time)
            
#             # Extracting only "speaker" and "transcription" keys from each dictionary
#             new_list = [{"speaker": item["speaker"], "transcription": item["transcription"]} for item in data["timestamps"]]
#             transcriptList.append(new_list)
            

#     except KeyError as e:
#         print(f"Error extracting answer: {e}")
#         return "Error extracting answer"
    
#     # return render_template('transcript copy.html', transcriptList=transcriptList)
#     return transcriptList


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            # Insert new user into the database
            users.insert_one({'username': request.form['username'], 'password': request.form['password']})
            session['username'] = request.form['username']  # Log the user in
            return redirect(url_for('home'))
        confirm = 'That username already exists!'
        return render_template('register.html', confirm=confirm)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})

        if login_user:
            if request.form['password'] == login_user['password']:
                session['username'] = request.form['username']  # Log the user in
                if request.form.get('remember'):
                    session.permanent = True  # Mark the session as permanent
                return redirect(url_for('dashboard'))

        return render_template('login.html', confirm='Invalid username/password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear user session and remove cookie
    session.pop('username', None)
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('username', '', expires=0)
    return resp

@app.route('/about')
def about():
    # Check if user is logged in, else abort
    if 'username' not in session:
        abort(401)  # Unauthorized
    return render_template('upload.html')


# Route for resetting password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = mongo.db.users.find_one({'username': username})
        if user:
            reset_token = generate_token()  # Generate reset token
            reset_link = f"http://localhost:5000/set_new_password/{reset_token}"
            # Store the reset token in the database
            mongo.db.reset_tokens.insert_one({'username': username, 'token': reset_token})
            # Access Email Subject and Sender
            EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT')
            EMAIL_SENDER = os.getenv('EMAIL_SENDER')

            # Send reset password email with reset_token
            msg = Message(EMAIL_SUBJECT, sender=EMAIL_SENDER, recipients=[username])
            msg.html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reset Password</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 20px auto;
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}
                    h4 {{
                        color: #333;
                    }}
                    a {{
                        color: #007bff;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h4>Click on this link to reset your password:</h4>
                    <p><a href="{reset_link}">{reset_link}</a></p>
                </div>
            </body>
            </html>
            """
            mail.send(msg)  # Send email
            confirm = "Password reset link has been sent to your email."
            return render_template('reset_password.html', confirm=confirm)
        else:
            confirm = "User not found."
            return render_template('reset_password.html', confirm=confirm)

    return render_template('reset_password.html')


# Route for setting new password after clicking the reset link
@app.route('/set_new_password/<token>', methods=['GET', 'POST'])
def set_new_password(token):
    reset_token_entry = mongo.db.reset_tokens.find_one({'token': token})
    if reset_token_entry:
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            # Update password in the database
            mongo.db.users.update_one({'username': reset_token_entry['username']}, {'$set': {'password': new_password}})
            # Delete the reset token entry from the database
            mongo.db.reset_tokens.delete_one({'token': token})
            confirm = "Password has been reset successfully."
            return render_template('login.html', confirm=confirm)
        return render_template('set_new_password.html')
    else:
        confirm = "Invalid or expired token."
        return render_template('login.html', confirm=confirm)

# Endpoint to generate Bearer token
# @app.route('/generate_token_auth', methods=['GET'])
# def generate_token_auth():
#     global global_id_token
#     # Get REFRESH_TOKEN from request data
#     refresh_token = 'eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.LbCWWrJ_5wfE7U9BKgQx8sX0ldFk9k8DW7q-Ui_6yaQicPg77v6sC56_zUrRUkYMUkncOXEQ2QPqJs60X4T7hNCc8qbCiBcsMp_n7UROYU0bIzzhY1LRJkR4BzeiiluJBDHWOX42sbSXJcPoakMLSCVlXki6Hp9X29DbcfsMGMpOKfDVCp4gaGq-C47Cuv2_nLxMEHAnYB17M0xxWdp4586xtDBqZV4dgEBO-qC6iktvfwgQojs9BVV3IxF8JKRcf-n0hAM9bpc-RFUJoKfdysGpIKzxv_kZmPfeHpDkUJ51dtmgVOLWgf5FXRFfbPtgLm2LnkZPiChDSSUahIgYuA.nUYHj8xquOV8Fsr8.RlUXt72jB5ubf2sC2iF75-fUywfqnCUfXG8YQ_Qtz9ZUavQmG5x0X6_Hexm2-iUA8HvkBCXx9W5hI3hD2eDbxYjeRfw1cONXmqZg74y78gF4XTalnWkYuJ3n7QTZE9QRgj8Ik9rHnSUPeiWZ9cEgQat2I7TfWhO2Nv8yh4qpClZcpdTnvtzORXYz-BE0dxwboJJd1MJzwb85EhnJbTatitmxQFgz0aZ8uE2Poje9aJe0qUHHUlqH-FvJBb3t_3y2aOIBBAa9UqAbGyXIpz-XnHH_jcgBy2hBgqHW17P7fPWnzcwdxl_AZv0yM5fhKm5oCYkirjv4Tp-l1Xi0u5gyKrMnsmeGIG5bstMLAri25Vpx9sebOzAHU1nKcPmXgt662rvzV3e-oZbOvKtleNVlrVZxvSW38syJLhYm3wqaGZSWaWVoKWifJgrAWggn5wC3B-1LOV4Sdazx5NkBqH7YUrDrpHFFLLsVvp3gNuk8U_dgwU6mHd5ajymj3_d5ySfSq9pi8VCxtv0er_TuyYGliG60TnYN6fFKQjmLgHlyN_pdnJTupl9jlk-5hIvzKQicoWdJEmlsgcAFSS16ThpUod5-iqtDsJDrXOG3727b_sPpa4Klcu_qqow8aHoIlgzxrVLQHvpLEZkqIOGt_EmWmMHUEH3GVT-Jdy_K-NNhybT448EUimOSZiHgeI6eEFXT24Kr06I1s5ufdItVT9kuCp-Yy7_ZuoJhgsmCWXJRrzIVc2HXdZTbD8yNE2sTupUC-IvUVg4sn55SU3FxYDhc4u6REMhKTWPJSbKuq0Z4_wrPpHW5v76ok8gYQ1mZgVNCJKvTKaVOYy5hfqVyy-cMXkg6wBd_tWc-XDs_TOAy41-zhA-6D6o7lpXN5ieUz2jBHIeV7L9z2YcjNARimjanS5U_6MDvtg3IGxMoJIXL1FVUTgm5yYrgzlNcSLulE5QuyK22vglE3jtJia04Ilo6-afpMM0jUwnGAnlTS9T6bRmdECVWD-7KMNh2MkGUsYp2VjGFM-ey1NdI1xnnnKpAW_3KFTvQbtAi1PAIY7_F-FFKA7jXLJ0xMFU1Xy4y_MXJXeV1hXc92gICTV9Q5bsOWA0zhvsF8OclYJl5HWgmlyOvl1bRpyKtFwGplKiEBe0iOmAzjrMZjisJ2ciXUD2l1TFcZqtU5_eS7OEKtcSDbXtWMjS7vobqmoCC1fTc7-ZyASiIKzPYgoPxZGclFoJeNpmYcFs2IgTrFu0-6Nj6BOEvskAX98i22H08ZgQA0nq4RT8ESVjJdgDJCz-ltOaaIGffTOctZp62oAtgXmnDSH1Oi-tglzKTLyWfEQ.3VEu75MdMKfzfaJzKx0QJg'
#     # Make request to generate token
#     url = "https://dev.botlhale.xyz/generateAuthToken"
#     payload={'REFRESH_TOKEN': refresh_token,}
#     files=[]
#     headers = {}
#     response = requests.request("POST", url, headers=headers, data=payload, files=files)

#     if response.status_code == 200:
#         # Parse response JSON
#         auth_result = response.json().get('AuthenticationResult')
#         access_token = auth_result.get('AccessToken')
#         id_token = auth_result.get('IdToken')
        
#         # Store ID token in session
#         # Update the global variable
#         global_id_token = id_token
        
#         return jsonify({'access_token': access_token, 'id_token': id_token}), 200
#     else:
#         return jsonify({'error': 'Failed to generate token'}), response.status_code


@app.route('/get-meeting-transcript', methods=['POST'])
def get_dataa():
    if 'username' not in session:
        abort(401)  # Unauthorized
        
    currently_logged_in_user = session["username"]
    
    try:
        # Get meeting name from the form data
        meeting_name = request.form['meeting_name']
        
        MONGODB_URI = os.getenv('MONGO_URI')
        myclient = pymongo.MongoClient(MONGODB_URI)

        mydb = myclient["TranscriptForge"]
        mycol = mydb["Meeting_details"]
        
        transcriptList = []

        for x in mycol.find({"UserEmail": currently_logged_in_user, "Meeting_Name": meeting_name}):
            date = x['Date']
            # Replace these variables with your actual values
            org_id = x['OrgId']
            presigned_url_data = x['Filename']
            bearer_token = session.get('id_token')
            headers = {'Authorization': f'Bearer {bearer_token}'}
            
            # Get status using the ASR Async get status GET endpoint
            status_url = os.getenv('STATUS_URL')
            status_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
            status_response = requests.get(status_url, params=status_params, headers=headers)
            if status_response.status_code != 200:
                return f"Error getting status: {status_response.status_code}"
            
            status_data = status_response.json()
            print('status_data', status_data)
            
            # Get data using the ASR Async get data GET endpoint
            data_url = os.getenv('DATA_URL')
            data_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
            data_response = requests.get(data_url, params=data_params, headers=headers)
            if data_response.status_code != 200:
                return f"Error getting data: {data_response.status_code}"
            print('-------------------------------------')
            data = data_response.json()
            print('filename', data)
            
            # Function to convert milliseconds to seconds and format as HH:MM:SS
            def milliseconds_to_hhmmss(milliseconds):
                seconds = milliseconds / 1000
                return str(datetime.timedelta(seconds=seconds)).split('.')[0]  # Splitting to remove milliseconds

            # Extracting only "speaker" and "transcription" keys from each dictionary
            new_list = [{"speaker": item["speaker"], "transcription": item["transcription"], "start_time": milliseconds_to_hhmmss(item['start'])} for item in data["timestamps"]]
            
            # Append meeting name along with the transcript data
            transcriptList.append({"meeting_name": meeting_name, "transcript": new_list})

    except KeyError as e:
        print(f"Error extracting answer: {e}")
        return "Error extracting answer"
    
    # return the transcript list as JSON data
    # return jsonify(transcriptList)
    return render_template('meetingTranscript.html', transcriptList=transcriptList, date=date)

@app.errorhandler(401)
def unauthorized(error):
    # Redirect unauthorized users to login page
    return redirect(url_for('login'))

# Define a custom error handler for 404 errors (Page Not Found)
@app.errorhandler(404)
def page_not_found(error):
    # Redirect users to a custom error page or any other route you prefer
    return redirect(url_for('error_404'))

# Define a route for the custom error page
@app.route('/error404')
def error_404():
    return render_template('404.html')

# Define a custom error handler for all errors
@app.errorhandler(Exception)
def handle_error(error):
    # Redirect users to a custom error page or any other route you prefer
    return redirect(url_for('error_page'))

# Define a route for the custom error page
@app.route('/error')
def error_page():
    return render_template('error_page.html')

if __name__ == '__main__':
    app.run(debug=True)
