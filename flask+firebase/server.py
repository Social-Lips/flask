from flask import Flask, request, send_file,render_template
import os
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("./social-lips-firebase-adminsdk-c28zn-d607a10c33.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<string:file_id>', methods=['GET'])
def download_file(file_id):
    bucket = firebase_admin.storage.bucket(app=firebase_admin.get_app(), name="social-lips.appspot.com")

    try:
        firebase_blob_path = "posts/video/" + file_id  
        
        # Get a reference to the specified file in Firebase Storage
        blob = bucket.blob(firebase_blob_path)
        
      
        file_name = os.path.basename(file_id)  # Extract  filename from the path
      
  
        save_directory = "videos/"
        file_path = os.path.join(save_directory, file_name+".mp4")
        # return file_path
        # Download the file from Firebase Storage to the specified path
        blob.download_to_filename(file_path)

        subtitle_text = "WEBVTT\n\n0:00:00.000 --> 0:00:02.000\nSubtitle line 1\n\n0:00:02.001 --> 0:00:04.000\nSubtitle line 2"
        subtitle_file_path="subtitle/"+file_name+".vtt"
        with open(subtitle_file_path, "w", encoding="utf-8") as vtt_file:
            vtt_file.write(subtitle_text)



    

    # Upload the VTT subtitle file to the "posts/subtitles" folder in Firebase Storage
        destination_blob_name = f"posts/subtitles/{file_name}.vtt"
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(subtitle_file_path)

        # Clean up: Remove the local VTT file
        os.remove(subtitle_file_path)
        os.remove(file_path)
        # Send a response to indicate the file has been downloaded
        return f"File uploaded  {subtitle_file_path}"
    except Exception as e:
        return str(e), 404
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    try:
        # Replace this with your Firebase Storage bucket name
        bucket = storage.bucket(app=firebase_admin.get_app(), name="social-lips.appspot.com")
        blob = bucket.blob(file.filename)

        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )

        return "File uploaded successfully"
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)