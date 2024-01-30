from flask import Flask, jsonify, render_template, request
import requests
from transcript import uploadAudioRoute
import os
import pymongo

app = Flask(__name__)

# Register the blueprint from abc.py
app.register_blueprint(uploadAudioRoute, url_prefix='/uploadAudioRoute_prefix')

@app.route('/')
def recordingAudio():
    return render_template('index.html')

# ////////////////////////////////////////////////////////

# Define the path where you want to save the recordings
UPLOAD_FOLDER = 'TranscriptForge/recording'
PROCESSED_FOLDER = 'TranscriptForge/processedAudio'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

@app.route('/upload', methods=['POST'])
def upload_audio():
    # Check if the 'audio' key is in the request files
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    print(audio_file)

    # Ensure the 'uploads' directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

    # Save the audio file to the specified path
    # file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
    file_path = 'TranscriptForge/recording/' + audio_file.filename
    audio_file.save(file_path)
    


    return jsonify({'message': 'File uploaded and processed successfully'})

# asr_0O849E41pNrV_en-wZA_16000_BotlhaleAI999_True__S9E5Ey0P070u25012024_143056

@app.route('/getdata', methods=['GET'])
def get_data():
    currently_logged_in_user = 'monamodi68@gmail.com'
    
    try:
        MONGODB_URI="mongodb+srv://monamodi68:FVTjynigAKmcKhsH@cluster0.kydsxea.mongodb.net/posts?retryWrites=true&w=majority"
        myclient = pymongo.MongoClient(MONGODB_URI)

        mydb = myclient["TranscriptForge"]
        # print(myclient.list_database_names())
                
        mycol = mydb["Meeting_details"]
        
        transcriptList = []

        for x in mycol.find({"UserEmail": currently_logged_in_user}):
            # Replace these variables with your actual values
            org_id = x['OrgId']
            presigned_url_data = x['Filename']
            bearer_token = 'eyJraWQiOiJuOU5kRWNSNjVqRWZFWmttY1VkSWlDUHc4bUJBNlZEVlNWdW9ORlFQZmpZPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJmNDA4YTRlOC1lMGMxLTcwMTctMTg0My0wZjVjZWUxZjc5MTgiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX1N5ZHpTM2JoMyIsImNvZ25pdG86dXNlcm5hbWUiOiJmNDA4YTRlOC1lMGMxLTcwMTctMTg0My0wZjVjZWUxZjc5MTgiLCJvcmlnaW5fanRpIjoiOTNjYTgxZmYtY2Y4Ny00NTZlLTg5ZjQtODA3Njg1MzE0OGM0IiwiYXVkIjoiNHJ0bXNnam9vOGQ3MmpuZG1nMnZqdTliY2YiLCJldmVudF9pZCI6IjJjMTA4ZjhlLWFmYWItNGQzZS04NWUxLTk3Nzc5ZDg5ZmNkOSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNjkxNjU0ODM4LCJuYW1lIjoiWG9saXNhbmkgTmt3ZW50c2hhIiwiZXhwIjoxNzA2NzI3NTM3LCJpYXQiOjE3MDY2NDExMzgsImp0aSI6IjNkMTRiOTE4LWE1YzctNDZjNy05YmRkLTRkNTUwNzNlYzAxYiIsImVtYWlsIjoieG9saXNhbmlAYm90bGhhbGUuYWkifQ.dLSiZmwT0U5up85NMlNVuROH8kg_p1wKJVNap_vdZZ3MvC5p2tcbPqr-3nACMgD0Tl15uaugVekYB1oXfKAbYI42ARWqlcrof3a8iicdhMoGvjtNeDPQn8AWl75fxOMKZJpgJfpa8Vt0d5bWEG1CZ7WeDqr-PnOUGZQwvILxgtB9HVkjryHjpwPhzsFVeuL_7f_zDSsh8GY-40OGgVQEIpV0kfrK8sKBjMDhCpNqmkpu8uV7uHol4XWoS8F3lkeJ6sbHy7BBAwfez6ToU20mIWUybfEw9MatwhiCIboFG0fXseLgEEmEQdbfyQcVN6WwBKJcUAGmjr9vDNFf5Ply5A'
            headers = {'Authorization': f'Bearer {bearer_token}'}
            
            # Get status using the ASR Async get status GET endpoint
            status_url = "https://dev.botlhale.xyz/asr/async/status"
            status_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
            status_response = requests.get(status_url, params=status_params, headers=headers)
            if status_response.status_code != 200:
                return f"Error getting status: {status_response.status_code}"
            
            status_data = status_response.json()
            print('status_data', status_data)
            
            # Get data using the ASR Async get data GET endpoint
            data_url = "https://dev.botlhale.xyz/asr/async/data"
            data_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
            data_response = requests.get(data_url, params=data_params, headers=headers)
            if data_response.status_code != 200:
                return f"Error getting data: {data_response.status_code}"
            print('-------------------------------------')
            data = data_response.json()
            print('filename', data)
            
            summary = x['Summary']
            
            # Extracting only "speaker" and "transcription" keys from each dictionary
            new_list = [{"speaker": item["speaker"], "transcription": item["transcription"], "Summary": summary} for item in data["timestamps"]]
            transcriptList.append(new_list)
            

    except KeyError as e:
        print(f"Error extracting answer: {e}")
        return "Error extracting answer"
    

    
    
    
    # return render_template('transcript.html', transcriptList=transcriptList)
    return transcriptList
    
if __name__ == '__main__':
    app.run(debug=True)
