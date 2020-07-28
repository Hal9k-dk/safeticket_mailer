[TOC]

# Intro
This script/program is made to extract infomation about ticket sells from safeticket.dk and send it in an email to the IT Unions there are specials deal for there menbers.

# Requirements
[requirements.txt](requirements.txt)

# Install systemd services
The script is meant to be run user a service user, so if you don't have one, create a service user and enable it as a linger with `sudo loginctl enable-linger USER`.  

Now enter user service user `sudo -u USER -i`.
```
# Go to home folder
cd

# Git clone this project
git clone "https://github.com/Hal9k-dk/safeticket_mailer"

# enter the folder
cd safeticket_mailer

# Create symbolic links for everything bin running this script
bin/install_symbolic_links_to_services.sh
```

# Configuration
Copy the `config.example.py` to `config.py` and change the variables in the file

# Start the systemd tiemr (scheduler for the service)
Check the `systemd.service/safeticket-mailer.timer` to figure out when it is running
```
systemctl --user enable --now safeticket-mailer.timer
```

# A small library have been written to interact with Safeticket
[safeticket_wrapper](lib/safeticket_wrapper)
