# Long Term Photo

Shoot a photo from a Raspberry Pi controlled camera using the `timelapse.py` script on a configurable frequency. Send the files up to Google Cloud bucket. Rinse, wash, repeat.

## Setup
[Check out the setup markdown for more specific instructions](setup.md). This project requires:
- a Raspberry Pi
- [a camera which supports gphoto2](http://www.gphoto.org/proj/libgphoto2/support.php)
- power supplies, USB cables
- a Google Cloud account with storage (Google Cloud Storage, aka GCS)
    - we use a service account for the upload to GCS
- Github

## Enclosure

The STL files to 3d print my version of the enclosure are in the subdirectory "3d_print_files". That subdirectory also includes a PDF with additional information, including a visualization and complete parts list.

## Video Output

The script generates JPG images in the format `YYYY-MM-DD_HH-MM-ss.jpg`. I use ffmpeg to put those all together into an mpeg video. First I download all JPGs from the bucket onto a Google Compute instance within my cloud project (probably not the best) with this command:

```
gsutil cp -r gs://<bucket_name>/ .
```

Then cd into that directory and run the ffmepg command, to create "output.mp4":

```
ffmpeg -framerate 30 -pattern_type glob -i 2023-04-*.jpg -c:v libx265 output.mp4
```


## To Do

In no particular order:
- Create an array of times for each day that finds "interesting" times, such as sunrise, sunset, or other times of day that might be visually interesting.
- Take pictures only during the interesting times (ex. - sunrise, sunset)
- Take less frequent pictures at night (maybe?)
