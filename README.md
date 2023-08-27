# dispatchPi
## A communicating e-paper picture frame, powered by a Raspberry Pi Zero

<img src="https://i.imgur.com/E302Bw2.jpg|width=100px" width="200">

**[Follow the complete tutorial here!](https://malcolmosh.github.io/pages/DispatchPi/dispatchpi_part0/)

The frame's job is to display an image from a fixed URL at specific intervals. There is a Flask app hosted at this address. Whenever it is pinged, it pulls the latest image received in a Gmail inbox, with the help of the Gmail API and Auth 2.0.

There are two folders to browse here:

- **Screen** contains the code found on the Raspberry Pi device
- **Server** holds the code hosted online in a dockerized Flask app 
