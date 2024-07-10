import subprocess
import sys
import os
import venv

VENV_DIR = '/home/picc/repos/picc-device/venv'

def create_virtual_environment():
    if not os.path.exists(VENV_DIR):
        venv.create(VENV_DIR, with_pip=True)

def install_requirements():
    pip_executable = os.path.join(VENV_DIR, 'bin', 'pip')
    subprocess.check_call([pip_executable, "install", "-r", "requirements.txt"])

def create_service_file():
    service_file_content = f"""
    [Unit]
    Description=Run main.py at startup
    After=network.target

    [Service]
    ExecStart={VENV_DIR}/bin/python /home/picc/repos/picc-device/main.py
    WorkingDirectory=/home/picc/repos/picc-device
    StandardOutput=journal
    StandardError=journal
    Restart=always
    User=picc
    Group=picc
    Environment="PATH={VENV_DIR}/bin"
    Environment="PYTHONPATH={VENV_DIR}/lib/python3.11/site-packages"

    [Install]
    WantedBy=multi-user.target
    """
    with open("/etc/systemd/system/main_script.service", "w") as service_file:
        service_file.write(service_file_content)

def setup_service():
    create_service_file()
    subprocess.check_call(["sudo", "systemctl", "daemon-reload"])
    subprocess.check_call(["sudo", "systemctl", "enable", "main_script.service"])
    subprocess.check_call(["sudo", "systemctl", "start", "main_script.service"])

def add_startup_command():
    bashrc_path = os.path.expanduser("~/.bashrc")
    startup_command = "sudo systemctl start main_script.service\n"
    
    with open(bashrc_path, "r") as bashrc:
        lines = bashrc.readlines()
    
    if startup_command not in lines:
        with open(bashrc_path, "a") as bashrc:
            bashrc.write(startup_command)

# Run the setup
if os.geteuid() != 0:
    print("Please run the script as root.")
else:
    create_virtual_environment()
    install_requirements()
    setup_service()
    add_startup_command()
