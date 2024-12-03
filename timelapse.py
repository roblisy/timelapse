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
    blob.upload_from_filename(filename, timeout=config['upload_timeout'])

if __name__ == "__main__":
    set_photo_quality()
    while True:
        # Create the file name
        filename = f"""{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg"""
        
        # Call gphoto and take the picture
        capture_image(filename=filename)
        # Upload, with shitty error handling.
        print(f"Uploading original file {filename}")
        try:
            upload_image(filename=filename)
        except:
            print("There was an error")

        #jpg_files = glob.glob(f"{filename}.jpg")
        # for file in jpg_files:
        #    print(f"Uploading {file}")
        #    upload_image(filename=file)
        #    os.remove(file)
        #upload_image(filename=filename)

        # Look for any existing local jpgs and upload them
        # As is this will OVERWRITE any duplicate files in the bucket with the same name
        #jpg_files = glob.glob("*.jpg")
        #for file in jpg_files:
        #    upload_image(file)
        #    print(f"removing {file}")
        #    os.remove(file)
        # Wait for the interval and do it all again
        sleep(config['interval'])