import os
import subprocess
import sys
import yaml
import glob
from datetime import datetime
from time import sleep
from google.cloud import storage

# Load our config options
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

def set_photo_quality():
    """
    Uses gphoto2 settings specific to my camera model to set the image size and quality.
    We don't really need super high quality images, since they will be stacked on top of
    each other and processed into a timelapse movie.
    """
    subprocess.run(["gphoto2", "--set-config", "imagequality=0"]) # Quality standard
    subprocess.run(["gphoto2", "--set-config", "imagesize=2"]) # Size small
    subprocess.run(["gphoto2", "--set-config", "expprogram=15"]) # Landscape exposure program
    
def capture_image(filename: str):
    """Function to call gphoto2 and download the image locally to the Raspberry Pi"""
    subprocess.run(["gphoto2", "--capture-image-and-download", "--filename", filename])

def upload_image(filename: str):
    """Upload the image to Google Cloud Storage"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(config['bucket_name'])
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)

def delete_local(filename: str):
    """
    Function to delete a local file if and only if the file exists in our GCP bucket
    """
    
    # Do all the GCS housekeeping
    storage_client = storage.Client()
    bucket = storage_client.bucket(config['bucket_name'])
    blob = bucket.blob(filename)

    # try/except the local file and GCS sync
    try:
        blob.reload()  # Check if the blob exists
        print(f"File '{filename}' already exists in GCS. Deleting local file.")
        os.remove(filename)
        return True
    except Exception as e:
        if "404 Not Found" in str(e): #check the error message for 404
            print(f"File '{filename}' not found in GCS. Uploading...")
            try:
                blob.upload_from_filename(filename)
                print(f"File '{filename}' uploaded successfully.")
                return True
            except Exception as upload_error:
                print(f"Error uploading file: {upload_error}")
                return False
        else:
            print(f"An error occurred: {e}")
            return False


if __name__ == "__main__":
    set_photo_quality()
    while True:
        # Create the file name
        filename = f"""{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg"""
        
        # Call gphoto and take the picture
        capture_image(filename=filename)
        # Upload, with shitty error handling.
        try:
            print(f"Uploading original file {filename}")
            upload_image(filename=filename)
        except Exception as e:
            print(f"""There was an error: {e}""")
        
        # Find all local jpgs, check if they exist in GCS. If they do, upload them and delete local
        jpg_files = glob.glob("*.jpg")
        for file in jpg_files:
            delete_local(file)

        # Wait for the interval and do it all again
        sleep(config['interval'])