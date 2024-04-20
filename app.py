import re
from flask import Flask, Response, jsonify, request,render_template
from flask_cors import CORS
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import Dial, VoiceResponse
from flasgger import Swagger
import json
from datetime import timedelta,datetime
import dialer_classes as dialer
from dotenv import load_dotenv
import client_data_operation as cdo
import general_operational_func as gof
from datetime import datetime
####################################### App Initialization#################################################################
app = Flask(__name__)
CORS(app)                                                    ## Enable Cross Origin Resource Sharing
swagger=Swagger(app)

###################################### Supportive or Parent Class Object #################################################

Twilio = dialer.Twilio()                       # Instantiate Twilio client for communication with Twilio APIs
Agent = dialer.AgentAttributes()               # Instantiate AgentAttributes class to represent agent attributes
Incoming = dialer.IncomingHandler(Twilio)               # Instantiate IncomingFlow class to manage incoming call flow and passing twilio object as reference
popup = dialer.PopupDialer()                  # Instantiate PopupDialer class to represent popup dialer attributes
LoginHandler = dialer.Login()  # Instantiate CredentialHandler class to manage credentials
LogOutHandler=dialer.Logout()
###########################################################################################################################
phone_pattern = re.compile(r"^[\d\+\-\(\) ]+$")
# Store the most recently created identity in memory for routing calls
IDENTITY = {"identity": "FirstAgent","identity1": "SecondAgent"}
## Golbal Variables definition
ngrok_link=''

################################# Inilizing Various Data Extractors ##################################
ClientDataExtractor=cdo.ClientDataExtractor()
IncomingClientDataExtractor = cdo.IncomingClientDataExtractor()
OutgoingClientDataExtractor = cdo.OutgoingClientDataExtractor()
AirtableOperationHandler=cdo.OperationOnAirtable()

#############################Log Handler################################
log=gof.setLogs("Call.logs")
################################# Endpoints Definitions  ################################                               ##

@app.route("/sms",methods=["GET"])
def test():
    """
    Endpoint to render the SMS interface.

    Returns:
        HTML template for the SMS interface with dealer name, number, and identifier.
    """
    return render_template("sms_interface.html" , name_=popup.name,number=popup.number,identifier="popup-sms")


@app.route("/dialer-popup",methods=["GET"])
def dialer_popup():
    """
    Endpoint to render the dialer popup interface.

    Returns:
        HTML template for the dialer popup interface with dealer name, number, and identifier.
    """
    return render_template("dialer_interface.html",name_=popup.name,number=popup.number,identifier="popup-call")
#################################################Airtable extension embedded call#######################################
@app.route("/dialer",methods=["GET"])
def dialer_():
    """
    Endpoint to render the dialer interface.

    Returns:
        HTML template for the dialer interface with agent's dealer name, number, and identifier.
    """
    return render_template("dialer_interface.html",name_=Agent.dealer_name,
                           number=Agent.dealer_number,identifier="EmbeddCall")

################################################END######################################################
@app.route("/call",methods=["POST"])
def index():
    """
    Endpoint to Config the Agents to attend Incoming or OutBound Calls.

    Parameters:
        dealer_name (str): Name of the dealer.
        dealer_number (str): Phone number of the dealer in E.164 format.

    Returns:
        - If dealer_number is "+11234567890", returns JSON response containing 
          incoming caller details from the database.
        - Otherwise, returns JSON response containing dealer_number and dealer_name.

    If the request carries a number starting with "+11234567890", it indicates a caller 
    in the queue that the agent will connect with. The endpoint handles data extraction 
    for the incoming caller if it exists in the database.
    """
    ## reset all agent attribute for next details
    Agent.recording_link=''
    Agent.call_log_sid=''
    Agent.call_status="ongoing"
    Agent.dealer_number = gof.phone_number_formatter(request.args.get('dealer_number'))                  ##-------------get the phone number and format to E.164 format
    Agent.dealer_name=request.args.get('dealer_name')                                             ##-------------get the dealer name from the POST request
  
   
    if Agent.dealer_number=="+11234567890":
        # Get the first key-value pair
        caller_sid, incoming_metadata = next(iter(Incoming.incoming_caller_details.items()))
        # dealer_number=incoming_metadata["callerNumber"]
        incoming_metadata=IncomingClientDataExtractor.get_airtable_data_for_incoming_caller(incoming_metadata,Agent)
    
        log.info("Incoming Caller Details: %s", incoming_metadata)
        return jsonify(incoming_metadata)


    log.info(f"Dealer Number: {Agent.dealer_number}, Dealer Name: {Agent.dealer_name}")
    return {"dealer_number":Agent.dealer_number,"dealer_name":Agent.dealer_name}



@app.route("/pop-call-sms",methods=["POST","GET"])
def pop_index():
    global ngrok_link
    """
    Endpoint to Config the Agent to attend for calls or SMS in PopUp Mode.

    Parameters:
        dealer_name (str): Name of the dealer.
        dealer_number (str): Phone number of the dealer in E.164 format.
        channel_type (str): Type of communication channel (e.g., call, SMS).

    Returns:
        Renders a template for displaying a "redirect" window that will redirect the user to the specified PopUp Window.
    """
    popup.number = gof.phone_number_formatter(request.args.get('dealer_number'))                  ##-------------get the phone number and format to E.164 format
    popup.name=request.args.get('dealer_name')                                             ##-------------get the dealer name from the POST request
    popup.channel_type=request.args.get('channel_type')
    log.info(f"Dealer Number: {popup.name}, Dealer Name: {popup.number} , Channel Type: {popup.channel_type}")
    return render_template("redirect_popup.html",channel_type=popup.channel_type)



@app.route("/fetch-OutBound-Dealer-AirData", methods=["POST", "GET"])
def get_Outbound_Dealer_data():
    """
    Endpoint to fetch outbound dealer data from the Airtable database.

    Parameters (JSON Payload):
        RecordID (str): Unique ID of the buyer or client in the Airtable database.
        ContactSpecific (bool): Flag indicating if the data is contact-specific.
        BuyerSpecific (bool): Flag indicating if the data is buyer-specific.
        CurrentVehicle (str): Details of the current vehicle of interest.

    Returns:
        JSON response containing the fetched data.

    This endpoint is used to extract data such as recommendations, leads, or other contact information 
    for outbound clients from the Airtable database.The endpoint invokes a class method 
    on Object "OutgoingClientDataExtractor" and then performs various methods to retrieve data from the Airtable database.
    """
    try:
        RecordID = request.json.get("RecordID")
        contactOnly = request.json.get("ContactSpecific")
        BuyerSpecific = request.json.get("BuyerSpecific")
        CurrentVehicle = request.json.get("CurrentVehicle")
        # Log request details
        log.info(f"Fetching outbound dealer data for RecordID: {RecordID}, Contact Specific: {contactOnly}, Buyer Specific: {BuyerSpecific}")
        # Fetch data from Airtable
        data = OutgoingClientDataExtractor.get_airtable_data_for_outgoing_caller(RecordID, CurrentVehicle, contactOnly, BuyerSpecific)
    except Exception as e:
        # Log warning if an exception occurs
        log.warning(f"Failed to fetch outbound dealer data: {e}")
        # Ensure that data is defined even in case of an error
        data = {}

    # Return fetched data
    return jsonify(data)


# Define a global variable to store the cached token and its expiration time
cached_token = None
token_expiry = None
# caching token
@app.route("/token", methods=["POST"])
def token():
    """
    Generates a token for authentication.These tokens grant temporary access to Twilio services on behalf of a user or client application, 
    allowing Us to interact securely with Twilio APIs.


    :return: A JSON object containing the identity and token.
    :rtype: dict
    """
    identity=IDENTITY["identity"]
    log.info(f"token generation {Agent.dealer_name} {Agent.dealer_number}")
    try:
        identity=IDENTITY["identity"] 
        now=datetime.now().timestamp()
        nbf_=now-5000
        token = AccessToken(Twilio.account_sid, Twilio.api_key, Twilio.api_secret, identity=identity,nbf=nbf_,ttl=10800)
        
        voice_grant = VoiceGrant(
            outgoing_application_sid=Twilio.twiml_application_sid,

        )
        log.info(datetime.now())
        token.add_grant(voice_grant)
        
        token = token.to_jwt()

        log.info("New token generated.")
        return jsonify(identity=identity, token=token)

    except Exception as e:
        log.error(f"Error initializing token: {e}")
        return jsonify(error=str(e))
    

@app.route("/lobby",methods=["POST","GET"])
def lobby_page():
    """
    Endpoint to render a Idle Page

    Returns:
        Renders a static html file "lobby.html".
    
    """
    return app.send_static_file("static_html/lobby.html")

@app.route("/message", methods=["POST"])
def SMS():
    """
    Endpoint to send an SMS message using Twilio.

    Parameters (JSON Payload):
        message (str): Body of the SMS message to be sent.
        To (str): Phone number of the recipient in E.164 format.

    Returns:
        If the message is successfully sent:
            JSON response indicating success along with the message SID.
        If sending the message fails:
            JSON response indicating failure along with the error message.
    """
    try:
        # Extract data from JSON request body
        data = request.get_json()
        message_body = data.get("message")  
        to_client = data.get("To")
        
        # Send SMS using Twilio
        message = Twilio.client.messages.create(
                        body=message_body,
                        from_=Twilio.PhoneNumber,
                        to=to_client
                    )
        print("Message SID:", message.sid)
        return jsonify({"Status": "Message Sent", "sid": message.sid}), 200
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"Status": "Failed", "Error": str(e)}), 400
##=======================================Incoming Caller Endpoints (require refactoring)===================================================

# ########### Endpoint Called by twilio serverless function to identify the situation of the server 
@app.route("/incoming-assigned",methods=["POST","GET"])
def incoming_assingned():
    """
    An Endpoint called by twilio serverless function to verify the condition or status of the server and Intensity of Caller in Queue at Present
    """
    log.info("Endpoint called by serverless twilio function")
    return jsonify({"NumIncomingHandle":len(Incoming.incoming_caller_details),"isUserLogged":Agent.isAvailable})

######################## Endpoints to handle Incoming Calls ##########################################################
@app.route("/check-queue-for-incoming",methods=["POST","GET"])
def check_queue_for_incoming():
    """
    An Endpoint that is used to check the presence of the Caller or Incoming Calls by verifying the Queue length.
    Execution : 
               Calls a method on the Incoming Object to handle the Incoming Presence

    Returns :
            return a json response along with jsonified data containing parameters such as queue_size or caller details
    """
    try:
        queue_sid="QU3ee6c979823c257d9efefebdfa1c5968"
        data=Incoming.check_incoming_presence(queue_sid)
        return jsonify(data)
    except Exception as e:
       
        log.warn(f"Error checking the queue status for queue sid {queue_sid}")
        return jsonify({"status":"failed" , "error":e})

@app.route("/store-incoming-details",methods=["POST","GET"])
def store_incoming_caller_details():
    """
    This Endpoint allow storage of Key details related to incoming Caller for future Use.

    Parameters JSON(payloads)
    From        :   Phone number of the Caller 
    CallerState :   State from where the call has been originate
    CallSid_    :   unique id assigned by twillio to each calls
    CallerCity  :   City from where the call has been originate

    Execution :
    The Endpoint extract data from payload received and store the Data in an Incoming Dictionary.This Data will be later on used when agent connect to them.
    The Endpoint store the data into a dic attribute  "incoming_caller_details" of Incoming object. 

    Returns :
            Status = > success || Indicating the Incoming Callers Parameters are successfully stored with no errors (response 200 OK) 
                   = > failed  || Indicating the Occurence of an Error while executing the Endpoint logic to store incoming Parameters
    """
    try:
        from_       = request.json.get("From")
        callerState = request.json.get("CallerState_")
        callerSid   = request.json.get("CallSid_")
        callerCity  = request.json.get("CallerCity")

        print(from_,callerState,callerSid,callerCity)

        response_data = {"callerNumber": from_, "callerState": callerState, "callerCity": callerCity  }
        
        Incoming.incoming_caller_details[callerSid]=response_data
        log.info(Incoming.incoming_caller_details)
        return jsonify({"Status":"success"})
    except Exception as e:
        log.info(e)
        return jsonify({"Status":"failed"})
    
@app.route("/refresh-queue", methods=["POST", "GET"])
def refresh_queue():
    # Create a new dictionary with only the items that satisfy the condition
    """
    This Endpoint allow the refreshing or updating the queued data in "incoming_caller_details" to ensure its Caller Validity in queue.

    Execution : 
              The Endpoint Invoke a method on the Incoming Object named "refresh_queue_line".This method is used to handle scenerio when: 
              When a caller leave the queue without ever connnecting with Agent.This is done to make sure that our incoming callers data stored in
              "incoming_caller_details" are up-to-date with queue lines and only store the data of callers which are in queue.

    """
    Incoming.refresh_queue_line()
    log.info(f"removed incoming call detials from server(refresh queue) after completed call===================>{Incoming.incoming_caller_details}")
    return jsonify({"message": "success"})

#######################################################################################################################################################
##########################################################################################################################################################

@app.route("/voice", methods=["POST","GET"])
def voice():
    """
    The Endpoint is invoked by the twilio Webhook originated from dedicated twiml Application which is triggerd whenever call is to be connected

    Parameter(s) (Payload) :
                To (str) :  Phone number or unique incoming identifier to whom the agent is going to be connected 
    """
    to = request.form.get("To")

    log.info("=====================================Connecting Agent with Calls both Outbound And Inbound caller in queue==================================")
    resp = VoiceResponse()

    if to == "+11234567890":       ## incoming identifier 
        dial=Dial(record='record-from-answer')
        dial.queue("Queue1")
        resp.append(dial)   
        log.info("Connecting incoming to Agent")

    elif to:
        # Placing an outbound call from the Twilio client
        dial = Dial(caller_id=Twilio.PhoneNumber,record='record-from-answer')
        log.info("initiated call to client")
        if phone_pattern.match(to):
            dial.number(to)
        else:
            dial.client(to)
        resp.append(dial)
    else:
        resp.say("Thanks for calling!")

    return Response(str(resp), mimetype="text/xml")


############################ Endpoints to Handle disconnection of call####################################################
 

@app.route("/Check-Call-State",methods=["POST","GET"])
def call_state():
    """
    This endpoint allow to update the Call Status : Ongoing => Disconnected.
    The Endpoint play a major role in alert the frontend that the call has been Disconnected.

    Receving Payload from two site:

    Twilio Device Json(Payload) :
                           origin  : Indicate the origin of the request 
                           CallSid : The unique identifier for call 
                           status  : Indicate the call status (ongoing or disconnected) 

    Airtable Dialer Extension Json(Payload) :
                           call_type : Provide additional info about call direction (inbound or outbound)

    Execution: 
            Once the call is connected using Twilio Device the frontened will send request to know the status of call until it is disconnected.
            call_type will be used to correctly fetch the accurate call recording data from twilio log database based on the provided call sid.
            Once the recording data is fetched,it is then forwarded for formatting by invoking a function named "get_recording_url" from goc.

    Return : 
        return a jsonified response containing the data that includs recording url , call status
    """
    try:
        origin=request.json.get("origin")         ## this will indicate that our device has been disconnected meaning call has been cut or hangup
        status=request.json.get("status")
        Call_Direction=request.json.get("call_type")

        if origin=="TwilioDevice":
            Agent.call_log_sid=request.json.get("CallSid")   ## get the call sid for the outbound call    
        if status:
            Agent.call_status=status
        
      
        log.info(f"==================================Call SID  {Agent.call_log_sid}================================================")
        # if status and dealer_number:
        if Call_Direction=="Outgoing":
            log.info(f"outgoing call {Agent.call_log_sid}")
            if Agent.call_log_sid:
                recording = Twilio.client.recordings.list(call_sid=Agent.call_log_sid)[0].fetch()
                Agent.recording_link=gof.get_recording_url(recording)

        elif Call_Direction=='Incoming':
            Agent.call_log_sid, _ = next(iter(Incoming.incoming_caller_details.items()))
            log.info(f"incoming call {Agent.call_log_sid}")
            if Agent.call_log_sid:
                recording = Twilio.client.recordings.list(call_sid=Agent.call_log_sid)[0].fetch()
                Agent.recording_link=gof.get_recording_url(recording)
        log.info(f"recording url====================================>{Agent.recording_link}")
        return jsonify({"status":Agent.call_status,"recording_link":Agent.recording_link})

    except Exception as e:
       
        log.warn(f"warning call fallback url: ============================>{e}")
        return jsonify({"status":Agent.call_status,"recording_link":''})

############################### View more option Endpoints #######################################3

@app.route("/get-contacts-for-buyer",methods=["POST","GET"])
def view_contacts_for_buyer():
    """
    This Endpoint allow the frontend User to access all contacts for the provided Buyer

    Parameter(s) :
        BuyerID : a unique id provided by User to uniquely identify the Buyer rows in the airtable
    
    Execution : 
        Invoke a method on Extractor Object "ClientDataExtractor" to get the contacts for the requested Buyer

    Return : 
        if success : 
        return a jsonified data containing the contact details for the requested Buyer
        if failed  :
        return a empty jsonified data
        
    """
    try:
        buyerId=request.json.get("BuyerID")
        Contact_MetaData=ClientDataExtractor.get_Contacts_for_Buyer(buyerId)
        return jsonify(Contact_MetaData)##Contact_MetaData
    except Exception as e:
        log.warning(f"warning getting contacts for buyer: ==================>{e}")
        return jsonify({})

@app.route("/get-more-recommendation", methods=["POST","GET"])    
def fetch_view_more_recomendation():
    """
    This Endpoint allow the frontend User to access 3 Recommendated Vehicles per reuqest for the provided Buyer
    
    Parameter(s) :
        leadids : a list of unique id provided by User to uniquely identify corresponding Vehicles rows in the airtable
    
    Execution : 
        Invoke a method on Extractor Object "ClientDataExtractor" to get the vehicles details for the requested vehicles.During the process the provided
        lead ids are subsequently converted to reflect the vehicles they are using.

    Return : 
        if success : 
        return a jsonified data containing the vehicle details for the request vehicles in leadids
        if failed  :
        return a empty jsonified data

    """
    leadids=request.json.get("leadids")
    log.info(f"lead id for new recommendation are================>{leadids}")
    Recommendation= ClientDataExtractor.get_associated_vehicles_details(leadids)
    log.info(f"new recommendation:===========================>{Recommendation}")
    return jsonify(Recommendation)

################################################################################################################


@app.route("/arrange-lead-based-score",methods=["POST","GET"])
def arrange_lead_based_score():
    leadids=request.json.get("leadids")
    """
    This endpoint is used to arrange the lead based on their score. Hot >> Warm >> Cold

    Parameter(s) :
        leadids : a list of unique id provided by User to uniquely identify corresponding Vehicles rows in the airtable
    
    Execution : 
        Invoke a method on AirtableOperationHandler Object to sort the lead based on their score

    Return : 
        if success : 
        return a jsonified data containing the sorted lead ids
        if failed  :
        return a same leadids list as jsonified data
    
    """
    try:
        leadids=AirtableOperationHandler.sort_leads(leadids)
        # Buyer_MetaData['Lead_ID']=leadids
    except Exception as e:
        log.warning(f"warning arranging leads based on score:============================>{e}")
    return jsonify(leadids)
        

@app.route("/set-interaction-status",methods=["POST","GET"])
def setInteractionStatus():
    """
    This Endpoint allow to append the record of the recent interaction into the "Interaction" Airtable Table

    Parameter(s) Json(Payload) : 
        Type : type of interaction i.e Phone Call or SMS or Email
        Date : date of the interaction
        BuyerID : a unique id provided by User to uniquely identify the Buyer rows in the airtable
        ContactID : a unique id provided by User to uniquely identify the Contact rows in the airtable
        LeadID : list of unique id provided by User that uniquely identify the Lead rows in the airtable (Associate leads with which User Interacted)
        VehicleID : list of  unique id provided by User that uniquely identify the Vehicle rows in the airtable (Vehicle recommendated on Call or SMS)
        recording : url of the recording for call 
        Notes : notes taken by the user while interacting with the Buyer

    Execution : 
        Invoke a method  "append_interaction_record" on AirtableOperationHandler to append the interaction record

    Return : 
        if success : 
        return a json data containing the status of success
        if failed  :
        return a json data indicating error and failed status

    """
    try:
        type_      =  request.json.get("Type")
        date       =  request.json.get("Date")
        buyerid    =  request.json.get("BuyerID")
        contactid  =  request.json.get("ContactID")
        leadids   =  request.json.get("LeadID")
        vehicleids  =  request.json.get("VehicleID")
        recording  =  request.json.get("recording")
        notes      =  request.json.get("Notes")
        log.info("======================================Call Overview=========================================================")
        log.info(f"Type of interaction used {type_} || On Date {date} || Called (BuyerID) {buyerid} or Contact (ContactID) {contactid} || Associated recommednation made(LeadID(s)) {leadids} || Associated Vehicles(VehicleID) {vehicleids} || Call Recording(url) {recording} || Notes Taken as {notes}")

        AirtableOperationHandler.append_interaction_record(type_,date,buyerid,contactid,leadids,vehicleids,recording,notes)
        return {"status":"success"}
    except Exception as e:
        log.warning(f"error updating interaction table {e}")
        return {"status":"failed","error" : str(e)}
    

@app.route("/preview-past-notes",methods=["POST","GET"])
def previewPastNotes():
    """
    This Endpoint allow to preview the notes taken by the user while interacting with the Buyer

    Parameter(s) :
        BuyerName : a primary key provided by User to uniquely identify the Buyer rows in the "Interaction" Airtable 

    Execution : 
        Invoke a method  "extract_notes" on AirtableOperationHandler to extract the past notes taken by Agent or User by matching Buyer's name in the Interaction table 

    Return : 
        return a jsonified data containing all associated past notes for given Buyer
    
    """
    try:
        BuyerName=request.json.get("BuyerName")
        log.info(f"preview past notes: {BuyerName}")
        PastNotesData=AirtableOperationHandler.extract_notes(BuyerName)
        return jsonify(PastNotesData)
    except Exception as e:
        log.warning(f"Error previewing the past notes {e}")
        return {"status":"failed","error":str(e)}


@app.route("/set-offer-amount",methods=["POST","GET"])
def setBuyerOfferAmount():
    """
    This Endpoint allow to update the offer amount field for the sepcific lead in Airtable "Leads" Airtable

    Parameter(s) :
        offer_amount : offer amount for the lead
        lead_ID : a unique key provided by User to uniquely identify the lead rows in the "Leads" Airtable that is to be updated with new Amount

    Execution : 
        Invoke a method  "update_offer_amount" on AirtableOperationHandler to update the offer amount in leads Airtable for the given leadid.The
        process essential make a api request with the given offer amount to the Airtable.

    Return : 
        if success : 
        return a json data containing the status of success
        if failed  :
        return a json data indicating error and failed status
    """
    try:
        offer_amount=request.json.get("offer_amount")
        lead_ID=request.json.get("lead_ID")
        log.info(f"==============lead ID:{lead_ID} and offer amount:{offer_amount}======================")
        AirtableOperationHandler.update_offer_amount(lead_ID,offer_amount)
        return jsonify({"status":"success"})
    except Exception as e:
        log.warning(f"error setting offer amount {e}")
        return jsonify({"status":"failed","error":str(e)})
    

@app.route("/set-progress-status",methods=["POST","GET"])
def setProgressStatus():
    """
    This Endpoint allow to update the progress status field for the sepcific lead in Airtable "Leads" Airtable
    
    Parameter(s) : 
        progress : new progress status for the lead
        lead_ID : a unique key provided by User to uniquely identify the lead rows in the "Leads" Airtable that is to be updated with new progress status

    Execution : 
        Invoke a method  "update_progress_status" on AirtableOperationHandler to update the progress status in leads Airtable for the given leadid.
        This process essential make a api request with the given progress status to the Airtable.

    Return : 
        if success : 
        return a json data containing the status of success
        if failed  :
        return a json data indicating error and failed status
    """
    try:
        progress=request.json.get("progress")
        lead_ID=request.json.get("lead_ID")
        log.info(f"==============lead ID:{lead_ID} and progress status:{progress}==========================")
        AirtableOperationHandler.update_progress_status(lead_ID,progress)
        return jsonify({"status":"success"})
    except Exception as e:
        log.warning(f"error setting progress status {e}")
        return jsonify({"status":"failed","error":str(e)})
    

############################################## Agent Idle time check ##############################################
@app.route("/last-request",methods=["POST","GET"])
def before_request():
    """
    This Endpoint capture the last request send by the active user 
    """
    try:
        Agent.last_request_time = datetime.now()
    except Exception as e:
        print(e)
    # log.info(f"last request time is{last_request_time}")
    return {"status":"sucess"}

# Route to check the status of the request variable
@app.route('/confirm-user-state',methods=["POST","GET"])
def check_status():
    """
    This Endpoint ensure that the user is still active or not.If the user stays idle for 60min.The system will consider the user as Inactive and resets its associated
    attributes
    """
    if Agent.last_request_time is None or datetime.now() - Agent.last_request_time > timedelta(minutes=60):
        log.info(f"confirm user {Agent.last_request_time}")
        status = "Inactive"
        ## reset the agent attributes in idle logout
        LogOutHandler.reset_agent_attributes(Agent)
    else:
        status = "Active"
    return f"Request status: {status}"

###########################################################Agents Login/Out Logic ##########################################################

@app.route("/login", methods=["POST"])
def agent_login():
    """
    This Endpoint handle the login process of the Agent.The endpoint is called using the Frontened i.e Airtable Extension

    Parameter(s) :
        userId : user id of the Agent
        password : password of the Agent

    Execution : 
        The payload contains userId and password which is used to authenticate the Agent.Invoke a method  "verify_credentials" on CredentialHandler to verify the credentials of the Agent
        If verified,the Agent attribute is updated with login time and availability status

    return :
        if verified :
        return a json data containing the success status
        if failed  :
        return a json data indicating error and failed status
    """
    global ngrok_link
    data = request.json
    username = data.get("userId")
    password = data.get("password")
    ngrok_link = data.get("ngrok_url")
    if LoginHandler.verify_credentials(username, password):
        log.info("Successfully login Verified!")
        Agent.login_time = datetime.now()
        Agent.isAvailable=True
        return jsonify({"login_status": "success", "userID": username})
    else:
        return jsonify({"login_status": "failed"})

@app.route("/logout", methods=["POST"])
def agent_logout():
    # data = request.json
    """
    This Endpoint handle the logout process of the Agent.The Endpoint is Called throught the Frontend when user logout from Exntension.

    Parameter(s) :
        userId : user id of the Agent
        call_count : Number of calls made by the Agent when active on the Frontend

    Execution :
        The payload contains a userId which is used to identify which user is logging out.The endpoints Invoke a method on sub class of CredentialHandler
        to handle the formatting a datetime and appending it into the Google sheet(current database contains agents activity log).
        Once the User is logged out, the attribute of Agent is reset especially the login time and their Availability status

    return :
        if verified :
        return a json data containing the success status and userid
        if failed  :
        return a json data indicating error and failed status
    """
    try:
        calls_count = request.json.get("call_count")
        userid = request.json.get("userid")

        log.info(f"call counts {calls_count} for userid {userid}")
        login_time = Agent.login_time
        ## reset the agent attribute
        LogOutHandler.reset_agent_attributes(Agent)

        LogOutHandler.append_agents_activity_log(login_time,calls_count,userid,gof)

        log.info("Agent Activity Updated in google sheet")
        #################################################
        return jsonify({"logout_status": "success", "userID": userid})
    except Exception as e:
        log.warning(f"error logout: ============================>{e}",exc_info=True)
        return jsonify({f"logout_status": "failed","error":str(e)})

if __name__ == "__main__":

    app.run(debug=True,port=5000,host="0.0.0.0")


