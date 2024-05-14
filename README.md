# The main project repository for the PICC-Device.

The purpose is to process signals from a NanoVNA to controll a RC car. This repository contains everything
- The S-parameters S11 and S21 from the NanoVNA are the inputs and the code will output distance and angle values continuously.
- A web app is launched at `http://ip-address:5000/` creating an interface showing angle, distance, other system data.
- System configuration and settings can be altered through this interface.
- If setup is done right, the code should run at startup on a Raspberry Pi.

This code is devoloped by The PICC Group at Lund University for the 2024 IEEE AP-S Student Design Contest.

## Setup
- Clone the repository.
- Run the setup.py file with `sudo python setup.py`.
- Restart the Raspberry Pi.

### The PICC Group
The PICC Group is a project in the 2024 IEEE AP-S Student Design Contest. 
[The PICC Group Website](https://picc-group.github.io)
[The PICC Group](picc-logo.png)

##### Members
- Teo Bergkvist
- Otto Edgren
- Oscar Gren
- Måns Jacobsson
- Christian Nelson
- Dr. Johan Lundgren (Mentor)
