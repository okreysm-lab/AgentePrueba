from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def leer_correos():

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    correos = []

    if not messages:
        return []

    for msg in messages:

        txt = service.users().messages().get(userId='me', id=msg['id']).execute()

        headers = txt['payload']['headers']

        subject = ""

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']

        correos.append(subject)

    return correos


if __name__ == "__main__":

    correos = leer_correos()

    for c in correos:
        print(c)