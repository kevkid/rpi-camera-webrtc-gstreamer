from flask import Flask, jsonify, render_template, request, redirect, url_for
import ssl
import os
import multiprocessing
import sys
import time
import raspi_opencv_motion as rom
sys.path.append('../cameras/')
from webrtc_sendrecv import *
#gstreamer stuff
import gi
import sys
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
Gst.init(sys.argv)
#gstreamer stuff
app = Flask(__name__)
global config
global pipelines
config_loc = 'config.json'

#camera class
class camera:
    def __init__(self, address_port):
        ap = address_port.split(':')
        self.address = ap[0]#ip address of cam
        self.port = ap[1]#port camera is transmitting udp stream
        self.motion_port = str(int(ap[1])+1)
        self.client_port = str(int(ap[1])+2)
        self.motionSplit = '''udpsrc port={} ! tee name=t t. ! queue ! udpsink port={} name=motion_port t.
                            ! queue ! udpsink port={} name=client_port'''.format(self.port, self.motion_port, self.client_port)
        self.pipelines = {}
        self.clientSplit = '''udpsrc port={} ! tee name=t'''.format(self.client_port)
        self.clients = []#dunamically add clients (browser ids)
    def gen_clientSplit(self):
        tmp = self.clientSplit
        for client in self.clients:
            tmp += ' t. ! queue ! udpsink port={}'.format(client)
        return tmp

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
#this is sent as soon as js is loaded on webpage
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
    wsserver = config['wsserver']
    for i, cam in enumerate(cameras):#n cameras, using an index so we can adjust the ports for each browser
        cam.clients.append(str(int(browser_id)+i))
        print(cam.clients)
        pipe = Gst.parse_launch(cam.gen_clientSplit())#must check for duplicate browserids
        cam.pipelines['clientSplitPipe'] = pipe
        pipe.set_state(Gst.State.PLAYING)
        print(cam.address)
        print('browserport: {} for camera: {}'.format(cam.clients[-1], cam.address))
        print(cam.gen_clientSplit())
        p = multiprocessing.Process(target=run_client_local, args=(wsserver, cam.address, str(int(browser_id)+i), browser_id))
        p.start()
        time.sleep(3)

def run_client_local(server, ip, port, browser_id):#usually the camera server
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    our_id = random.randrange(3000, 9000)
    peerid = browser_id
    c = WebRTCClient(our_id, peerid, server, ip, port)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(c.connect())
    res = asyncio.get_event_loop().run_until_complete(c.loop())
    #sys.exit(res)
    #return 0

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
    resp = jsonify(success=False, wasCameraAdded=0, reason="Camera was not added, because already in database")#camera was added
    return resp

def motion_detection(cam, directory):
    print("in motion detection")
    print(cam.motion_port)
    cameraMonitor = rom.Monitor(ipAddr=cam.address, port=cam.motion_port,directory=directory+cam.address, threshold=0.005, timeToRecord=5, bitrate=2048)
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
#pipe should be camera  -> udpsink to clientSplit
#                       ->udp to motion/save
def recieveCamInfo(cameras):
    global pipelines
    pipelines = {}
    for cam in cameras:
        pipe = Gst.parse_launch(cam.motionSplit)
        cam.pipelines['motionSplit'] = pipe#put actual pipe into cam class
        pipe.set_state(Gst.State.PLAYING)
if __name__ == '__main__':
    global config
    config = open_config('config.json')
    http_addr = config['httpsserver'].split(':')
    wss_addr = config['wsserver'].replace('wss://','').split(':')
    httpsserver = config['httpsserver']
    wsserver = config['wsserver']
    certpath = config['certpath']
    cameras = []#list of cameras
    for cam in config['cameras']:
        cameras.append(camera(cam))
    recieveCamInfo(cameras)#starts 2 pipelines, one to save, one to forward to clients.
    video_save_dir = config['video_save_dir']
    #start signaling server
    p = multiprocessing.Process(target=run_signaling_server)#, args=("run_signaling_server", ))
    p.start()
    print('server pid: {}'.format(p.pid))
    for cam in cameras:
        print(cam.address)
        print(cam.port)
        c = multiprocessing.Process(target=motion_detection, args=(cam,video_save_dir))
        c.start()
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain("/opt/cert/nginx-selfsigned.crt", "/opt/cert/nginx-selfsigned.key")
    #context = ('/opt/cert/nginx-selfsigned.crt', '/opt/cert/nginx-selfsigned.key')#certificate and key files
    app.run(host=http_addr[0], debug=True, ssl_context=context, use_reloader=False, port=http_addr[1])
    #app.run(host='192.168.11.148', debug=True, ssl_context=context, use_reloader=False)
    #app.run(host='127.0.0.1', debug=True, ssl_context=context, use_reloader=False)
