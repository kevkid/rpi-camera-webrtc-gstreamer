//var connection = new WebSocket('wss://192.168.11.148:8765');
var connection = new WebSocket(wsserver);
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
var name
function getOurId() {
    return Math.floor(Math.random() * (9000 - 10) + 10).toString();
}

//on page load
document.addEventListener('DOMContentLoaded', function () {
  /*When the page loads, we get a name and we send this to the
  *http server. The http server will launch a client with this id
  */
  name = getOurId()
  server_addr = 'https://'+httpsserver+'/get_browser_id'//This has to be fixed
  data = {'browser_id': name};//servers address

  $.ajax({
     type: "POST",
     url: server_addr,
     data: JSON.stringify(data, null, '\t'),
     contentType: 'application/json;charset=UTF-8',
     success: null,
   }).done(function(response) {
     if (response['success'] == 1){
       console.log("Successfully send browsers id to http server");
       console.log(`Browser ID: ${name}`);
     }
     else{
       console.log("We are not supposed to get here");
     }
   }).fail(function (response){
     console.log('failure of some sort');
   });
 });

function logIn(){
  //name = getOurId();//Generate a random id for the browser
  ourIDSpan.innerHTML = name;
  if(name.length > 0){
       connection.send('HELLO ' + name.toString() + ' 1');
  }
}


//handle messages from the server
connection.onmessage = function (message) {
   console.log("Got message", message.data);
   var data = {};
   if (message.data === "HELLO"){
     data.type = message.data;
   }
   else if (message.data === "SESSION_OK") {
     data.type = message.data;
   }
   else{
     data = JSON.parse(message.data);
   }

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
      case "ice":
         console.log("IN ICE");
         handleCandidate(data);
         break;
      case "sdp"://Here we handle our offer from the client.
         console.log("IN SDP");
         handleOffer(data);
         break;
      case "userLoggedIn":
         handleUserLoggedIn(data.names);
         break;
      case "HELLO":
         handleHello(data);
         break;
      default:
         console.log("GOT INTO DEFAULT CASE")
         console.log(data)
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
    "iceServers": [{ "url": "stun:stun.l.google.com:19302" }]
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
      navigator.getUserMedia = ( navigator.getUserMedia ||
                       navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia ||
                       navigator.msGetUserMedia);
      navigator.getUserMedia({ video: true, audio: true }, function (myStream) {
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
function add_camera(){
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
  	 alert(error);
        });
     };
}
//initiating a call, add camera from browser?
/*
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
	 alert(error);
      });
   }
});
*/
//when somebody sends us an offer
//when somebody sends us an offer we always set that offer given to us as our remote description
function handleOffer(data) {
   connectedUser = data.sdp.name;
   addConnection(connectedUser)
   console.log("RTCPeerConnection object was created");
   console.log(connections[connectedUser]);
   console.log("this is the offer: ",data.sdp);
   connections[connectedUser].setRemoteDescription(new RTCSessionDescription(data.sdp));

   //create an answer to an offer
   //When we create our answer to an offer we always set it to our local description
   connections[connectedUser].createAnswer(function (answer) {
      connections[connectedUser].setLocalDescription(answer);

      send({
         sdp: answer,
         type: "answer",
         sentTo: connectedUser,
      });

   }, function (error) {
      alert("Error when creating an answer");
      alert(error);
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
    candidate = {type:"candidate", candidate:data.ice.candidate, sdpMLineIndex: data.ice.sdpMLineIndex};
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

function handleHello(){
  console.log("Got Hello, registering with server");
  //connection.send("SESSION " + name.toString());
}
//constraints for desktop browser
var desktopConstraints = {

   video: {
      mandatory: {
         maxWidth:1920,
         maxHeight:1080
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
var cameraCounter = 0;
function addConnection(name){
  //create our element
  videoElement = document.createElement("video");
  var vidName = "video_"+name;
  videoElement.setAttribute("id", vidName);
  videoElement.setAttribute("controls", true);
  videoElement.setAttribute("autoplay", true);
  videoElement.setAttribute("muted", true);
  var col = $("<div class='col'>");
  var video_div = $("<div class='vid'>");
  var video_title_div = $("<div>");

  video_title_div.text(vidName);
  video_div.append(videoElement);
  video_div.append(video_title_div);
  col.append(video_div);
  var row_div;
  if (cameraCounter == 0){
    row_div = $("<div id='row_div' class='row'>");
    row_div.append(col);
    $("#callPage").append(row_div);
  }
  else{
    $("#row_div").append(col);//should be our last row
  }
  cameraCounter += 1;
  //cameraCounter = cameraCounter % 3;//2 for right now


  var connection = new RTCPeerConnection(configuration);

  // setup stream listening
  //connection.addStream(stream);//my stream?

  //when a remote user adds stream to the peer connection, we display it
  connection.onaddstream = function (e) {
     videoElement.srcObject = e.stream;
  };
  var playPromise = videoElement.play();
  if (playPromise !== undefined) {
    playPromise.then(_ => {
      // Automatic playback started!
      // Show playing UI.
    })
    .catch(error => {
      console.log("Cant autoplay ", error);
      // Auto-play was prevented
      // Show paused UI.
    });
  }
  // Setup ice handling
  connection.onicecandidate = function (event) {

     if (event.candidate) {
        send({ice:{type:"candidate",
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex}});
        console.log("This is what our event looks like", {ice:{type:"candidate",
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex}});
     }
     if (connections[name].connectionState == "connected"){
       console.log("Connection state is CONNECTED")
     }
     else{
       //console.log(connections[name].connectionState);
       console.log(event);
     }
  };
  //Add a connection dynamically
  connections[name] = connection
}
