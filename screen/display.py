import os
#import sys
import requests
from waveshare_epd import epd7in5_V2
from PIL import Image, ImageFont, ImageDraw
from pisugar import *
import datetime

import glob, random

#import local functions
from image_transform_local import Image_transform

#function to display image
def show_image(image):
    try:
            # Display init, clear
            display = epd7in5_V2.EPD()
            display.init() #update 
            
            #display the image
            display.display(display.getbuffer(image)) 

    except IOError as e:
            print(e)

    finally:
        display.sleep()

def get_battery_percentage():
    try : 
        # get battery percentage
        conn, event_conn = connect_tcp('newframe.local')
        s = PiSugarServer(conn, event_conn)
        battery_percentage = str(round(s.get_battery_level()))
        local_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Battery_percentage at {local_datetime} was {battery_percentage}") # print percentage with date for logs
        return battery_percentage
    except: 
         return "XX"


try:
    # fetch web page
    filename="https://dashboardpi-of6skuawsa-nn.a.run.app/dashboard_homepage"

    #pull image from web
    response = requests.get(filename, stream=True)
    response.raw.decode_content = True
    image = Image.open(response.raw)

    # overlay battery percentage on image picked up from web

    updated_image = Image.new(mode="1", size=(800, 480), color=255) # create new image
    script_dir = os.path.dirname(os.path.realpath(__file__))
    font_path = os.path.join(script_dir, "fonts", "Roboto-Medium.ttf")
    font = ImageFont.truetype(font_path, 15) # select font
    updated_image.paste(image, (0, 0)) # paste dashboard on canvas

    draw = ImageDraw.Draw(updated_image) # create Draw
    draw.text((90, 438), get_battery_percentage(), font=font, fill=0, align='center') # Add text to image

    #push it to the screen
    show_image(updated_image)

#if an error occurs (connection slow or missing), print a random local picture instead
except Exception as e:
    local_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Exception occurred at {local_datetime}, printing local image instead : {e}")

    #set the directory
    script_dir = os.path.dirname(os.path.realpath(__file__))

    #set the filetypes to pick from (here png and jpg)
    png_files = os.path.join(script_dir, "pics", "*.png")
    jpg_files = os.path.join(script_dir, "pics", "*.jpg")
    file_path_type = [png_files, jpg_files]

    # Get list of all PNG and JPG images
    png_images = glob.glob(png_files)
    jpg_images = glob.glob(jpg_files)

    # Combine both lists
    images = png_images + jpg_images

    # Check if images list is empty
    if not images:
        print(f"Oops at {local_datetime} : No local images found!")
    else:
        # Choose a random image path
        random_image = random.choice(images)
        #run the local function to process and display it
        local_image=Image_transform(imported_image=random_image)
        image=local_image.render(fit="crop")
        show_image(image)


