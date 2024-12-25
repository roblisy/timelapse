#!/bin/sh
# Startup Bash script for our timelapse project.
# To schedule this to run on reboot on your Raspberry Pi:
# sudo crontab -e
# add the line below to your file:
# @reboot sh /home/rob/timelapse/startup.sh >/home/rob/timelapse/logs/cronlog 2>&1
# This executes the startup.sh script upon reboot

# Start a TMUX session named "take_photos", activate our environment, and run our Python program
tmux new-session -d -s take_photos \
    # Get to the correct directory
    cd /home/rob/timelapse/ && \
    # Create the logs directory if it does not exist.
    mkdir -p logs && \
    # Activate our environment
    . timelapse/bin/activate && \
    # run our Python script
    python timelapse.py
