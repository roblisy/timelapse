# Long Term Photo

Shoot a photo from a Rasbperry Pi controled camera on a configurable frequency. Send the files up to Google Cloud bucket. Rinse, wash, repeat.

## Setup
[Check out the setup markdown for more specific instructions](setup.md). This project requires:
- a Raspberry Pi
- [a camera which supports gphoto2](http://www.gphoto.org/proj/libgphoto2/support.php)
- power supplies, USB cables
- a Google Cloud account with storage (Google Cloud Storage, aka GCS)
    - we use a service account for the upload to GCS

## Video Output

The script generates JPG images in the format `YYYY-MM-DD_HH-MM-ss.jpg`. I use ffmpeg to put those all together into an mpeg video. First I download all JPGs from the bucket onto a Google Compute instance within my cloud project (probably not the best) with this command:

```
gsutil cp -r gs://<bucket_name>/ .
```

Then cd into that directory and run the ffmepg command, to create "output.mp4":

```
ffmpeg -framerate 30 -pattern_type glob -i 2023-04-\*.jpg -c:v libx265 output.mp4
```

## To Do

In no particular order:
- add shell script to download and process JPGs
- create an array of times for each day that finds "interesting" times
- take pictures only during the interesting times (ex. - sunrise, sunset)
- take less frequent pictures at night
