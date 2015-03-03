#!/usr/bin/python

import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

import base64

from pprint import pprint

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available
# scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
    credentials = run(flow, STORAGE, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)

# # Retrieve a page of threads
# labels = gmail_service.users().labels().list(userId='me').execute()
#
# # Print ID for each thread
# if labels['labels']:
#     for label in labels['labels']:
#         print label
#         # print 'Label: % , ID: %s' % (label['name'], label['id'])
# exit()
messages = gmail_service.users().messages().list(labelIds='Label_50', userId='me', q='has:attachment', maxResults=300).execute()

pprint(messages)
# Print ID for each thread
if messages['messages']:
    while True:
        for i, message in enumerate(messages['messages']):
            print 'Getting message %s: %s' % (i, message['id'])
            gmessage = gmail_service.users().messages().get(userId='me', id=message['id']).execute()
            payload = gmessage['payload']
            if 'filename' in payload and payload['filename']:
                print 'Payload has filename %s' % payload['filename']
            if 'parts' in payload:
                print '\tFound %s parts' % (len(payload['parts']))
                parts = payload['parts']
                for part in parts:
                    if part['filename']:
                        print '\t\tFound attached file %s' % part['filename']
                        if 'data' in part['body']:
                            print '\t\tData in body'
                            data = part['body']['data']
                        else:
                            print '\t\tDownloading attachment id %s ...' % part['body']['attachmentId'][:10],
                            attachment = gmail_service.users().messages().attachments().get(userId='me', messageId=gmessage['id'], id=part['body']['attachmentId']).execute()
                            print ' Done'
                            data = attachment['data']
                        outfile = open(part['filename'], 'w')
                        outfile.write(base64.urlsafe_b64decode(data.encode('UTF-8')))
                        outfile.close()
        if 'nextPageToken' in messages and messages['nextPageToken']:
            print 'Found next page token, getting next page'
            messages = gmail_service.users().messages().list(labelIds='Label_50', userId='me', q='has:attachment', maxResults=300, pageToken=messages['nextPageToken']).execute()
        else:
            print 'No next page token, exiting'
            break
