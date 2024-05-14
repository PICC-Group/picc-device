import subprocess
import sys
import os


subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def create_service_file():
    service_file_content = """
    [Unit]
    Description=Run main.py at startup
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/pi/main.py
    WorkingDirectory=/home/pi
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target
    """
    with open("/etc/systemd/system/main_script.service", "w") as service_file:
        service_file.write(service_file_content)

def setup_service():
    create_service_file()
    subprocess.check_call(["sudo", "systemctl", "enable", "main_script.service"])
    subprocess.check_call(["sudo", "systemctl", "start", "main_script.service"])

# Run the setup
if os.geteuid() != 0:
    print("Please run the script as root.")
else:
    setup_service()
