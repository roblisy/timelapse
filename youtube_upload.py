import argparse
import datetime
import os
import shutil
import logging
# GCP import
#from google.cloud import storage
# YouTube Imports
import google_auth_oauthlib
import google_auth_httplib2
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

# YouTube scope7
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set to INFO for less output
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('youtube_upload.log')
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

def authenticate_youtube():
    """Authenticates with the YouTube Data API using OAuth 2.0.

    This function sets the `OAUTHLIB_INSECURE_TRANSPORT` environment variable
    (which should be avoided in production) and then uses the
    `InstalledAppFlow` to authenticate with the YouTube API.  It reads
    credentials from a client secrets file.

    Returns:
        googleapiclient.discovery.Resource: A YouTube API service object.

    Raises:
        google_auth_oauthlib.flow.FlowError: If there's an issue with the OAuth flow.
        FileNotFoundError: If the client secrets file is not found.
        # Add other exceptions that might be raised.
    """
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    client_secret = "/Users/rob/Desktop/Junk/timelapse/timelapse_youtube_creds.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secret, scopes=["https://www.googleapis.com/auth/youtube.upload"])
    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    logger.info("Authenticated to YouTube API")

    return youtube

def upload_video_to_youtube(youtube, date_str, media_file):
    """
    Uploads a video to YouTube using the YouTube Data API.
    """
    request_body = {
        "snippet": {
            "categoryId": "22",
            "playlistId": "PLYG-zpqrLYkvQCLkIEm9kwMIpS2AXITuO",
            "title": f"Seattle Skyline - {date_str}",
            "description": f"Timelapse photo of the Seattle skyline for {date_str}.",
        },
        "status": {
            "privacyStatus": "public",
        },
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=googleapiclient.http.MediaFileUpload(media_file, chunksize=-1, resumable=True),
    )
    logger.info("Starting upload of video to YouTube")

    response = None

    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
        print(f"Upload complete! Video ID: {response['id']}")

def main():
    """
    Main function for uploading videos to YouTube.

    This function parses command-line arguments to determine the date range and file prefix for the videos to be uploaded. 
    It authenticates with the YouTube API, uploads videos for each date in the specified range, and optionally cleans up 
    local video files after uploading.

    Args:
        --start_date (str): Start date in YYYY-MM-DD format.
        --end_date (str): End date in YYYY-MM-DD format.
        --prefix (str, optional): Prefix for video files. Default is 'skyline'.
        --no_cleanup (bool, optional): If specified, local copies of videos will not be deleted after upload. Default is to delete.

    Raises:
        ValueError: If the date format is incorrect.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Upload videos from local storage to YouTube")
    parser.add_argument("--start_date", type=str, required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end_date", type=str, required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument("--prefix", type=str, required=False, default="skyline", help="Prefix for video files. Default is 'skyline'.")
    # For argparse - store the "action"  setting IF the argument is on the command line. If it's not, the argument is the opposite.
    parser.add_argument("--no_cleanup", action="store_false", help="Delete local copies of videos after upload. Default is to delete.")
    args = parser.parse_args()

    logger.debug(f"Arguments: {args}")


    # Some easy date formatting.
    start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")

    # YouTube part - authenticate for uploading. Ideally only do this once.
    youtube = authenticate_youtube()
    logger.info("Authenticated to YouTube API")

    for date in (start_date + datetime.timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)):
        logger.info (f"Starting video upload for {date}")
        date_str = date.strftime("%Y-%m-%d")
        video_file = f"{args.prefix}_{date_str}.mp4"
        # Upload video to YouTube
        upload_video_to_youtube(youtube=youtube, date_str=date_str, media_file=video_file)

    # Clean up local directory (optional)
    if args.no_cleanup:
        for file in os.listdir("."):
            if file.endswith(".mp4"):
                os.remove(file)
    else:
        print(f"Keeping videos in {os.getcwd()}")

if __name__ == "__main__":
    main()