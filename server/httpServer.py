from flask import Flask, jsonify, render_template, request, redirect, url_for
import ssl
import os
import multiprocessing
import sys
import time
import raspi_opencv_motion as rom
sys.path.append('../cameras/')
from webrtc_sendrecv import *
app = Flask(__name__)
global config
config_loc = 'config.json'
# for CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST') # Put any other methods you need here
    return response
@app.route('/')
def index():
    #return app.send_static_file('index.html')
    return render_template('index.html', httpsserver=httpsserver, wsserver=wsserver)

#This gives the server the browsers peer_id so we can properly launch webrtcbin
@app.route('/get_browser_id', methods=['POST'])
def get_browser_id():
    b_id = request.json['browser_id']
    launch_cameras(b_id)#launch our camera clients
    return jsonify(success=True)

'''
TODO: I have to get the server to stop recording the video., somehow kill the process
'''
@app.route('/remove_camera', methods=['POST'])
def remove_camera():
    camera = request.json['camera']
    print(camera)
    res = [i for i in config['cameras'] if camera in i]
    res = res[0]
    config['cameras'].remove(res)
    save_config(config_loc)
    return jsonify(success=True, wasCameraRemoved=True)

#multiprocessing stuff
def terminate_process():
	global p
	if p.is_alive():
		p.terminate()
def run_signaling_server():
    #literally a hack:https://stackoverflow.com/questions/7974849/how-can-i-make-one-python-file-run-another
    #terminate_process()
    #p = multiprocessing.Process()
    print('running signaling server!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    os.system('python3 signaling_server.py --addr '+wss_addr[0]+' --port '+wss_addr[1]+' --cert-path /opt/cert/')
    #exec(open("./signaling_server.py").read())

def launch_cameras(browser_id = ""):
    assert (os.path.exists(config_loc)),"Config does not exist, make sure it does!"
    config = open_config(config_loc)
    cameras = config['cameras']
    wsserver = config['wsserver']
    time.sleep(1)
    for i in cameras:#n cameras
        camera = i.split(':')
        print(camera)
        p = multiprocessing.Process(target=run_client_local, args=(wsserver, camera[0], camera[1], browser_id))
        p.start()
        #time.sleep(3)

def run_client_local(server, ip, port, browser_id):#usually the camera server
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    our_id = random.randrange(10, 10000)
    print("OUR ID: {}!!!!!!!!!!!!!!!!!!!!!!".format(our_id))
    peerid = browser_id
    print(server)
    print(peerid)
    c = WebRTCClient(our_id, peerid, server, ip, port)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(c.connect())
    res = asyncio.get_event_loop().run_until_complete(c.loop())
    sys.exit(res)
    return 0

@app.route('/get_req_for_cam', methods=['GET','POST'])
def get_req_for_cam():
    global config
    print("POST FROM SERVER ASKING US FOR CAMERA")
    camera = request.json['camera']
    wsserver = request.json['wsserver']#gives us our websocket server so our client can connect, will prob be changed later
    if camera not in config['cameras']:
        config['cameras'].append(camera)#change naming convention
        save_config(config_loc)
        ip_port = camera.split(':')
        p = multiprocessing.Process(target=run_client_local, args=(wsserver, ip_port[0], ip_port[1]))
        p.start()
        time.sleep(1)
        resp = jsonify(success=True, wasCameraAdded=1)#camera was added
        return resp
        #return redirect(url_for('index'), code=302)
    resp = jsonify(success=False, wasCameraAdded=0, reason="Camera was not added, because already in database")#camera was added
    return resp

def motion_detection(ip_port, directory):
    print("in motion detection")
    cameraMonitor = rom.Monitor(ipAddr=ip_port[0], port=ip_port[1],directory=directory, threshold=0.015, timeToRecord=30, bitrate=2048)
    cameraMonitor.run()

import json
def open_config(location):
    with open(location) as json_file:
        return json.load(json_file)

def save_config(location):
    global config
    with open(location, 'w') as outfile:
        json.dump(config, outfile)
        print("saved config")

if __name__ == '__main__':
    global config
    config = open_config('config.json')
    http_addr = config['httpsserver'].split(':')
    wss_addr = config['wsserver'].replace('wss://','').split(':')
    httpsserver = config['httpsserver']
    wsserver = config['wsserver']
    certpath = config['certpath']
    cameras = config['cameras']
    video_save_dir = config['video_save_dir']
    #start signaling server
    p = multiprocessing.Process(target=run_signaling_server)#, args=("run_signaling_server", ))
    p.start()
    print('server pid: {}'.format(p.pid))
    for i in cameras:#2 cameras
        camera = i.split(':')
        print(camera)
        c = multiprocessing.Process(target=motion_detection, args=(camera,video_save_dir+camera[0],))
        c.start()
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain("/opt/cert/nginx-selfsigned.crt", "/opt/cert/nginx-selfsigned.key")
    #context = ('/opt/cert/nginx-selfsigned.crt', '/opt/cert/nginx-selfsigned.key')#certificate and key files
    app.run(host=http_addr[0], debug=True, ssl_context=context, use_reloader=False, port=http_addr[1])
    #app.run(host='192.168.11.148', debug=True, ssl_context=context, use_reloader=False)
    #app.run(host='127.0.0.1', debug=True, ssl_context=context, use_reloader=False)
