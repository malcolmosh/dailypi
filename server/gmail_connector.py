# -*- coding: utf-8 -*-

from __future__ import print_function

from googleapiclient.discovery import build

import base64
import re

# class that connects to Gmail and allows you to parse messages
class GmailConnector():

    def __init__(self, creds):
        # creds are the credentials used to connect to the gmail API
        self.creds = creds
        # A shared Gmail inbox is created specifically for the project.
        #create lists to attachments for all parties
        self.inbox_attachments = []

        # Build API call
        self.service =  build('gmail', 'v1', credentials=self.creds)

    def pull_attachments(self, userID, num_emails=10):
        
        #List all emails
        results = self.service.users().messages().list(userId=userID).execute()
        
        #get id of first 10 emails
        for idx,message in enumerate(results['messages'][0:num_emails+1]):
            message_id=(message['id'])
            message_content=self.service.users().messages().get(userId=userID, id=message_id, format='full').execute()
            #assign default body text to empty
            data=""

            #find the sender
            for header_parts in message_content['payload']['headers']:
                if header_parts['name']== "From":
                    sender=(header_parts['value'])
            
            for parts in message_content['payload']['parts']:
                #get text embedded in email content
                
                #if part has another part
                if "parts" in parts:
                    data=(base64.urlsafe_b64decode((parts["parts"][0]["body"]["data"]).encode("ASCII")).decode("utf-8").replace('\r\n', ''))
                    #remove text between brackets
                    data=re.sub(r'\[.*?\]', ' ', data)
                    
                #else if parts are not recursive
                elif parts['mimeType']=='text/plain':
                    data=(base64.urlsafe_b64decode((parts["body"]["data"]).encode("ASCII")).decode("utf-8").replace('\r\n', ''))
                    #remove text between brackets
                    data=re.sub(r'\[.*?\]', ' ', data)
                    
                #get attachment
                #avoid collecting useless attachments that have no name (logos and other stuff)
                if 'attachmentId' in parts['body'] and parts['filename']!="":
                    att_id = parts['body']['attachmentId']
                
                    # create a list of attachments
                    self.inbox_attachments.append([message_id,att_id, data])
                   
    def grab_first_image(self, userID):
        #get first available attachment
        img_data = self.service.users().messages().attachments().get(userId=userID, messageId=self.inbox_attachments[0][0],id=self.inbox_attachments[0][1]).execute()
        img_data=img_data['data'].encode('UTF-8')
        output_text=self.inbox_attachments[0][2]
        
        #decode string
        file_data=base64.urlsafe_b64decode(img_data)
        
        #open as an image
        import io
        from PIL import Image
        image_to_send=Image.open(io.BytesIO(file_data))
        
        # return image and body of first revelant email
        return(image_to_send,output_text)

