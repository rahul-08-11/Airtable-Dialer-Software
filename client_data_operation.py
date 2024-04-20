import time
import os
from pyairtable import Api
from dotenv import load_dotenv
import general_operational_func as gof

load_dotenv()

class Airtable:
    def __init__(self):
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.api_key = os.getenv('AIRTABLE_API')
        self.api = Api(api_key=self.api_key)
        self.contact_table_id=os.getenv('CONTACT_TABLE_ID')
        self.company_table_id=os.getenv('COMPANY_TABLE_ID')
        self.lead_table_id=os.getenv('LEAD_TABLE_ID')
        self.vehicle_table_id=os.getenv('VEHICLE_TABLE_ID')
        self.interaction_table_id=os.getenv('INTERACTION_TABLE_ID')

        self.contact_table = self.api.table(self.base_id, self.contact_table_id)
        self.company_table = self.api.table(self.base_id, self.company_table_id)
        self.lead_table = self.api.table(self.base_id, self.lead_table_id)
        self.vehicle_table = self.api.table(self.base_id, self.vehicle_table_id)
        self.interaction_table = self.api.table(self.base_id, self.interaction_table_id)

class ClientDataExtractor(Airtable):  
    def __init__(self):
        super().__init__()

    def get_associated_vehicles_details(self,lead_ids):
        Recommendation={}
        for leadId in lead_ids:
            lead_record = self.lead_table.get(record_id=leadId)
            vehicle_Id = lead_record["fields"].get("Vehicle interested in")
            if vehicle_Id is not None:   
                vehicle_score = lead_record["fields"].get("Lead Score")
                progress_status = lead_record["fields"].get("Progress Status")
                vehicle_record = self.vehicle_table.get(record_id=vehicle_Id[0])
                vehicle_name = vehicle_record["fields"].get("Vehicle")
                # Create a new dictionary for each vehicle recommendation

                vehicle_metadata = {
                    "vehicle_name": vehicle_name,
                    "leadId": leadId,
                    "score": vehicle_score,
                    'make': vehicle_record["fields"].get("Make"),
                    "year": vehicle_record["fields"].get("Year"),
                    "trim": vehicle_record["fields"].get("Trim"),
                    "mileage": vehicle_record["fields"].get("Mileage"),
                    "source": vehicle_record["fields"].get("Source"),
                    "price": vehicle_record["fields"].get("Price"),
                    "model": vehicle_record["fields"].get("Model"),
                    "VIN": vehicle_record["fields"].get("VIN"),
                    "vehicle_Id":vehicle_Id[0],
                    "Progressstatus": progress_status

                }
                ## logic will be changed when refactored
            Recommendation[leadId]=vehicle_metadata
        return Recommendation


    def get_recommendation_for_dealer(self,Buyer_MetaData,CurrentVehicle):
        s=time.time()
        print("=====================================getting recommendation for dealer===================================================")
        print(f"current vehicle {CurrentVehicle}")
        lead_ids=Buyer_MetaData['Lead_ID']
        # print("lead ids========================>",lead_ids)
        buyer_name=Buyer_MetaData['buyer_name'].split(":")[0].strip()
        Recommendation={}
        # print(buyer_name)

        try:
            
            record=self.lead_table.all(formula=f"AND(Buyer = '{buyer_name}', Name = '{CurrentVehicle}')")        # print(record)
            current_vehicle_lead_id=record[0]['id']
            print("current vehicle lead id========================>",current_vehicle_lead_id)
            Recommendation=self.get_associated_vehicles_details([current_vehicle_lead_id])
            print("lead id in totaal are =======================>",len(lead_ids),lead_ids)
            lead_ids=lead_ids.remove(current_vehicle_lead_id)
            print("lead id after removing current vehicle are =======================>",len(lead_ids),lead_ids)
            Buyer_MetaData['Lead_ID']=lead_ids

        except Exception as e:
            print(f"warning getting recommendation for dealer:=========================>{e}")
        print(f"Recommendation time==================>{time.time()-s}") 
        return Recommendation

    def get_client_data_for_dealer(self,client_ids,Buyer_MetaData):
        print("==========================get client details=========================================")
        print(f"client Ids==================>{client_ids}")
        try:
            recordid = client_ids[0]
            Buyer_MetaData['clients_id']=recordid
            record = self.contact_table.get(record_id=recordid)
            Buyer_MetaData['buyer_name'] = Buyer_MetaData['buyer_name'] + " : " + record['fields'].get("Name")
            contact_number=record["fields"].get("Phone")
            Buyer_MetaData["contact_number"] = gof.phone_number_formatter(contact_number) if contact_number is not None else None
        except Exception as e:
            print(e)
            print(f"warning getting client data for dealer:====================================>{e}")
        return Buyer_MetaData

    def get_Buyers_data_for_dealer(self,buyerId,Buyer_MetaData,ClientOnly):
        print("==========================get buyer details=========================================")
        print(f"Buyerid===================>{buyerId}")
            #==================================================================
        # Buyer Details extraction
        s=time.time()

        try:
            print("getting company records")
            record = self.company_table.get(record_id=buyerId)
            print("company record", record)
            Buyer_MetaData["buyer_name"] = record['fields'].get("Name")
            buyer_number =record["fields"].get("Dealer Phone")
            buyer_number= gof.phone_number_formatter(buyer_number) if buyer_number is not None else None
            Buyer_MetaData["buyer_avg_price"] = record["fields"].get("Average Purchase Price")
            Buyer_MetaData["buyer_address"] = record["fields"].get("Address")
            Buyer_MetaData["Lead_ID"] = record["fields"].get("Recommendations")
            Buyer_MetaData["buyer_category"] = record["fields"].get("Category")

            if buyer_number is not None:
                print("no dealer number")
                Buyer_MetaData["contact_number"] = buyer_number
            else:
                if not ClientOnly:
                    print("it is not a client only,getting first contact number ")
                    client_ids = record['fields'].get("Contacts")[0]
                    print("client ids ====================================================>",client_ids)
                    Buyer_MetaData['clients_id']=client_ids
                    contact=self.contact_table.get(record_id=client_ids)
                    Buyer_MetaData['buyer_name'] = Buyer_MetaData['buyer_name'] + " : " + contact['fields'].get("Name")
                    Buyer_MetaData["contact_number"]=gof.phone_number_formatter(contact["fields"].get("Phone"))
                    print("buyer client number is=============================> ",Buyer_MetaData["contact_number"])
            e=time.time()
            print("time took by get buyer details function is ",e-s)
        except Exception as e:
            print(f"warning : getting buyer data for dealer {e}")
        return Buyer_MetaData

    def get_dealer_data(self,ID,CurrentVehicle=None,ClientOnly=False,BuyerOnly=False):
        start=time.time()
        #### this function take 3 different id i.e leadID ,CLientID or BuyrID.WHich id is which is define by other two argument ClietnOnly ==>ClientID and BuyerID==BuyerID
        # buyerId = ''
        clients_ids=''
        Buyer_MetaData = {
            "buyer_id": '',
            "buyer_name": '',
            "contact_number": '',
            "buyer_avg_price": '',
            "buyer_address": '',
            "buyer_category": '',
            'clients_id': '',
            "Lead_ID": ''
        }

        if ClientOnly:
            print("================Its is a client Id===============================")
            clients_ids=[ID]
            contact_record = self.contact_table.get(record_id=ID)
            buyer_id=contact_record['fields'].get("Company")[0]
            Buyer_MetaData['buyer_id']=buyer_id
            Buyer_MetaData=self.get_Buyers_data_for_dealer(buyer_id,Buyer_MetaData,ClientOnly)
            Buyer_MetaData=self.get_client_data_for_dealer(clients_ids,Buyer_MetaData)
            Recommendation=self.get_recommendation_for_dealer(Buyer_MetaData,CurrentVehicle)

        elif BuyerOnly:
            print("=================Its is a Buyer Id only===============================")
            Buyer_MetaData["buyer_id"]=ID
            Buyer_MetaData=self.get_Buyers_data_for_dealer(ID,Buyer_MetaData,ClientOnly)
            Recommendation=self.get_recommendation_for_dealer(Buyer_MetaData,CurrentVehicle)

        else:
            print("==================Its is a Lead Id========================================")
            s=time.time()
            #api = Api('patBYsz67hEBv1UQI.0709abfe05c883158b5e3bd9474708e1c103a171a96583b033dcd90f3a266718')
            #lead_table = api.table('appNyT6Qt9d1AsBeu','tbl644gquZMYmhww2')
            print(f"record id {ID}")
            lead_record = self.lead_table.get(record_id=ID)
            Buyer_MetaData['buyer_id'] = lead_record['fields'].get("Buyer")[0]
            print(f"buyer meta data : {Buyer_MetaData}")
            Buyer_MetaData=self.get_Buyers_data_for_dealer(Buyer_MetaData['buyer_id'],Buyer_MetaData,ClientOnly)
            print("getting recommmendation")
            Recommendation=self.get_recommendation_for_dealer(Buyer_MetaData,CurrentVehicle)
            e=time.time()
            print("time it took it is lead id ======================================",e-s)

        end=time.time()
        print(f"time it took ======================================{start-end}")
        # print(Buyer_MetaData)
        # print(Recommendation)
        return {
            "Status": "success",
            "BuyerMetaData": Buyer_MetaData,
            "Recommendation": Recommendation
        }
    
    def get_Contacts_for_Buyer(self,buyer_id):
        try:
            Contact_MetaData={}
            buyer_record=self.company_table.get(record_id=buyer_id)
            contacts_ids=buyer_record['fields'].get('Contacts')
            for contact_id in contacts_ids:
                contact_record=self.contact_table.get(record_id=contact_id)
                name=contact_record['fields'].get('Name')
                phone_number=contact_record['fields'].get('Phone')
                contact_title=contact_record['fields'].get('Title')
                Contact_MetaData[contact_id]={"name":name,"phone_number":phone_number,"contact_title":contact_title,"BuyerID":buyer_id}
            print(Contact_MetaData)
            return Contact_MetaData
        except Exception as e:
            print(f"warning : getting buyer data for dealer {e}")
            return {}
    

class IncomingClientDataExtractor(ClientDataExtractor):
    def __init__(self):
        
        super().__init__()

    def get_airtable_data_for_incoming_caller(self,Incoming_MetaData,Agent):
        caller_number=Incoming_MetaData["callerNumber"]
        caller_city=Incoming_MetaData["callerCity"]
        caller_state=Incoming_MetaData["callerState"]

        try:
            records = self.company_table.all(formula=f"{{Dealer Phone}}='{caller_number}'")
            if records:
                first_record = records[0]  # Access the first record in the list
                buyerID = first_record['id']
                print("buyer Id",buyerID)
                Agent.Dealer_Name=first_record['fields'].get("Name")
            
                data=self.get_dealer_data(buyerID,BuyerOnly=True)
                print(data)
                print("got airtable data from incoming caller",)
                return data
            else:
                return {"message": "No Record Found In DataBase","caller_number":caller_number,"caller_city":caller_city,"caller_state":caller_state}
        except Exception as e:
            print(f"Something Went Wrong : function Name :get_airtable_data_for_incoming_caller============================>{e}")
            return {"message": f"Something Went Wrong{e}","caller_number":caller_number,"caller_city":caller_city,"caller_state":caller_state}
        


    
class OutgoingClientDataExtractor(ClientDataExtractor):
    def __init__(self):
        super().__init__()


    def get_airtable_data_for_outgoing_caller(self,RecordID,CurrentVehicle,contactOnly,BuyerSpecific):
        data=self.get_dealer_data(RecordID,CurrentVehicle,contactOnly,BuyerSpecific)
        return data
    


class OperationOnAirtable(Airtable):
    def __init__(self):
        super().__init__()

    def sort_leads(self,leadids):
        ## sorts lead based on score HOT >> WARM >> COLD
        lead_groups = {'Hot': [], 'Warm': [], 'Cold': []}
        for lead in leadids:
            record = self.lead_table.get(record_id=lead)
            score = record['fields'].get("Lead Score")
            lead_groups[score].append(lead)

        leadids = lead_groups['Hot'] + lead_groups['Warm'] + lead_groups['Cold']
        return leadids
        
  
    def update_offer_amount(self,lead_ID,offer_amount):
        offer_amount_=offer_amount[lead_ID]
        if offer_amount_:
            offer_amount=int(offer_amount_)
            self.lead_table.update(lead_ID,{"Offer Amount":offer_amount})


    def update_progress_status(self,lead_ID,progress_status):
        if progress_status:
            self.lead_table.update(lead_ID,{"Progress Status":progress_status})



    def extract_notes(self,BuyerName):
        PastNotesData={}
        record =self.interaction_table.all(formula=f"AND(Company='{BuyerName}')")
        for record in record:
            createtime=record['fields'].get("Date and time")
            note=record['fields'].get("Notes")
            PastNotesData[createtime]=note
        return PastNotesData
    

    def append_interaction_record(self,type_,date,BuyerID,ContactID,LeadID,VehicleID,recording,notes):
        if not ContactID: ## review the contactid logic for incoming calls
            ContactID=[]
        else:
            ContactID=[ContactID]
        
        data ={
            "Type": str(type_),
            "Date and time": date,
            "Company": [BuyerID], 
            "Contact": ContactID,
            "Notes":notes,
            "Lead": LeadID,  
            "Vehicle(s)": VehicleID,  
            "Recording": recording
        }
        self.interaction_table.create(data)
        
        