from flask import request
import requests
import pymongo
from flask import Blueprint
import asyncio


uploadAudioRoute = Blueprint('transcript', __name__)


@uploadAudioRoute.route('/upload', methods=['POST'])
def upload():
    loggedInUserEmailAddress = 'monamodi68@gmail.com'

    org_id = 'BotlhaleAI999'
    language_code = 'en-wZA'
    sample_rate = '16000'
    diarization = True
    
    # Get the uploaded file
    file = request.files['audio']
    
    if file.filename == '':
        return "No selected file"
    
    print('file.filename', file.filename)
    # Save the file
    file_path = f'TranscriptForge/recording/{file.filename}'
    file.save(file_path)
    
    # API endpoints and credentials
    upload_url = "https://dev.botlhale.xyz/asr/async/upload"
    api_url = 'https://dev.botlhale.xyz/llm'
    bearer_token = 'eyJraWQiOiJuOU5kRWNSNjVqRWZFWmttY1VkSWlDUHc4bUJBNlZEVlNWdW9ORlFQZmpZPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJmNDA4YTRlOC1lMGMxLTcwMTctMTg0My0wZjVjZWUxZjc5MTgiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX1N5ZHpTM2JoMyIsImNvZ25pdG86dXNlcm5hbWUiOiJmNDA4YTRlOC1lMGMxLTcwMTctMTg0My0wZjVjZWUxZjc5MTgiLCJvcmlnaW5fanRpIjoiOTNjYTgxZmYtY2Y4Ny00NTZlLTg5ZjQtODA3Njg1MzE0OGM0IiwiYXVkIjoiNHJ0bXNnam9vOGQ3MmpuZG1nMnZqdTliY2YiLCJldmVudF9pZCI6IjJjMTA4ZjhlLWFmYWItNGQzZS04NWUxLTk3Nzc5ZDg5ZmNkOSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNjkxNjU0ODM4LCJuYW1lIjoiWG9saXNhbmkgTmt3ZW50c2hhIiwiZXhwIjoxNzA2NzI3NTM3LCJpYXQiOjE3MDY2NDExMzgsImp0aSI6IjNkMTRiOTE4LWE1YzctNDZjNy05YmRkLTRkNTUwNzNlYzAxYiIsImVtYWlsIjoieG9saXNhbmlAYm90bGhhbGUuYWkifQ.dLSiZmwT0U5up85NMlNVuROH8kg_p1wKJVNap_vdZZ3MvC5p2tcbPqr-3nACMgD0Tl15uaugVekYB1oXfKAbYI42ARWqlcrof3a8iicdhMoGvjtNeDPQn8AWl75fxOMKZJpgJfpa8Vt0d5bWEG1CZ7WeDqr-PnOUGZQwvILxgtB9HVkjryHjpwPhzsFVeuL_7f_zDSsh8GY-40OGgVQEIpV0kfrK8sKBjMDhCpNqmkpu8uV7uHol4XWoS8F3lkeJ6sbHy7BBAwfez6ToU20mIWUybfEw9MatwhiCIboFG0fXseLgEEmEQdbfyQcVN6WwBKJcUAGmjr9vDNFf5Ply5A'
    
    headers = {'Authorization': f'Bearer {bearer_token}'}
    payload = {'OrgID': org_id, 'LanguageCode': language_code, 'SampleRate': sample_rate, 'Diarization': diarization}
    
    # Perform the initial request to get the presigned URL
    response = requests.post(upload_url, headers=headers, data=payload)
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    
    presigned_url_data = response.json()
    print('presigned_url_data', presigned_url_data)
    # Use the presigned URL for file upload
    with open(file_path, 'rb') as f:
        files = {'file': (presigned_url_data['fields']['key'], f)}
        upload_response = requests.post(presigned_url_data['url'], data=presigned_url_data['fields'], files=files)
    
    if upload_response.status_code != 204:
        return f"Error uploading file: {upload_response.status_code}"
    
    async def main():
        print("Hello")
        await asyncio.sleep(10)
            # Get status using the ASR Async get status GET endpoint
        status_url = "https://dev.botlhale.xyz/asr/async/status"
        status_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
        status_response = requests.get(status_url, params=status_params, headers=headers)
        if status_response.status_code != 200:
            return f"Error getting status: {status_response.status_code}"
        
        status_data = status_response.json()
        print('status_data', status_data['status'])

    asyncio.run(main())
 
    # Get data using the ASR Async get data GET endpoint
    data_url = "https://dev.botlhale.xyz/asr/async/data"
    data_params = {'OrgID': org_id, 'FileName': presigned_url_data['fields']['key']}
    data_response = requests.get(data_url, params=data_params, headers=headers)
    if data_response.status_code != 200:
        return f"Error getting data: {data_response.status_code}"
    print('-------------------------------------')
    data = data_response.json()
    print('filename', data)
    
    
    # Extracting only "speaker" and "transcription" keys from each dictionary
    new_list = [{"speaker": item["speaker"], "transcription": item["transcription"]} for item in data["timestamps"]]
    
    formatted_string = "\n".join([f"Speaker: {item['speaker']}, Transcription: {item['transcription']}" for item in new_list])
    print(formatted_string)
    
    prompt_specific = f'please summarize this meeting {formatted_string}'
    
    params = {'prompt': prompt_specific, 'n': 1, 'max_tokens': 200, 'temperature': 1.0, 'top_p': 1.0, 'top_k': 10}
    
    response = requests.post(api_url, data=params, headers=headers)
    
    if response.status_code == 200:
        try:
            MONGODB_URI="mongodb+srv://monamodi68:FVTjynigAKmcKhsH@cluster0.kydsxea.mongodb.net/posts?retryWrites=true&w=majority"
            myclient = pymongo.MongoClient(MONGODB_URI)

            mydb = myclient["TranscriptForge"]
            print(myclient.list_database_names())
                
            mycol = mydb["Meeting_details"]

            mydict = {"UserEmail": loggedInUserEmailAddress, "OrgId":org_id, "Filename": presigned_url_data, "Summary": response.text }

            x = mycol.insert_one(mydict)
            return response.text
        except KeyError as e:
            print(f"Error extracting answer: {e}")
            return "Error extracting answer"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return f"Error: {response.status_code} - {response.text}"

    