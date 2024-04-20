$(function () {
  const speakerDevices = document.getElementById("speaker-devices");
  const ringtoneDevices = document.getElementById("ringtone-devices");
  const outputVolumeBar = document.getElementById("output-volume");
  const inputVolumeBar = document.getElementById("input-volume");
  const volumeIndicators = document.getElementById("volume-indicators");
  const callButton = document.getElementById("button-call");
  const outgoingCallHangupButton = document.getElementById("button-hangup-outgoing");
  const callControlsDiv = document.getElementById("call-controls");
  const audioSelectionDiv = document.getElementById("output-selection");
  const getAudioDevicesButton = document.getElementById("get-devices");
  // const logDiv = document.getElementById("log");
  const incomingCallDiv = document.getElementById("incoming-call");
  const muteButton = document.getElementById("button-mute");
  const getprogressnotify=document.getElementById("callbar");
  const clientname =document.getElementById("clientname");
  // dial pad numbers
  const One =document.getElementById('one')
  const Two =document.getElementById('two')
  const Three =document.getElementById('three')
  const Four =document.getElementById('four')
  const Five =document.getElementById('five')
  const Six =document.getElementById('six')
  const Seven =document.getElementById('seven')
  const Eight =document.getElementById('eight')
  const Nine =document.getElementById('nine')
  const Zero =document.getElementById('zero')
// Access data attributes here
var dataElement = document.getElementById('data');
var name_ = dataElement.getAttribute('data-name');
var number = dataElement.getAttribute('data-number');
var identifier = dataElement.getAttribute('data-identifier');


  const notifyCallState=document.getElementById("notify-call-state");
  const incomingCallHangupButton = document.getElementById(
    "button-hangup-incoming"
  );
  const incomingCallAcceptButton = document.getElementById(
    "button-accept-incoming"
  );
  const incomingCallRejectButton = document.getElementById(
    "button-reject-incoming"
  );
  // const phoneNumberInput = document.getElementById("phone-number");
  const incomingPhoneNumberEl = document.getElementById("incoming-number");
  const startupButton = document.getElementById("startup-button");

console.log("Number: " + number);
console.log("Name: " + name_);
let device;
let token;
var dealer_number=number;
var dealer_name = name_;
var callsid;
callButton.onclick = (e) => {
    e.preventDefault();
    callButton.disabled = true;
    makeOutgoingCall();
  };
  getAudioDevicesButton.onclick = getAudioDevices;
  speakerDevices.addEventListener("change", updateOutputDevice);
  ringtoneDevices.addEventListener("change", updateRingtoneDevice);
  
  // SETUP STEP 1:
  // Browser client should be started after a user gesture
  // to avoid errors in the browser console re: AudioContext
  startupButton.addEventListener("click", startupClient);

  // SETUP STEP 2: Request an Access Token
  async function startupClient() {
    // log("Requesting Access Token...")
    try {
    
      const data = await $.ajax({
        url: "/token",
        method: "POST",
        body: JSON.stringify({
   
        })
      });
      console.log("Got a token.");
      const time=new Date().toLocaleString();
      console.log(time)
      token = data.token;
     
      if (dealer_number=="+11234567890"){
        clientname.textContent = "Incoming Connected: " + dealer_name;

      }else{
        clientname.textContent = "Calling " + dealer_name;

      }
      await new Promise(resolve => setTimeout(resolve, 7000));
      console.log("intilizing")
   
      await intitializeDevice();
    } catch (err) {
      console.log(err);
      // log("An error occurred. See your browser console for more information.");
    }
  }

  // SETUP STEP 3:
  // Instantiate a new Twilio.Device
  function intitializeDevice() {
    // logDiv.classList.remove("hide");
    // log("Initializing device");
    console.log(token)
    device = new Twilio.Device(token, {
      logLevel: 1,
      // Set Opus as our preferred codec. Opus generally performs better, requiring less bandwidth and
      // providing better audio quality in restrained network conditions.
      codecPreferences: ["opus", "pcmu"]
    });
    addDeviceListeners(device);

       // Device must be registered in order to receive incoming calls
    if (device.state === 'unregistered') {
        device.register();
        console.log("Registering device...");
    } else {
        console.log("Device is already registered or in the process of registering.");
    }
  }

  // SETUP STEP 4:
  // Listen for Twilio.Device states
  function addDeviceListeners(device) {
    device.on("registered", function () {
      console.log("Twilio.Device Ready to make and receive calls!");
      callButton.click();
      callControlsDiv.classList.remove("hide");
    });

    device.on("error", function (error) {
      
      console.log("Twilio.Device Error: " + error.message);
      startupClient();
    });
    
    // device.on("incoming", handleIncomingCall);

    device.audio.on("deviceChange", updateAllAudioDevices.bind(device));

    // Show audio selection UI if it is supported by the browser.
    if (device.audio.isOutputSelectionSupported) {
      audioSelectionDiv.classList.remove("hide");
    }
  }

  // MAKE AN OUTGOING CALL
  async function makeOutgoingCall() {
    var params = {
      // get the phone number to call from the DOM
      To: dealer_number,
    };

    console.log(params)
    if (device) {
      // log(`Attempting to call ${params.To} ...`);
      if(dealer_number=="+11234567890"){
        getprogressnotify.textContent="Incoming Connected";
          }
          else{
      getprogressnotify.textContent="Calling...";
    }
     
      console.log("device object",device)
      const call = await device.connect({ params });
      console.log("call object",call)
    
   
      // add listeners to the Call
      // "accepted" means the call has finished connecting and the state is now "open
      // "disconnected" means the call has finished or cut
      // "rejected" means the call was rejected
      notifyCallState.textContent="Call Ready!";
      call.on("accept", updateUIAcceptedOutgoingCall);
      call.on("disconnect",  updateUIDisconnectedOutgoingCall); // Wrap the function call in an anonymous function
      call.on("cancel",  updateUICanceledOutgoingCall);
  
      // check key press and send digits
      One.onclick = () => { call.sendDigits("1"); }
      Two.onclick = () => { call.sendDigits("2"); }
      Three.onclick = () => { call.sendDigits("3"); }
      Four.onclick = () => { call.sendDigits("4"); }
      Five.onclick = () => { call.sendDigits("5"); }
      Six.onclick = () => { call.sendDigits("6"); }
      Seven.onclick = () => { call.sendDigits("7"); }
      Eight.onclick = () => { call.sendDigits("8"); }
      Nine.onclick = () => { call.sendDigits("9"); }
      Zero.onclick = () => { call.sendDigits("0"); }

      let isMuted = false;
      muteButton.onclick = () => {
        if (isMuted) {
            // Unmute the call
            call.mute(false);
            isMuted = false;
            muteButton.textContent = "Mute"; // Change button text to reflect the action
        } else {
            // Mute the call
            call.mute(true);
            isMuted = true;
            muteButton.textContent = "Unmute"; // Change button text to reflect the action
        }
    };

     
      await new Promise(resolve => setTimeout(resolve, 8000));
      callsid = call.parameters.CallSid;
      console.log("call sid is ",callsid)
      outgoingCallHangupButton.onclick = () => {
        // log("Hanging up ...");
        call.disconnect();
    
        getprogressnotify.textContent="Call Hanged Up";

        callButton.disabled=false;
        callButton.classList.remove('hide');
        outgoingCallHangupButton.classList.add('hide');
    }} else {
     console.log("Unable to make call.");
    }
  }

  function updateUIAcceptedOutgoingCall() {

   muteButton.classList.remove("hide");
    getprogressnotify.textContent="Call Connected";
    outgoingCallHangupButton.classList.remove("hide");
  }

  function updateUIDisconnectedOutgoingCall(call) {
    // log("Call disconnected.");
    callButton.disabled = false;
    getprogressnotify.textContent="Disconnected";
    outgoingCallHangupButton.classList.add("hide");
    muteButton.classList.add("hide");
    callButton.classList.remove('hide');
  console.log("call sid is ",callsid)
   // volumeIndicators.classList.add("hide");
  if(identifier!="popup-call"){
    fetch("/Check-Call-State", {
      method: "POST",
      body: JSON.stringify({
        status:"Disconnected",
        CallSid:callsid,
        origin:"TwilioDevice",
        dealer_number:dealer_number
      }),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    });
  }
  }
  function updateUICanceledOutgoingCall() {
    // log("Call disconnected.");
    callButton.disabled = false;
    getprogressnotify.textContent="Disconnected";
    outgoingCallHangupButton.classList.add("hide");
    callButton.classList.remove('hide');
    console.log("call sid is ",callsid)
    if (identifier != "popup-call") {
    fetch("/Check-Call-State", {
      method: "POST",
      body: JSON.stringify({
        status:"Disconnected",
        CallSid:callsid,
        origin:"TwilioDevice",
        dealer_number:dealer_number
      }),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    });
  }
  }
  
  // AUDIO CONTROLS

  async function getAudioDevices() {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    updateAllAudioDevices.bind(device);
  }

  function updateAllAudioDevices() {
    if (device) {
      updateDevices(speakerDevices, device.audio.speakerDevices.get());
      updateDevices(ringtoneDevices, device.audio.ringtoneDevices.get());
    }
  }

  function updateOutputDevice() {
    const selectedDevices = Array.from(speakerDevices.children)
      .filter((node) => node.selected)
      .map((node) => node.getAttribute("data-id"));

    device.audio.speakerDevices.set(selectedDevices);
  }

  function updateRingtoneDevice() {
    const selectedDevices = Array.from(ringtoneDevices.children)
      .filter((node) => node.selected)
      .map((node) => node.getAttribute("data-id"));

    device.audio.ringtoneDevices.set(selectedDevices);
  }

  // Update the available ringtone and speaker devices
  function updateDevices(selectEl, selectedDevices) {
    selectEl.innerHTML = "";

    device.audio.availableOutputDevices.forEach(function (device, id) {
      var isActive = selectedDevices.size === 0 && id === "default";
      selectedDevices.forEach(function (device) {
        if (device.deviceId === id) {
          isActive = true;
        }
      });

      var option = document.createElement("option");
      option.label = device.label;
      option.setAttribute("data-id", id);
      if (isActive) {
        option.setAttribute("selected", "selected");
      }
      selectEl.appendChild(option);
    });
  }
});
