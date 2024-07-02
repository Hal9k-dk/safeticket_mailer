[TOC]

# Intro
This script/program is made to extract information about ticket sells from safeticket.dk and send it in an email to the IT Unions there are specials deal for there members.  

Here are a list of the scripts arguments. Most of them are there to help configure it.  
**Note:** This script will not send emails before the `--send-emails` argument is used.
```
usage: main.py [-h] [--debug] [--events] [--tickets] [--ticket-fields] [--ticket-stats] [--show-emails] [--send-emails]

SafeTicket Mailer

optional arguments:
  -h, --help       show this help message and exit
  --debug          Print a lot of info
  --events         Print all events
  --tickets        Print all the types of ticket of an event
  --ticket-fields  Print all the possible fields existion for the tickets
  --ticket-stats   Print ticket types and there stats for the event
  --show-emails    Display the email there is going to be sendt
  --send-emails    This will send the emails to the unions
```

# Requirements
[requirements.txt](requirements.txt)

# Install systemd services
The script is meant to be run user a service user, so if you don't have one, create a service user and enable it as a linger with `sudo loginctl enable-linger USER`.  

Now enter user service user `sudo -u USER -i`.
```
# Go to the home folder
cd

# Git clone this project
git clone "https://github.com/Hal9k-dk/safeticket_mailer"

# enter the folder
cd safeticket_mailer

# Create symbolic links for everything bin running this script
bin/install_symbolic_links_to_services.sh
```

# Configuration
Copy the `config.example.py` to `config.py` and change the variables in the file.
There are a lot of comment/description for all the variables in the config-file that it shouldn't be a problem mail it work.

Check out the [config.example.py](config_example.py) file.

# Start the systemd tiemr (scheduler for the service)
Check the `systemd.service/safeticket-mailer.timer` to figure out when it is running
```
systemctl --user enable --now safeticket-mailer.timer
```

# A small library have been written to interact with Safeticket
[safeticket_wrapper](src/lib/safeticket_wrapper)
