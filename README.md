# christmas-tree
Raspberry-pi code for LED christmas tree

hostname ledpi.local
username martin
password *****

----setup new pi-----
flash Rasberry Pi OS Lite (32-bit) on imager, enabling SSH

in cmd 
# ssh martin@ledpi.local
# sudo apt update && sudo apt upgrade -y
# sudo apt install python3 python3-pip git -y


can't install dependencies like GPIO as they are externally managed. a Virtual environment will have to be setup instead.
# python3 -m venv ~/led-env
# source ~/led-env/bin/activate
have to activate everytime. Then commands like pip install RPi.GPIO will work

# deactivate
exits the venv



----setup vscode---
with remote SSH installed:
command palette - "Remote-SSH: Connect to Host..."
then username@ledpi.local
# doesn't work for armv6 - so not raspberry pi zero W



---comands---
# cd
# nano program.py
# sudo venvName/bin/python3 script.py
# sudo ~/led-env/bin/python3 set_led.py 1



