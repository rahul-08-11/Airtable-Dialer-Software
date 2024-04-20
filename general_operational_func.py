import logging 
import re
from oauth2client.service_account import ServiceAccountCredentials
import gspread



def setLogs(logfile):
    '''Set Up logging'''
    logging.basicConfig(
    filename=logfile,
    level=20, filemode='a', # You can adjust the log level as needed
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
    log = logging.getLogger("my-logger")
    # Create a console (stream) handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Set the formatter for the console handler
    console_handler.setFormatter(formatter)
    # Add the console handler to the logger
    log.addHandler(console_handler)
    return log

def phone_number_formatter(phone_number):
    partially_cleaned_number = phone_number.split(" ext. ")[0]
    clean_phone_number = ''.join(filter(str.isdigit, partially_cleaned_number))
    if clean_phone_number.startswith("1") and len(clean_phone_number) == 11 and len(clean_phone_number)>1:
        clean_phone_number = clean_phone_number[1:]
        return '+1' + clean_phone_number
    else:
        return phone_number
    

def get_recording_url(recording_data):
  
    print(f"recording data : {recording_data}")
    if recording_data:
        try:
            recording_uri=recording_data.uri
            media_url = 'https://api.twilio.com'+recording_uri.replace("json","mp3")
            # log.info("get recording url function",media_url)
            return media_url
        except Exception as e:
            pass
            # log.warning(f"warning get recording url: ============================>{e}")
    else:
        return ''
    
def get_agent_database():
    try:
        scope = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("agent_data.json",scope)
        google_client = gspread.authorize(creds)
        sh = google_client.open("AgentDetails")
        sheet=sh.worksheet("AgentsActivity")
        return sheet
    except Exception as e:
        print(e)