import os
import subprocess
import yaml
import glob
from datetime import datetime
from time import sleep
from google.cloud import storage

# Load our config options
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

def capture_image(filename: str):
    """Function to call gphoto2 and download the image locally to the Raspberry Pi"""
    subprocess.run(["gphoto2", "--capture-image-and-download", "--filename", filename])

def upload_image(filename: str):
    """Upload the image to Google Cloud Storage"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(config['bucket_name'])
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)

if __name__ == "__main__":
    while True:
        # Create the file name
        filename = f"""{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg"""
        
        # Call gphoto and take the picture
        capture_image(filename=filename)
        upload_image(filename=filename)

        # Look for any existing local jpgs and upload them
        # As is this will OVERWRITE any duplicate files in the bucket with the same name
        jpg_files = glob.glob("*.jpg")
        for file in jpg_files:
            upload_image(file)
            print(f"removing {file}")
            os.remove(file)
        # Wait for the interval and do it all again
        sleep(config['interval'])