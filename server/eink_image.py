import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import cairosvg
from io import BytesIO


class Image_transform:
    def __init__(self, path_or_image):
        self._path_or_image = path_or_image
        self._image_file = self.load_image()

    def load_image(self):
        if isinstance(self._path_or_image, str) and self._path_or_image.endswith(".svg"):
            # Rasterize the SVG to PNG
            png_image = cairosvg.svg2png(url=self._path_or_image, dpi=300)
            # Convert PNG bytes data to Image object
            img = Image.open(BytesIO(png_image))
            
            # Create a white background image
            white_bg = Image.new("RGBA", img.size, "WHITE")
            white_bg.paste(img, (0, 0), img)  # The last parameter is the alpha mask for transparency
            return white_bg.convert("RGB")  # Convert to RGB to remove alpha channel
        else:
            # If it's an Image object or another format, return as it is.
            return self._path_or_image

    def render(self, height, width):
        # Resize image by height using a crop strategy 
        canvas = Image.new(mode="1", size=(width, height), color=(255))
        image = ImageOps.exif_transpose(self._image_file)

        hpercent = (height/float(image.size[1]))
        wsize = int((float(image.size[0])*float(hpercent)))
        image = image.resize((wsize,height), Image.LANCZOS)

        # Center the image on the frame
        left = (image.size[0] - width) / 2
        top = (image.size[1] - height) / 2
        right = (image.size[0] + width) / 2
        bottom = (image.size[1] + height) / 2

        # Crop the center of the image
        image = image.crop((left, top, right, bottom))

        # Paste image on canvas
        canvas.paste(image, (0, 0))

        return canvas

    def save(self, output_path_or_stream):
        """
        Save the rendered image to the specified output path or stream.
        """
        if isinstance(self._path_or_image, str) and self._path_or_image.endswith(".svg"): #if we're dealing with an SVG filepath
            self._image_file.save(output_path_or_stream, format = "PNG")
        else:
            final_image = self.render(height=800, width=480) # if we're dealing with an image directly
            final_image.save(output_path_or_stream, format = "PNG")
