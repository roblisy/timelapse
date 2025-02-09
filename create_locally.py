import argparse
import datetime
import os
import subprocess
import shutil
import logging
# GCP import
from google.cloud import storage

# There's some storage API bug that requires this as a workaround.
# See: https://github.com/googleapis/python-storage/issues/992
from google.cloud.storage.retry import DEFAULT_RETRY

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Set to INFO for less output
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('create_locally.log')
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

def download_images(bucket_name, local_dir, date_str):
  """
  Downloads JPG images from a Google Cloud bucket with a matching date pattern.

  Args:
    bucket_name: Name of the Google Cloud Storage bucket.
    local_dir: Local directory to download images to.
    date_str: Date string in YYYY-MM-DD format.
  """
  logger.info(f"Starting download of images from GCS for {date_str}")
  gutil_cmd = f"gsutil -m cp gs://{bucket_name}/{date_str}* {local_dir}"
  os.system(gutil_cmd)
  logger.info(f"Download of images from GCS complete for {date_str}")

def generate_daily_video(input_dir, output_file, date_str, fps):
  """
  Generates an MP4 video using ffmpeg with the given input images.

  Args:
    input_dir: Directory containing the input images.
    output_file: Path to the output MP4 file.
  """
  logger.info(f"Starting video generation for {date_str}")
  ffmpeg_cmd = f"ffmpeg -framerate {fps} -pattern_type glob -i '{input_dir}/{date_str}*.jpg' -c:v libx264 -preset ultrafast {output_file}"
  os.system(ffmpeg_cmd)
  logger.info(f"Video generation complete for {date_str}")

def generate_weekly_video(input_dir, output_file, week_start_str, week_end_str, fps):
    """Generates a weekly MP4 video."""
    logger.info(f"Starting video generation for week of {week_start_str} - {week_end_str}")

    # Create a list of image files, sorted by filename
    image_files = sorted([
        os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".jpg")
    ])

    if not image_files:
      logger.warning("No images found in %s for week of %s - %s", input_dir, week_start_str, week_end_str)
      return # Exit early if no images exist

    # Create a text file listing the image files (required for complex filter)
    with open("image_list.txt", "w") as f:
        for image_file in image_files:
            f.write(f"file '{image_file}'\n")

    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",  # Important for file paths
        "-i", "image_list.txt",
        "-vf", "fps=" + str(fps), # Set framerate here
        "-c:v", "libx264",
        "-preset", "ultrafast",
        output_file,
    ]
    
    # Execute ffmpeg command
    try:
        subprocess.run(ffmpeg_cmd, check=True) # check=True will raise an exception if the command fails
        logger.info(f"Video generation complete for week of {week_start_str} - {week_end_str}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed: {e}")
    finally:
        os.remove("image_list.txt") # Clean up the file list


def upload_video_to_gcs(bucket_name, local_file):
  """
  Uploads an MP4 video to the Google Cloud Storage bucket.

  Args:
    bucket_name: Name of the Google Cloud Storage bucket.
    local_file: Path to the local MP4 file.
  """
  logger.info(f"Starting upload of video to GCS for {local_file}")
  storage_client = storage.Client()
  bucket = storage_client.get_bucket(bucket_name)
  blob = bucket.blob(os.path.basename(local_file))
  blob.upload_from_filename(local_file, retry=DEFAULT_RETRY)
  logger.info(f"Upload of video to GCS complete for {local_file}")

def delete_images(local_dir):
  """
  Deletes all JPG files within the specified directory.

  Args:
    local_dir: Directory containing the JPG files to be deleted.
  """
  logger.info(f"Starting deletion of images in {local_dir}")
  for filename in os.listdir(local_dir):
    if filename.endswith(".jpg"):
      file_path = os.path.join(local_dir, filename)
      os.remove(file_path)
  logger.info(f"Deletion of images in {local_dir} complete")

def main():
    parser = argparse.ArgumentParser(description="Generate videos from images in Google Cloud Storage.")
    parser.add_argument("--video_type", type=str, required=True, default='daily', help="Default is 'daily', but weekly is also supported.")
    parser.add_argument("--start_date", type=str, required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end_date", type=str, required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument("--bucket_name", type=str, required=True, help="Name of the Google Cloud Storage bucket.")
    parser.add_argument("--prefix", type=str, required=False, help="Prefix string to append to the video name.")
    parser.add_argument("--fps", type=int, default=18, required=False, help="Frames per second for the video. Default is 18.")
    parser.add_argument("--delete_images", action="store_false", help="Delete images after generating video. Default is to delete the images.")
    args = parser.parse_args()

    logger.debug(f"Arguments: {args}")

    # Some easy date formatting.
    start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")

    # Create a video for a single day
    if args.video_type == "daily":
      logger.info("Generating daily videos")
      for date in (start_date + datetime.timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)):
          logger.info(f"Starting video generation step for {date}")
          # Local environment setup - create a directory for the images.
          date_str = date.strftime("%Y-%m-%d")
          local_dir = f"images_{date_str}"
          logger.debug(f"Local directory: {local_dir}")
          os.makedirs(local_dir, exist_ok=True)
          
          # Download images from GCS, generate video, and upload video back to GCS.
          download_images(args.bucket_name, local_dir, date_str)
          output_file = f"{args.prefix}_{date_str}.mp4"
          generate_daily_video(local_dir, output_file, date_str, args.fps)
          upload_video_to_gcs(args.bucket_name, output_file)

          # Clean up local directory (optional)
          if args.delete_images:
              shutil.rmtree(local_dir, ignore_errors=True)
              #os.remove(output_file)
          else:
              print(f"Keeping images in {local_dir}")

    # Create a video for a week
    # Thematically this creates 7 daily videos, then stiches them together at the last step.
    # I can probably clean this up a bit, and include it in the above IF statement, but for now
    # this works.
    elif args.video_type == "weekly":
        logger.info("Generating weekly videos")
        current_date = start_date
        while current_date <= end_date:
            week_end_date = current_date + datetime.timedelta(days=6)
            if week_end_date > end_date:
                week_end_date = end_date

            week_start_str = current_date.strftime("%Y-%m-%d")
            week_end_str = week_end_date.strftime("%Y-%m-%d")
            local_dir = f"images_{week_start_str}_{week_end_str}"
            logger.debug(f"Local directory: {local_dir}")
            os.makedirs(local_dir, exist_ok=True)

            for date in (current_date + datetime.timedelta(days=x) for x in range(0, (week_end_date - current_date).days + 1)):
                date_str = date.strftime("%Y-%m-%d")
                download_images(args.bucket_name, local_dir, date_str)

            output_file = f"{args.prefix}_{week_start_str}_{week_end_str}.mp4"
            generate_weekly_video(local_dir, output_file, week_start_str, week_end_str, args.fps)
            upload_video_to_gcs(args.bucket_name, output_file)

            if args.delete_images:
                shutil.rmtree(local_dir, ignore_errors=True)
            else:
                print(f"Keeping images in {local_dir}")

            current_date = week_end_date + datetime.timedelta(days=1)

if __name__ == "__main__":
    main()

# TODO:
# - maybe investigate how to NOT require manual YouTube authorization over longer periods?