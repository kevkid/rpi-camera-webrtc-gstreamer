#!/usr/bin/env python

import asyncio
import websockets
import json
import ssl
import pathlib
from concurrent.futures._base import TimeoutError
users = {}
connected = set()


async def sendTo(websocket, message):
    await websocket.send(json.dumps(message))

async def recv_msg_ping(ws):
    '''
    Wait for a message forever, and send a regular ping to prevent bad routers
    from closing the connection.
    '''
    msg = None
    while msg is None:
        try:
            msg = await asyncio.wait_for(ws.recv(), 30)
        except TimeoutError:
            print('Sending keepalive ping to {!r} in recv'.format(ws.remote_address))
            await ws.ping()
    return msg

async def signaling(websocket, path):
    while(True):
        message = None
        #name = None
        try:
            message = await recv_msg_ping(websocket)
            print(message)
        except websockets.ConnectionClosed:
            print("Connection to peer {!r} closed, exiting handler".format(websocket.remote_address))
            #figure out how we can allow the user to leave
            break

        #decode message
        try:
            data = json.loads(message)
            if data['type'] == "login":
                name = data['name']
                if name in users:#check if the browser is already logged in
                    await sendTo(websocket,{"type": "login",
                                            "payload":{"Success":False}})
                    print("sentTo Failed, username already taken")
                else:#new browser
                    payload = data['payload']
                    users[name] = {"websocket": websocket}#set the user to
                    if payload['location']  == "browser": #check if the peer is a browser which is passive and only accepts answers
                        users[name]['location'] = "browser"
                        await sendTo(websocket,{"type": "login",
                                            "payload":{"Success":True}})
                        peer_ids = []
                        #we are sending each python client every browser
                        for key, val in users.items():
                            print("key {}, val {}".format(key, val))
                            if val['location'] == "browser" and key not in connected:
                                peer_ids.append(key)
                                connected.add(key)
                        for key, val in users.items():
                            if val['location'] == "python":
                                for peer_id in peer_ids:
                                    await sendTo(val['websocket'], {'type': "peer_id", "peer_id":peer_id})#send all python clients my name to connect to me!
                                    await val['websocket'].send("SESSION_OK")
                    else:
                        users[name] = {"websocket": websocket}#set the user to
                        users[name]['location'] = "python"
                        print("in python area!")
                        await websocket.send("WAITING_FOR_PEER")
                        print("sent waiting for peer to python")
                    #need to fix this part where if a browser logs in we add all cameras somehow?
#                    for key, val in users.items():    
#                        await sendTo(val['websocket'], {"type":"userLoggedIn",
#                                     "names":list(users.keys())})
            elif data['type'] == "offer":#check if its an offer, message looks like: {"sdp": {"type": "offer", "sdp":... 
                name = data['name']
                sentTo = data['sentTo']
                users[name]['sentTo'] = sentTo
                conn = users[sentTo]['websocket']#in the peer we are offering to we store our websocket in there
                #check if we have a connection to our user stored (essentially if they logged in we should have it)
                if conn is not None:
                    payload = data['payload'] #Should look like: {"type":"offer", "sdp":sdp}
                    await sendTo(conn, {"type": "offer", 
                            "payload":payload,
                            "name":data['name']})#send the current connections name
                    #add other user to my list for retreaval later
                    print("offerFrom: {}, offerTo: {}".format(data['name'], data['sentTo']))
                    
            elif data['type'] == "answer":
                name = data['name']
                sentTo = data['sentTo']
                conn = users[sentTo]['websocket']
                users[name]['sentTo'] = sentTo
                payload = data['payload']
                if conn is not None:
                    #setting that UserA connected with UserB 
                    await sendTo(conn, {"type": "answer", 
                            "payload":payload, "from":name})
                #add other user to my list for retreaval later
                print("answerFrom: {}, answerTo: {}".format(data['name'], data['sentTo']))
            elif data['type'] == "candidate":
                print("in candidate")
                print("Sending candidate ice to: {}".format(users[data['name']]['sentTo']))
                sendingTo = users[data['name']]['sentTo']#Who am I sending data to
                conn = users[sendingTo]['websocket']
                print("Our data in candidate looks like this: {}".format(data))
                #payload = data['candidate']# data looks like: {"type": "candidate", "candidate": "candidate:1 1 UDP 2013266431 fe80::b8c2:dcff:feeb:9d7a 53950 typ host", "sdpMLineIndex": 0, "sentTo": "2078", "name": 432}
                print("this is what we are sending in candidate: {}".format(payload))
                if conn is not None:
                    #setting that UserA connected with UserB 
                    
                    await sendTo(conn, data)
                print("candidate ice From: {}, candidate ice To: {}".format(data['name'], users[data['name']]['sentTo']))
                
            elif data['type'] == "candidate":
                print("Disconnecting: {}".format(users[data['name']]['sentTo']))
                sendingTo = users[data['name']]['sentTo']#Who am I sending data to
                conn = users[sendingTo]['websocket']
                if conn is not None:
                    #setting that UserA connected with UserB 
                    await sendTo(conn, {"type": "leave"})
            elif data['type'] == "ping":
                print(data["msg"])
            else:
                print("Got wrong format: {}".format(data))
                type(data)
        except:
            print("Got another Message : {}".format(message))
            print(name)
            
        
        #closing the socket is handled?
        #await websocket.send(json.dumps({"msg": "Hello_World!!!!"}))
if __name__ == "__main__":
    print("Starting Server")
    #path.abspath("/opt/cert")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
    pathlib.Path("/opt/cert/nginx-selfsigned.crt").with_name('nginx-selfsigned.crt'), pathlib.Path("/opt/cert/nginx-selfsigned.key").with_name('nginx-selfsigned.key'))
    
    asyncio.get_event_loop().run_until_complete(
	websockets.serve(signaling, '127.0.0.1', 8765, ssl=ssl_context, max_queue=16))
        #websockets.serve(signaling, '192.168.11.148', 8765, ssl=ssl_context, max_queue=16))
    asyncio.get_event_loop().run_forever()
    print('ended')
    users = {}
