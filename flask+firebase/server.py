from flask import Flask, request, send_file,render_template
import os
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("./social-lips-firebase-adminsdk-c28zn-d607a10c33.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

# Function to download a video from Firebase Storage
def download_video(file_id, save_directory):
    bucket = firebase_admin.storage.bucket(app=firebase_admin.get_app(), name="social-lips.appspot.com")
    firebase_blob_path = "posts/video/" + file_id
    blob = bucket.blob(firebase_blob_path)
    file_name = os.path.basename(file_id)
    file_path = os.path.join(save_directory, file_name + ".mp4")
    blob.download_to_filename(file_path)
    print("file downloaded")
    return file_path

# Function to create a VTT subtitle file
def create_subtitle_file(video_file_path):
    subtitle_text = "WEBVTT\n\n0:00:00.000 --> 0:00:02.000\nSubtitle line 1\n\n0:00:02.001 --> 0:00:04.000\nSubtitle line 2"
    file_name = os.path.splitext(os.path.basename(video_file_path))[0]
    subtitle_file_path = "subtitle/" + file_name + ".vtt"
    with open(subtitle_file_path, "w", encoding="utf-8") as vtt_file:
        vtt_file.write(subtitle_text)
    print("Subtitle generated")
    return subtitle_file_path

# Function to upload a subtitle file to Firebase Storage
def upload_subtitle_to_firebase(subtitle_file_path, destination_blob_name):
    bucket = firebase_admin.storage.bucket(app=firebase_admin.get_app(), name="social-lips.appspot.com")
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(subtitle_file_path)
    print("Subtitle uploaded")
    return 1;


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<string:file_id>', methods=['GET'])
def download_file(file_id):

    try:
        save_directory = "videos/"
        video_file_path = download_video(file_id, save_directory)
        subtitle_file_path = create_subtitle_file(video_file_path)
        destination_blob_name = f"posts/subtitles/{os.path.basename(video_file_path)}.vtt"
        upload_subtitle_to_firebase(subtitle_file_path, destination_blob_name)
        
        # Clean up: Remove the local VTT and video files
        # os.remove(subtitle_file_path)
        # os.remove(video_file_path)

        return f"Subtitles uploaded to Firebase Storage as {destination_blob_name}"
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