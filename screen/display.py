import os
import sys
import requests
from waveshare_epd import epd7in5_V2
from PIL import Image, ImageFont, ImageDraw
import datetime
import re
from pathlib import Path

import random

#import local functions
from image_transform_local import Image_transform

# find script directory
dir_path = os.path.dirname(os.path.realpath(__file__))

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
        # capture input from command line
        battery_percentage_str = sys.argv[1]

        # Extract the number from the string
        battery_percentage = re.findall(r'[0-9]+', battery_percentage_str)[0]
    
        return battery_percentage
    
    except: 
         return "??"


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


    pic_path = os.path.join(dir_path, "pics")
    
    file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.JPG', '.JPEG', '.PNG', '.BMP', '.GIF'] # create a sect of file extensions
    
    all_images = [p.resolve() for p in Path(pic_path).glob("**/*") if p.suffix in file_extensions]  # Find all matching files for the given patterns in all subfolders of pic_path

    if not all_images:
        raise ValueError("No images found in the local directory. Check that your folder contains all your file types specified.")

    #choose a random image path
    random_image = random.choice(all_images)

    #run the local function to process and display it
    local_image=Image_transform(imported_image=random_image)
    image=local_image.render(fit="crop")
    show_image(image)

