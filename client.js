var connection = new WebSocket('wss://127.0.0.1:8765');
var name = "";


var otherUsernameInput = document.querySelector('#otherUsernameInput');
var connectToOtherUsernameBtn = document.querySelector('#connectToOtherUsernameBtn');
var connectedUser, myConnection;
//var localVideo = document.querySelector('#localVideo');
var remoteVideo = document.querySelector('#remoteVideo');
var peerList = document.querySelector('#peerList');
var callPage = document.querySelector('#callPage');
var ourIDSpan= document.querySelector('#ourID');
var yourConn;
var stream;
var connections = {}
var configuration;

function getOurId() {
    return Math.floor(Math.random() * (9000 - 10) + 10).toString();
}

//on page load
document.addEventListener('DOMContentLoaded', function () {

});

function logIn(){
  name = getOurId();//Generate a random id for the browser
  ourIDSpan.innerHTML = name;
  if(name.length > 0){
     send({
        type: "login",
        payload: {location: "browser"}
     });
  }
}


//handle messages from the server
connection.onmessage = function (message) {
   console.log("Got message", message.data);
   var data = JSON.parse(message.data);

   switch(data.type) {
      case "login":
         onLogin(data.payload);
         break;
      case "offer":
         handleOffer(data);
         break;
      case "answer":
         handleAnswer(data.answer, data.from);
         break;
      case "candidate":
         handleCandidate(data);
         break;
      case "userLoggedIn":
         handleUserLoggedIn(data.names)
      default:
         break;
   }
};

// Alias for sending messages in JSON format
function send(message) {

    message.name = name;

   connection.send(JSON.stringify(message));
};

//when a user logs in
function onLogin(payload) {
  success = payload.success;
  if (success === false) {
    console.log("Login failed with name: ", name);
    alert("oops...try a different username");
  } else {
  configuration = {
    "iceServers": [{ "url": "stun:stun.1.google.com:19302" }]
      };
   }
};

//Set up video:
      //loginPage.style.display = "none";
      //callPage.style.display = "block";

      //**********************
      //Starting a peer connection
      //**********************

      //getting local video stream
      navigator.webkitGetUserMedia({ video: true, audio: true }, function (myStream) {
         stream = myStream;

         //displaying local video stream on the page
         //localVideo.srcObject = stream;

         //using Google public stun server
         var configuration = {
            "iceServers": [{ "url": "stun:stun2.1.google.com:19302" }]
         };

      }, function (error) {
         console.log(error);
      });



/////////////////

connection.onopen = function () {
   console.log("Connected");
   //login here
   logIn()
};

connection.onerror = function (err) {
   console.log("Got error", err);
};

const handleDataChannelOpen = (event) =>{
    console.log("dataChannel.OnOpen", event);
};

const handleDataChannelMessageReceived = (event) =>{
    console.log("dataChannel.OnMessage:", event, event.data.type);

    setStatus("Received data channel message");
    if (typeof event.data === 'string' || event.data instanceof String) {
        console.log('Incoming string message: ' + event.data);
        textarea = document.getElementById("text")
        textarea.value = textarea.value + '\n' + event.data
    } else {
        console.log('Incoming data message');
    }
    send_channel.send("Hi! (from browser)");
};


const handleDataChannelError = (error) =>{
    console.log("dataChannel.OnError:", error);
};

const handleDataChannelClose = (event) =>{
    console.log("dataChannel.OnClose", event);
};

function onDataChannel(event) {
    setStatus("Data channel created");
    let receiveChannel = event.channel;
    receiveChannel.onopen = handleDataChannelOpen;
    receiveChannel.onmessage = handleDataChannelMessageReceived;
    receiveChannel.onerror = handleDataChannelError;
    receiveChannel.onclose = handleDataChannelClose;
}

//initiating a call, add camera from browser?
connectToOtherUsernameBtn.addEventListener("click", function () {
   var callToUsername = otherUsernameInput.value;

   if (callToUsername.length > 0) {
      addConnection(callToUsername)
      console.log("RTCPeerConnection object was created");
      console.log(connections[connectedUser]);
      connectedUser = callToUsername;

      // create an offer
      connections[callToUsername].createOffer(function (offer) {
         send({
            type: "offer",
            offer: offer,
            sentTo: callToUsername
         });
         //When creating an offer we always set the offer we created to our local description
         connections[callToUsername].setLocalDescription(offer);

      }, function (error) {
         alert("Error when creating an offer");
      });
   }
});

//when somebody sends us an offer
//when somebody sends us an offer we always set that offer given to us as our remote description
function handleOffer(data) {
   connectedUser = data.name;
   addConnection(connectedUser)
   console.log("RTCPeerConnection object was created");
   console.log(connections[connectedUser]);
   console.log("this is the offer: ",data.payload);
   connections[connectedUser].setRemoteDescription(new RTCSessionDescription(data.payload));

   //create an answer to an offer
   //When we create our answer to an offer we always set it to our local description
   connections[connectedUser].createAnswer(function (answer) {
      connections[connectedUser].setLocalDescription(answer);

      send({
         type: "answer",
         sentTo: connectedUser,
         payload: answer
      });

   }, function (error) {
      alert("Error when creating an answer");
   });
};

//when we got an answer from a remote user
//When getting an answer from a peer we set that answer to our remote description
function handleAnswer(answer, from) {//Have to figure out where the answer is coming from
    console.log("this is the answer: ",answer);
    connections[from].setRemoteDescription(new RTCSessionDescription(answer));
};

//when we got an ice candidate from a remote user
//Not exactly sure when we set our ice candidate
function handleCandidate(data) {
    candidate = {type:"candidate", candidate:data.candidate, sdpMLineIndex: data.sdpMLineIndex};
    console.log("this is the candidate: ",data);
    connections[data.name].addIceCandidate(new RTCIceCandidate(candidate));
};
//initiating a call block
//Update call list
function handleUserLoggedIn(names){
  peerList.value = ""
    for (i=0; i<names.length; i++){
        peerList.value = peerList.value + "\n" + names[i]
    }
}

//constraints for desktop browser
var desktopConstraints = {

   video: {
      mandatory: {
         maxWidth:800,
         maxHeight:600
      }
   },

   audio: true
};

//constraints for mobile browser
var mobileConstraints = {

   video: {
      mandatory: {
         maxWidth: 480,
         maxHeight: 320,
      }
   },

   audio: true
}

//if a user is using a mobile browser
if(/Android|iPhone|iPad/i.test(navigator.userAgent)) {
   var constraints = mobileConstraints;
} else {
   var constraints = desktopConstraints;
}


//on connection added
function addConnection(name){
  //create our element
  videoElement = document.createElement("video");
  videoElement.setAttribute("id", "video"+name);
  videoElement.setAttribute("autoplay", true);
  callPage.appendChild(videoElement);

  var connection = new webkitRTCPeerConnection(configuration);

  // setup stream listening
  //connection.addStream(stream);//my stream?

  //when a remote user adds stream to the peer connection, we display it
  connection.onaddstream = function (e) {
     videoElement.srcObject = e.stream;
  };

  // Setup ice handling
  connection.onicecandidate = function (event) {

     if (event.candidate) {
        send({type:"candidate",
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex});
        console.log("This is what our event looks like", {type:"candidate",
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex});
     }
  };
  //Add a connection dynamically
  connections[name] = connection
}
