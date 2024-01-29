# infoPi
## A simple e-paper dashboard, powered by a Raspberry Pi Zero

DailyPi is a straightforward home dashboard that shows daily tasks, events and weather on a 7.5 inch e-paper screen. All of the data preparation is conducted server-side, through a web app hosted on Google Cloud Run, which collects information from all relevant APIs and outputs a PNG image at a fixed URL. The local device is composed of a a Raspberry Pi zero W computer physically wired to an e-ink screen. The Pi's task is to regurlarly pull the dasbhoard PNG via Wifi and push it instantly to the display.

<img src="/main_splash_image.jpg|width=500px" width="500">

**[Follow the complete tutorial here!](https://malcolmosh.github.io/blog/2024/infopi-tutorial/)**
