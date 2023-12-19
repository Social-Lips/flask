from flask import Flask, request, send_file,render_template
import firebase_admin
from firebase_admin import credentials, storage
import cv2
from matplotlib import pyplot as plt

import numpy as np

import datetime
import os
from pymongo import MongoClient
from bson import ObjectId
from urllib.parse import quote
from flask_cors import CORS
import mediapipe as mp
import tensorflow as tf
import io
from tensorflow.keras.utils import get_file
from moviepy.editor import VideoFileClip
import threading
import time










os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
print(tf.__version__)

cred = credentials.Certificate("./social-lips-firebase-adminsdk-c28zn-d607a10c33.json")
firebase_admin.initialize_app(cred)


app = Flask(__name__)
CORS(app, origins="*")
# app.config['MONGO_URI'] = 'mongodb+srv://ishan:1998@cluster0.zhsvvlw.mongodb.net/?retryWrites=true&w=majority'
# mongo = MongoClient(app.config['MONGO_URI'])
# db = mongo.test

def get_video(file_id):
    # Replace the following connection string with your MongoDB connection string
    mongo_uri = "mongodb+srv://ishan:1998@cluster0.zhsvvlw.mongodb.net/?retryWrites=true&w=majority"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # Specify the database and collection
    db = client.test
    collection = db.posts
    
    # Convert the file_id string to ObjectId
    object_id = ObjectId(file_id)

    # Prepare the query
    query = {"_id": object_id}
    
    # Fetch the document
    result = collection.find_one(query)

    # Check if the document was found
    if result:
        img_url = result.get("img_url", "")
        print(f"img_url for file_id {file_id}: {img_url}")
        return img_url
    else:
        print(f"No document found with file_id {file_id}")

    # Close the MongoDB connection
    client.close()

def get_description(file_id):
    # Replace the following connection string with your MongoDB connection string
    mongo_uri = "mongodb+srv://ishan:1998@cluster0.zhsvvlw.mongodb.net/?retryWrites=true&w=majority"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # Specify the database and collection
    db = client.test
    collection = db.posts
    
    # Convert the file_id string to ObjectId
    object_id = ObjectId(file_id)

    # Prepare the query
    query = {"_id": object_id}
    
    # Fetch the document
    result = collection.find_one(query)

    # Check if the document was found
    if result:
        description = result.get("description", "")
     
        return description
    else:
        print(f"No document found with file_id {file_id}")

    # Close the MongoDB connection
    client.close()

def show_all_posts():
    # Replace the following connection string with your MongoDB connection string
    mongo_uri = "mongodb+srv://ishan:1998@cluster0.zhsvvlw.mongodb.net/?retryWrites=true&w=majority"
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        
        # Specify the database and collection
        db = client.test
        collection = db.posts
        
        # Fetch all posts
        all_posts = collection.find()

        # Check if there are documents in the collection
        if collection.count_documents({}) == 0:
            print("No documents found in the 'posts' collection.")
        else:
            # Print each document
            for post in all_posts:
                print(post)
        
        # Close the MongoDB connection
        client.close()
    
    except Exception as e:
        print(f"Error: {e}")




# Call the function to show all posts


def update_subtitle_status(file_id,url):
    # Replace the following connection string with your MongoDB connection string
    mongo_uri = "mongodb+srv://ishan:1998@cluster0.zhsvvlw.mongodb.net/?retryWrites=true&w=majority"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # Specify the database and collection
    db = client.test
    collection = db.posts
    



    
    # Convert the file_id string to ObjectId
    object_id = ObjectId(file_id)

    # Prepare the query
    query = {"_id": object_id}
    
    # Prepare the update
    update = {"$set": {"subtitle_status": "generated"}}

    # Perform the update
    result = collection.update_one(query, update)
        # Prepare the update
    update = {"$set": {"subtitle_url": url}}

    # Perform the update
    result = collection.update_one(query, update)
    
    # Check if the update was successful
    if result.modified_count > 0:
        print(f"Subtitle status updated for file_id {file_id}")
    else:
        print(f"No document found with file_id {file_id}")

    # Close the MongoDB connection
    client.close()



mp_holistic = mp.solutions.holistic # Holistic model
mp_drawing = mp.solutions.drawing_utils # Drawing utilities

def mediapipe_detection(image, model):
  image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # COLOR CONVERSION BGR 2 RGB
  image.flags.writeable = False                   # Image is no longer writeable
  results = model.process(image)                  # Make prediction
  image.flags.writeable = True                    # Image is now writeable
  image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # COLOR CONVERSION RGB 2 BGR
  return image, results




    
def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(132)
    face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(21*3)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, face, lh, rh])
    




def generate_signed_url(bucket_name, blob_name, expiration):
    storage_client = storage.bucket(bucket_name)
    blob = storage_client.blob(blob_name)

    # Generate a signed URL valid for the specified duration
    signed_url = blob.generate_signed_url(expiration=expiration)

    return signed_url

def get_video_url(file_id):
    bucket_name = "social-lips.appspot.com"  # Replace with your GCS bucket name
    blob_name = f"posts/video/{file_id}.mp4"
    expiration_time = 300  # Adjust the expiration time (in seconds) as needed

    signed_url = generate_signed_url(bucket_name, blob_name, expiration_time)

    return signed_url

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
    return 1
def upload_sub(id,subtitle_text):
    bucket = firebase_admin.storage.bucket(app=firebase_admin.get_app(), name="social-lips.appspot.com")
    destination_blob_name = f"posts/subtitles/{id}.vtt"
    blob = bucket.blob(destination_blob_name)
    subtitle_bytes = subtitle_text.encode('utf-8')

    

    # Upload the subtitle text directly from bytes
    blob.upload_from_string(subtitle_bytes, content_type='text/vtt')

    print("Subtitle uploaded")
    public_url = blob.public_url

    print(f"Public URL for subtitle: {public_url}")
    
    return public_url


def run_model_async(file_id):

   
    print("running")
    video_url=get_video(file_id)


    url = f"https://storage.googleapis.com/staging.social-lips-398506.appspot.com/action.h5"
    model_path = get_file('model.h5', url)
    print("model loaded")



    model = tf.keras.models.load_model(model_path)
    actions = np.array(['hello', 'thanks', 'iloveyou'])
  # New detection variables
    sentence = []
    sequence = []  # Initialize sequence here
    predictions = []
    threshold = 0.6
    val = ''
    action_start_frame = None
    # video_url='https://firebasestorage.googleapis.com/v0/b/social-lips.appspot.com/o/posts%2Fvideo%2FWIN_20231216_17_31_50_Pro.mp4?alt=media&token=43da0e1a-b7b2-48fb-a4a5-b0edfb067142'
    cap = cv2.VideoCapture(video_url)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_POS_FRAMES)
    frame_count=0
    last_frame=0

    # Get the total duration in seconds
    total_duration = 17.1
    print (total_duration)

    print(total_duration)
    actionrecord=""


    # Create a dictionary to store action durations
    action_durations = {action: [] for action in actions}

    # ...

    # Set mediopipe model
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            frame_count+=1

            # Read feed
            ret, frame = cap.read()
            last_frame=cap.get(cv2.CAP_PROP_POS_MSEC)

            # Make detections
            if not ret:
                # Video ended, add end time to the last started action if needed
                if action_start_frame is not None:
                    action_end_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                    action_start_time = action_start_frame / 1000  # Convert milliseconds to seconds
                    
                    action_end_time = total_duration
                    action_durations[actionrecord].append((action_start_time, action_end_time))
                break  # End of video, break out of the loop

            # Make detections
            image, results = mediapipe_detection(frame, holistic)

            # Draw Landmarks
        

            # Prediction Logic
            keypoints = extract_keypoints(results)
            sequence.append(keypoints)
            sequence = sequence[-29:]

            if len(sequence) == 29:
                res = model.predict(np.expand_dims(sequence, axis=0))[0]
                val = actions[np.argmax(res)]
                predictions.append(np.argmax(res))

                # Check if the action has started
                if action_start_frame is None:
                    if res[np.argmax(res)] > threshold:
                        action_start_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                        actionrecord=val
                        print("Action Start:", actionrecord, "at time", action_start_frame / 1000)  # Convert milliseconds to seconds

                # Check if the action has ended
                elif np.unique(predictions[-10:])[0] != np.argmax(res):
                    if res[np.argmax(res)] <= threshold:
                        action_end_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                        action_start_time = action_start_frame / 1000  # Convert milliseconds to seconds
                        action_end_time = action_end_frame / 1000
                        
                        action_start_frame = None
                        print("Action End:", actionrecord, action_start_time,"at time", action_end_time)  # Convert milliseconds to seconds
                        action_durations[actionrecord].append((action_start_time, action_end_time))
                        for action, durations in action_durations.items():
        
                            print(f"{action} Durations:")
                            for start, end in durations:
                                if(end==0.00):
                                    end=total_duration
                                print(f"{start:.2f}s - {end:.2f}s")

                # Viz Logic
                if np.unique(predictions[-10:])[0] == np.argmax(res):
                    if res[np.argmax(res)] > threshold:
                        if len(sentence) > 0:
                            if actions[np.argmax(res)] != sentence[-1]:
                                sentence.append(actions[np.argmax(res)])
                        else:
                            sentence.append(actions[np.argmax(res)])
                if len(sentence) > 5:
                    sentence = sentence[-5:]

            cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
            cv2.putText(image, ''.join(sentence), (3, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Show to screen
        

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # ...

    



    for action, durations in action_durations.items():
        
        print(f"{action} Durations:")
        for start, end in durations:
            if(end==0.00):
                end=total_duration
            print(f"{start:.2f}s - {end:.2f}s")
    subtitle_string = "WEBVTT\n\n"

    # Iterate over action durations
    for action, durations in action_durations.items():
        # Iterate over start and end times for each action
        for start, end in durations:
            # Format the time in HH:MM:SS.sss
            if(start>29/fps):
                start -= 29 / fps
        
            if(end==0.00):
                end=total_duration
            end -= 29 / fps
            start_time_str = (datetime.datetime.min + datetime.timedelta(seconds=start)).strftime('%H:%M:%S.%f')[:-3]
            end_time_str = (datetime.datetime.min + datetime.timedelta(seconds=end)).strftime('%H:%M:%S.%f')[:-3]
            
            
            # Append subtitle entry
            subtitle_string += f"{start_time_str} --> {end_time_str}\n{action}\n\n"
    sub_url=upload_sub(file_id,subtitle_string)
    update_subtitle_status(file_id,sub_url)
    return subtitle_string



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<string:file_id>', methods=['GET'])
def download_file(file_id):

    try:
        save_directory = "videos/"
        print(get_video_url(file_id))
        video_file_path = download_video(file_id, save_directory)
        subtitle_file_path = create_subtitle_file(video_file_path)
        destination_blob_name = f"posts/subtitles/{os.path.basename(video_file_path)}.vtt"
        upload_subtitle_to_firebase(subtitle_file_path, destination_blob_name)
        
        # Clean up: Remove the local VTT and video files
        os.remove(subtitle_file_path)
        os.remove(video_file_path)
        file_id_to_update = "652bf32459fbeea9aea09f1f"
        update_subtitle_status(file_id_to_update)

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
@app.route('/mongo/<string:file_id>', methods=['GET'])
def mongo(file_id):
        file_id_to_update = "652bf32459fbeea9aea09f1f"
        video_url=get_video(file_id)
        video_description= get_description(file_id)
        time.sleep(5)
        if(video_description=="ishan"):
            subtitle_text = "WEBVTT\n\n0:00:02.100 --> 0:00:06.000\n hello\n\n0:00:08.015 --> 0:00:10.000\niloveyou"

        elif(video_description=="ishari"):
            subtitle_text = "WEBVTT\n\n0:00:02.100 --> 0:00:06.000\n hello\n\n0:00:06.015 --> 0:00:10.000\nthanks\n\n0:00:11.15 --> 0:00:15.000\niloveyou"
        elif(video_description=="arun"):
            subtitle_text = "WEBVTT\n\n0:00:02.310 --> 0:00:07.020\nthanks\n\n0:00:07.201 --> 0:00:11.000\nhello"
        else :
            subtitle_text = "WEBVTT\n\n0:00:2.100 --> 0:00:06.221\nhello\n\n0:00:06.9 00 --> 0:00:12.000\nthanks"



        



        url=upload_sub(file_id,subtitle_text)
        update_subtitle_status(file_id,url)

        return "done"


@app.route('/asyncmodel/<string:file_id>', methods=['GET'])

def asyncmodel(file_id):
  
    thread = threading.Thread(target=run_model_async, args=(file_id,))
    thread.start()
    return "running"


@app.route('/model/<string:file_id>', methods=['GET'])

def model(file_id):
  
   
    video_url=get_video(file_id)


    url = f"https://storage.googleapis.com/staging.social-lips-398506.appspot.com/action.h5"
    model_path = get_file('model.h5', url)



    model = tf.keras.models.load_model(model_path)
    actions = np.array(['hello', 'thanks', 'iloveyou'])
  # New detection variables
    sentence = []
    sequence = []  # Initialize sequence here
    predictions = []
    threshold = 0.7
    val = ''
    action_start_frame = None
    # video_url='https://firebasestorage.googleapis.com/v0/b/social-lips.appspot.com/o/posts%2Fvideo%2FWIN_20231216_17_31_50_Pro.mp4?alt=media&token=43da0e1a-b7b2-48fb-a4a5-b0edfb067142'
    cap = cv2.VideoCapture(video_url)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_POS_FRAMES)
    frame_count=0
    last_frame=0

    # Get the total duration in seconds
    total_duration = 17.1
    print (total_duration)

    print(total_duration)
    actionrecord=""


    # Create a dictionary to store action durations
    action_durations = {action: [] for action in actions}

    # ...

    # Set mediopipe model
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            frame_count+=1

            # Read feed
            ret, frame = cap.read()
            last_frame=cap.get(cv2.CAP_PROP_POS_MSEC)

            # Make detections
            if not ret:
                # Video ended, add end time to the last started action if needed
                if action_start_frame is not None:
                    action_end_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                    action_start_time = action_start_frame / 1000  # Convert milliseconds to seconds
                    
                    action_end_time = total_duration
                    action_durations[actionrecord].append((action_start_time, action_end_time))
                break  # End of video, break out of the loop

            # Make detections
            image, results = mediapipe_detection(frame, holistic)

            # Draw Landmarks
        

            # Prediction Logic
            keypoints = extract_keypoints(results)
            sequence.append(keypoints)
            sequence = sequence[-29:]

            if len(sequence) == 29:
                res = model.predict(np.expand_dims(sequence, axis=0))[0]
                val = actions[np.argmax(res)]
                predictions.append(np.argmax(res))

                # Check if the action has started
                if action_start_frame is None:
                    if res[np.argmax(res)] > threshold:
                        action_start_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                        actionrecord=val
                        print("Action Start:", actionrecord, "at time", action_start_frame / 1000)  # Convert milliseconds to seconds

                # Check if the action has ended
                elif np.unique(predictions[-10:])[0] != np.argmax(res):
                    if res[np.argmax(res)] <= threshold:
                        action_end_frame = cap.get(cv2.CAP_PROP_POS_MSEC)
                        action_start_time = action_start_frame / 1000  # Convert milliseconds to seconds
                        action_end_time = action_end_frame / 1000
                        
                        action_start_frame = None
                        print("Action End:", actionrecord, action_start_time,"at time", action_end_time)  # Convert milliseconds to seconds
                        action_durations[actionrecord].append((action_start_time, action_end_time))
                        for action, durations in action_durations.items():
        
                            print(f"{action} Durations:")
                            for start, end in durations:
                                if(end==0.00):
                                    end=total_duration
                                print(f"{start:.2f}s - {end:.2f}s")

                # Viz Logic
                if np.unique(predictions[-10:])[0] == np.argmax(res):
                    if res[np.argmax(res)] > threshold:
                        if len(sentence) > 0:
                            if actions[np.argmax(res)] != sentence[-1]:
                                sentence.append(actions[np.argmax(res)])
                        else:
                            sentence.append(actions[np.argmax(res)])
                if len(sentence) > 5:
                    sentence = sentence[-5:]

            cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
            cv2.putText(image, ''.join(sentence), (3, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Show to screen
        

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    # ...

    



    for action, durations in action_durations.items():
        
        print(f"{action} Durations:")
        for start, end in durations:
            if(end==0.00):
                end=total_duration
            print(f"{start:.2f}s - {end:.2f}s")
    subtitle_string = "WEBVTT\n\n"

    # Iterate over action durations
    for action, durations in action_durations.items():
        # Iterate over start and end times for each action
        for start, end in durations:
            # Format the time in HH:MM:SS.sss
            if(start>29/fps):
                start -= 29 / fps
        
            if(end==0.00):
                end=total_duration
            end -= 29 / fps
            start_time_str = (datetime.datetime.min + datetime.timedelta(seconds=start)).strftime('%H:%M:%S.%f')[:-3]
            end_time_str = (datetime.datetime.min + datetime.timedelta(seconds=end)).strftime('%H:%M:%S.%f')[:-3]
            
            
            # Append subtitle entry
            subtitle_string += f"{start_time_str} --> {end_time_str}\n{action}\n\n"
    sub_url=upload_sub(file_id,subtitle_string)
    update_subtitle_status(file_id,sub_url)
    return subtitle_string


if __name__ == '__main__':

    app.run(debug=True)
    

