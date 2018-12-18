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
            msg = await asyncio.wait_for(ws.recv(), 10)
        except TimeoutError:
            print('Sending keepalive ping to {!r} in recv'.format(ws.remote_address))
            await ws.ping()
    return msg

async def signaling(websocket, path):
    while(True):
        #print (websocket.remote_address)
        #get message from client
        message = None
        try:
            message = await recv_msg_ping(websocket)
            #print(message)
        except websockets.ConnectionClosed:
            print("Connection to peer {!r} closed, exiting handler".format(websocket.remote_address))
            break

        #decode message
        try:
            data = json.loads(message)
            #print("Got this message from client: {}".format(message))
            
            if data['type'] == "login":
                if data['name'] in users:
                    await sendTo(websocket,{"type": "login", 
                            "Success":False})
                    print("sentTo Failed, username already taken")
                else:
                    users[data['name']] = {"websocket": websocket}
                    if data['location']  == "browser": #check if the peer is a browser which is passive and only accepts answers
                        users[data['name']]['location'] = "browser"
                        await sendTo(websocket, {"type": "login", 
                            "Success":True})
                        #print (users[data['name']])
                    else:
                        users[data['name']]['location'] = "python"
                        users[data['name']]['websocket'] = websocket#store python clients websocket
                        await websocket.send("SESSION_OK")
                        #print(users)
#                        for key, val in users.items():
#                            if val['location'] == "browser":#find the browsers
#                                await sendTo(websocket, {"type": "call", 
#                                                         "name":key})
                    #send all of the users a list of names that they can connect to
                    
                    for key, val in users.items():    
                        await sendTo(val['websocket'], {"type":"userLoggedIn",
                                     "names":list(users.keys())})
            elif data['type'] == "offer":#check if its an offer, message looks like: {"sdp": {"type": "offer", "sdp":...
                print("in offer")
                print("Sending offer to: {}".format(data['sentTo']))
                #if UserB exists then send him offer details 
                
                conn = users[data['sentTo']]['websocket']
                users[data['name']]['sentTo'] = data['sentTo']
                
                if conn is not None:
                    #setting that UserA connected with UserB 
                    #websocket['otherName'] = data['name']
                    #send to connection B
#                    if isinstance(data['offer'], str):
#                        offer = json.loads(data['offer'])
#                    else:
#                        offer = data['offer']
                    offer = data['offer']
                    await sendTo(conn, {"type": "offer", 
                            "offer":{"type":"offer", "sdp":offer},
                            "name":data['name']})#send the current connections name
                    #add other user to my list for retreaval later
                    print("offerFrom: {}, offerTo: {}".format(data['name'], data['sentTo']))
                    
            elif data['type'] == "answer":
                print("in answer")
                print("Sending answer to: {}".format(data['sentTo']))
                conn = users[data['sentTo']]['websocket']
                users[data['name']]['sentTo'] = data['sentTo']
                #print("in answer, answer type: {}, and the answer is this: {}".format(type(data['answer']), data['answer']))
                print("this is what we are sending: {}".format({"type": "answer", 
                            "answer":data['answer'], "from":data['name']}))
                if conn is not None:
                    #setting that UserA connected with UserB 
                    await sendTo(conn, {"type": "answer", 
                            "answer":data['answer'], "from":data['name']})
                    print("if we got here then we sent an answer!")
                #add other user to my list for retreaval later
                print("answerFrom: {}, answerTo: {}".format(data['name'], data['sentTo']))
            elif data['type'] == "candidate":
                print("in candidate")
                print("Sending candidate ice to: {}".format(users[data['name']]['sentTo']))
                sendingTo = users[data['name']]['sentTo']#Who am I sending data to
                conn = users[sendingTo]['websocket']
                candidate = data['candidate']
                print("this is what we are sending in candidate: {}".format({"type": "candidate", 
                            "candidate": data, "from": data['name']}))
                if conn is not None:
                    #setting that UserA connected with UserB 
                    
                    await sendTo(conn, {"type": "candidate", 
                            "candidate": data, "from": data['name']})
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
                print("Got another Message: {}".format(data))
                type(data)
        except:
            print("Got another Message: {}".format(message))
            print(type(message))
            print(message.keys())
            print("Not valid json")
            
        
        #closing the socket is handled?
        #await websocket.send(json.dumps({"msg": "Hello_World!!!!"}))
if __name__ == "__main__":
    print("Starting Server")
    #path.abspath("/opt/cert")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
    pathlib.Path("/opt/cert/nginx-selfsigned.crt").with_name('nginx-selfsigned.crt'), pathlib.Path("/opt/cert/nginx-selfsigned.key").with_name('nginx-selfsigned.key'))
    
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(signaling, '192.168.11.138', 8765, ssl=ssl_context, max_queue=16))
    asyncio.get_event_loop().run_forever()
    print('ended')
    users = {}
