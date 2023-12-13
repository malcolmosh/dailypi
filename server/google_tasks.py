# -*- coding: utf-8 -*-

from __future__ import print_function

from googleapiclient.discovery import build

import base64
import re

# class that connects to Gmail and allows you to parse messages
class GtasksConnector():

    def __init__(self, creds):
        # creds are the credentials used to connect to the Google Tasks API
        self.creds = creds
        self.task_list_ids = []

        # Build API call
        self.service =  build('tasks', 'v1', credentials=self.creds)
        
    def get_lists(self):
        # Call the Tasks API
        results = self.service.tasklists().list(maxResults=10).execute()
        items = results.get('items', [])

        if not items:
            print('No task lists found.')
            return

        print('Task lists:')
        for item in items:
            print(u'{0} ({1})'.format(item['title'], item['id']))
            #self.task_list_ids.append(item['id'])


    def get_tasks(self, tasklist_id):
        # Call the Tasks API
        results = self.service.tasks().list(tasklist=tasklist_id).execute()
        items = results.get('items', [])

        # Check if no tasks are found
        if not items:
            print("No tasks found.")
            return ["No tasks found."]
        
        # Return a list of grocery items
        return [item["title"] for item in items]

        
    

