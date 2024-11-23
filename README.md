# Airtable-Dialer-Software ![alt text](https://img.shields.io/badge/Flask-v0.3.0-0000)  ![alt text](https://img.shields.io/badge/Airtable-v1.8.0-FF4154) ![alt text](https://img.shields.io/badge/JavaScript-v18.13.0-F7DF1E) 


Welcome to the Backend repository for the Dialer Project!<br>
This repoisotry consist of backend implementation for the [Airtable Dialer Extension](https://github.com/rahul-08-11/Airtable-Dialer-Extension) along with popup-integration.

## Introduction
 The server code is responsible for handling API requests from the frontend, managing user authentication, and interacting with the Airtable API to fetch and update lead data. It serves as the backend infrastructure powering the dialer extension's functionalities.The server code is implemented in python, utilizing the flask framework for routing and middleware management. 

## Key Features


- **API Endpoint Handling**:  The backend server exposes a set of endpoints to handle API requests from the frontend application. These endpoints facilitate operations such as fetching lead data, updating client information, managing user authentication, and handling other system functionalities. By defining clear API endpoints, the frontend can communicate effectively with the backend to perform various tasks.<br>

- **User Authentication**: User authentication is implemented to ensure secure access to the backend resources. Only registered users with valid credentials can access the system functionalities.<br>

- **Airtable Integration**: The backend server integrates with the Airtable API to seamlessly fetch and update lead data stored in the Airtable database. This integration allows the system to retrieve client information, such as contact details, leads or recommendation, and interaction or notes, directly from the Airtable database. It enables real-time synchronization of data between the frontend application and the Airtable database, this allow agent to update airtable database through the UI itself.

- **Error Handling**: Robust error handling mechanisms are implemented to handle unexpected errors and provide meaningful responses to API requests.<br>
 
- **Popup Integration**: The backend is responsible for managing requests for popups from the Airtable. The popup dialer is called whenever the user or agent clicks on the associated button. The request is received, and the backend responds with the dynamic webpage necessary to set calls or send SMS.<br>

- **Call/SMS Integration** :The backend server facilitates seamless integration with Twilio API to enable call and SMS functionalities within the application. This integration allows the system to initiate outbound calls, receive inbound calls, and send custom SMS messages to clients using Twilio's communication services.
  
- **Scalability** :The backend server is designed to be scalable to meet the growing demand of the application. Scalability is achieved through horizontal scaling, which involves adding more server instances or resources to handle increased workload and user traffic. <br>

- **Database Management**:The backend manages a database to store activity-related data of agents or users, such as call logs, login/logout timestamps, and other relevant metrics. This database serves as a centralized repository for storing and retrieving important information about user interactions, system events, and performance metrics. Efficient database management ensures data integrity, accessibility, and reliability, enabling seamless operation of the application.<br>


- **Incoming Calls**: The backend receives incoming caller details from the Twilio serverless function set up using Twilio Function. The backend is responsible for handling and managing incoming calls throughout the session until the caller is connected with an agent.


## Twilio Queue Handling : Serverless function


## Software Architecture Diagram
