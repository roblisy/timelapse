# Setup Instructions

Setup generally involves a few overarching steps.

### Set up the Raspberry Pi and imaging software
- Image the OS for a Raspberry Pi (Raspberry Pi OS 64bit has been tested)
    - I use Raspberry Pi Imager and set custom install unstructions to join my WiFi, allow SSH, and set a static hostname.
- Boot the Pi and SSH into it
- [Install GPhoto2](https://www.codemacs.com/raspberrypi/howtoo/setting-up-gphoto2-on-raspberry-pi.6659091.htm)
    - `sudo apt-get install libgphoto2-dev`
    - `sudo apt-get install gphoto2`
- `git clone https://github.com/roblisy/timelapse.git`
- `cd timelapse`

### Configure Python environment

This step installs the packages Python needs for running our program.

- [Install Google Cloud SDK](https://cloud.google.com/sdk/docs/install#deb)
- Create a Google Cloud service account
- Grant the service account the roles `Storage Object User` and `Storage Object Viewer`
- Create the JSON key file file and download it to the Raspberry Pi using SCP or SFTP
- Create a virtual environment
    - `python3 -m venv timelapse`
    - `source ./timelapse/bin/activate`
- Install Google Cloud Storage and other required packages
    - `pip install requirements.txt`

### Start Python file as a system service
