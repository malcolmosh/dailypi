import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap


#function to transform the pic pulled from gmail into a 2 tone & resized image
class Image_transform:
    def __init__(self, imported_image, fit="crop"):
        self.imported_image=imported_image

    def render(self, fit="crop"):
        # fit can be "width" or "crop" or "height"
        #we are using the screen in portrait mode and so flipping the default landscape mode
        w = 480
        h = 800
        
        #create canvas in portrait mode
        canvas = Image.new(mode="1", size=(w, h), color=255) #fill colour for blank space (so, clear frame first)
        draw = ImageDraw.Draw(canvas)
        
        #use the line below if we're working with a path and not an image file
        #image = Image.open(self.imported_image)
        
        #use the line below if we're working with an image file directly
        image = self.imported_image

        #Remove exif orientation
        image = ImageOps.exif_transpose(image)
        
        #option 1 : fit the whole width to the frame
        if fit=="width":
            #Resize image to fit width
            wpercent = (w/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((w,hsize), Image.ANTIALIAS)
            
            #center the image vertically in the middle of the frame
            blank_space=h-image.size[1]
            adjust_height=int(blank_space/2)
            
            #paste on canvas with height adjustment
            canvas.paste(image, (0, 0+adjust_height))

        #option 2 : fit the whole height to the frame
        if fit=="height":
            
            #Resize image by height
            hpercent = (h/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
            image = image.resize((wsize,h), Image.ANTIALIAS)
            
            #center 
            blank_space=h-image.size[1]
            adjust_height=int(blank_space/2)
            #Paste image on canvas
            canvas.paste(image, (0, 0+adjust_height))

        #option 3 : crop the image in the center 
        if fit=="crop":
        
            #Resize image by height
            hpercent = (h/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
            image = image.resize((wsize,h), Image.ANTIALIAS)
            
            #Center the image on the frame. First, set overflow
            left = (image.size[0] - w)/2
            top = (image.size[1] - h)/2
            right = (image.size[0] + w)/2
            bottom = (image.size[1] + h)/2
            
            # Crop the center of the image
            image = image.crop((left, top, right, bottom))

            #Paste image on canvas
            canvas.paste(image, (0, 0))
        
        return(canvas)


