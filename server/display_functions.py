
from io import BytesIO

from gmail_connector import Gmail_connector
from eink_image import Image_transform



def pull_and_display_image(creds):
  #import image from the gmail API

  # initialize connector
  gmail_inbox =  Gmail_connector(creds=creds)

  # pull attachments (num_emails looks at the X most recent emails to be sure we intercept an attachment)
  gmail_inbox.pull_attachments(userID='me', num_emails=3)

  # get the image to send
  image_to_send, output_text = gmail_inbox.grab_first_image(userID = 'me')
 
  # prepare bytes stream
  output_stream = BytesIO()
  #transform image into a low res format for the eink screen
  transformed_image = Image_transform(path_or_image=image_to_send)
  transformed_image.save(output_path_or_stream = output_stream)
    
  # display the image (don't cache it)
  # output.seek resets the pointer to the beginning of the file 
  output_stream.seek(0)
  return output_stream


def prepare_dashboard_for_pi(final_svg_file_path : str):

  # initialize bytes output stream
  output_stream = BytesIO()

  transformed_svg = Image_transform(path_or_image=final_svg_file_path)
  transformed_svg.save(output_path_or_stream = output_stream)

  # display the image (don't cache it)
  # output.seek resets the pointer to the beginning of the file 
  output_stream.seek(0)

  return output_stream