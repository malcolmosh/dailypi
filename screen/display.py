import os
#import sys
import requests
from waveshare_epd import epd7in5_V2
from PIL import Image
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

try:
    # get web link
    # don't forget to point to the proper frame
    filename="https://YOUR_CLOUD_RUN_WEBSITE.a.run.app/satellite_frame"

    # URL could also be https://YOUR_CLOUD_RUN_WEBSITE.a.run.app/earth_frame
    
    #pull image from web
    response = requests.get(filename, stream=True)
    response.raw.decode_content = True
    image = Image.open(response.raw)

    #push it to the screen
    show_image(image)
    

#if an error occurs (connection slow or missing), print a random local picture instead
except:

    #set the directory
    directory = os.path.join(os.path.dirname(__file__), "pics")

    #set the filetypes to pick from (here, heic and jpg)
    file_path_type = [(directory+"/*.heic"), (directory+"/*.jpg")]
    images = glob.glob(random.choice(file_path_type))

    #choose a random image path
    random_image = random.choice(images)

    #run the local function to process and display it
    local_image=Image_transform(imported_image=random_image)
    image=local_image.render(fit="crop")
    show_image(image)


