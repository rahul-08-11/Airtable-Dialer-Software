import os
from twilio.rest import Client
from pyairtable import Api
import gspread
from datetime import datetime
import pandas as pd

class Twilio:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.PhoneNumber= os.getenv('TWILIO_NUMBER')
        self.twiml_application_sid = os.getenv('TWIML_APPLICATION_SID')
        self.api_key= os.getenv('TWILIO_API_KEY')
        self.api_secret= os.getenv('TWILIO_API_SECRET')
        self.client = Client(self.account_sid, self.auth_token)



class AgentAttributes:
    def __init__(self):
        self.userID = ''                             ##------------------unique identifier
        self.call_status = ''                        ##------------------call status i.e ongoing , disconnected
        self.dealer_name=  ''                        ##------------------dealer name to whom he is on contact
        self.dealer_number = ''                      ##------------------dealer number to whom he is on contactself.
        self.recording_link = ''                     ##------------------call recording link
        self.call_log_sid=''                          ##------------------call log sid
        self.isAvailable=False              ##------------------Agent State Unavailable indicated by False and  Available/Working indicated by True
        self.login_time=None
        self.last_request_time=None

class IncomingHandler:
    
    def __init__(self,Twilio):
        self.incoming_caller_details = {}
        self.length_of_queue=0
        self.twilio=Twilio

    def check_incoming_presence(self,queue_sid): ## this class method is going to run in an interval
        queue_size=self.twilio.client.queues(queue_sid).fetch().current_size

        if queue_size!=0:
            return {
                "incoming":"Yes",
                "queue_size":queue_size,
                "incoming_caller_details":self.incoming_caller_details
            }
        else:
            return {
                "incoming":"No",
                "queue_size":queue_size
            }
    
    def verify_incoming_and_office_hours(self):
        ## this method is been handled using a twilio serverless function 
        pass

    def record_incoming_caller_details(self,callerSid,response_data):
        self.incoming_caller_details[callerSid]=response_data
    

    def check_caller_in_queue(self,callersid):  ## helper function that is used by update_queue_and_details to check the status of caller in queue 
        status=self.twilio.client.calls(callersid).fetch().status    ## e.g. if caller left or hangup while waiting in queue 
        if status == "completed":
            return True
        else:
            return False

    def refresh_queue_line(self): ##this class method is going to run in an interval to ensure the queue line is updated 
        self.incoming_caller_details = {
                    callerSid: details for callerSid, details in self.incoming_caller_details.items() if not self.check_caller_in_queue(callerSid)
                }
       
    



class OutgoingFlow:
    
    def __init__(self):
        self.outgoing_caller_details = {}

    def config_agent_for_outgoing(self):
        pass
    
    def get_outgoing_caller_details(self):
        pass

    def connect_agent_with_outbound(self):
        pass

    def check_disconnection(self):
        pass

    def update_interaction_table(self):
        pass



class PopupDialer:
    def __init__(self):
        self.name=''
        self.number=''
        self.channel_type=''
        

class Credentials:
    def __init__(self) -> None:
        ## Assigned Dummy credentials
        self.user_credentials = {
                "user2002": "dial@123",
                "user2003": "dial@123"
            }
        

class Login(Credentials):
    def __init__(self):
        super().__init__()

    def verify_credentials(self,username,password):
        if username in self.user_credentials and self.user_credentials[username] == password:
            return True
        else:
            return False


class Logout():
    def __init__(self):
        pass

    def reset_agent_attributes(self,Agent):
        Agent.isAvailable=False
        Agent.login_time=None
        Agent.last_request_time=None

    def append_agents_activity_log(self,login_time,calls_count,userid,gof):
        try:
            session_duration = ((datetime.now() - pd.to_datetime(login_time)).total_seconds())/60
                # Format datetime strings
            login_time_formatted = login_time.strftime("%Y-%m-%d %H:%M:%S")  # Change the format here
            logout_time_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Change the format here

            data=[userid,login_time_formatted,logout_time_formatted,session_duration,calls_count]
            gof.get_agent_database().append_row(data)

        except Exception as e:
            print(e)
            return None
            





