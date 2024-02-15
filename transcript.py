from flask import Blueprint, session, request, jsonify
import json
import requests
import pymongo
import asyncio
from werkzeug.utils import secure_filename
from google.cloud import storage
import traceback

uploadAudioRoute = Blueprint('transcript', __name__)

# Replace with your bucket name
BUCKET_NAME = "botlhale-meeting-audio"

# Replace with your credentials path
CREDENTIALS_PATH = "keyfile.json"


@uploadAudioRoute.route('/upload', methods=['POST'])
def upload():
    try:
        # Access the username from the session
        loggedInUserEmailAddress = session.get('username')
        print('loggedInUserEmailAddress', loggedInUserEmailAddress)
        bearer_token = session.get('id_token')
        print('bearer_token', bearer_token)

        org_id = 'BotlhaleAI999'
        language_code = 'en-wZA'
        sample_rate = '16000'
        diarization = True
        
        # Get the uploaded file
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        print('file.filename', file.filename)
        print('Metting Name:', request.form['name'])
        date = request.form.get('date')
        print('Date:', date)
        
        # Save the file to TranscriptForge/recording directory
        file_path = f'TranscriptForge/recording/{file.filename}'
        file.save(file_path)
        
        # Upload to Google Cloud Storage
        filename = secure_filename(file.filename)
        client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_filename(file_path)

        # Get the public URL
        public_url = blob.public_url
        
        # API endpoints and credentials
        upload_url = "https://dev.botlhale.xyz/asr/async/upload"
        api_url = 'https://dev.botlhale.xyz/llm'
        
        headers = {'Authorization': f'Bearer {bearer_token}'}
        payload = {'OrgID': org_id, 'LanguageCode': language_code, 'SampleRate': sample_rate, 'Diarization': diarization}
        
        # Perform the initial request to get the presigned URL
        response = requests.post(upload_url, headers=headers, data=payload)
        if response.status_code != 200:
            return jsonify({"error": f"Error: {response.status_code} - {response.text}"}), 500
        
        presigned_url_data = response.json()
        print('presigned_url_data', presigned_url_data)
        
        # Use the presigned URL for file upload
        with open(file_path, 'rb') as f:
            files = {'file': (presigned_url_data['fields']['key'], f)}
            upload_response = requests.post(presigned_url_data['url'], data=presigned_url_data['fields'], files=files)
        
        if upload_response.status_code != 204:
            return jsonify({"error": f"Error uploading file: {upload_response.status_code}"}), 500
        
        async def main():
            print("Hello")
            await asyncio.sleep(10)
            # Get status using the ASR Async get status GET endpoint
            status_url = "https://dev.botlhale.xyz/asr/async/status"
            status_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
            status_response = requests.get(status_url, params=status_params, headers=headers)
            if status_response.status_code != 200:
                return jsonify({"error": f"Error getting status: {status_response.status_code}"}), 500
            
            status_data = status_response.json()
            print('status_data', status_data['status'])
        
        asyncio.run(main())
     
        # Get data using the ASR Async get data GET endpoint
        data_url = "https://dev.botlhale.xyz/asr/async/data"
        data_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
        data_response = requests.get(data_url, params=data_params, headers=headers)
        if data_response.status_code != 200:
            return jsonify({"error": f"Error getting data: {data_response.status_code}"}), 500
        
        data = data_response.json()
        print('filename', data)
        
        # Extracting only "speaker" and "transcription" keys from each dictionary
        new_list = [{"speaker": item["speaker"], "transcription": item["transcription"]} for item in data["timestamps"]]
        
        formatted_string = "\n".join([f"Speaker: {item['speaker']}, Transcription: {item['transcription']}" for item in new_list])
        print(formatted_string)
        
        prompt_specific = f'please summarize this meeting {formatted_string}'
        
        params = {'prompt': prompt_specific, 'n': 1, 'max_tokens': 1200, 'temperature': 1.0, 'top_p': 1.0, 'top_k': 10}
        
        response = requests.post(api_url, data=params, headers=headers)
        print(response.__dict__['_content'])
        response_data = json.loads(response.__dict__['_content'])

        # Extract DateReceived and Output
        date_received = response_data.get('DateReceived')
        print(date_received)
        output = response_data.get('Output')
        print(output)
        
        if response.status_code == 200:
            try:
                MONGODB_URI="mongodb+srv://monamodi68:FVTjynigAKmcKhsH@cluster0.kydsxea.mongodb.net/posts?retryWrites=true&w=majority"
                myclient = pymongo.MongoClient(MONGODB_URI)

                mydb = myclient["TranscriptForge"]
                print(myclient.list_database_names())
                    
                mycol = mydb["Meeting_details"]

                mydict = { "Meeting_Name": request.form['name'], "UserEmail": loggedInUserEmailAddress, "OrgId":org_id, "Filename": presigned_url_data, "Summary": response_data.get('Output'),"Date" : date, "RecordingURL": public_url}

                x = mycol.insert_one(mydict)
                return jsonify({"message": "Upload and processing successful", "data": response_data}), 200
            except KeyError as e:
                print(f"Error extracting answer: {e}")
                return jsonify({"error": "Error extracting answer"}), 500
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return jsonify({"error": f"Error: {response.status_code} - {response.text}"}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "message": "An error occurred during upload or processing"}), 500
