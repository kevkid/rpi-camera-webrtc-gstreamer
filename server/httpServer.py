from flask import Flask, jsonify, render_template, request
import ssl
import os
import multiprocessing
import sys
sys.path.append('../cameras/')
from webrtc_sendrecv import *
app = Flask(__name__)

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
    return render_template('index.html')


@app.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)

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
    os.system('python3 signaling_server.py')
    #exec(open("./signaling_server.py").read())

def run_client_local(server, ip, port):#usually the camera server
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    our_id = random.randrange(10, 10000)
    peerid = 1
    print(our_id)
    c = WebRTCClient(our_id, peerid, server, ip, port)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(c.connect())
    res = asyncio.get_event_loop().run_until_complete(c.loop())
    sys.exit(res)

@app.route('/get_req_for_cam', methods=['GET','POST'])
def get_req_for_cam():
    print("POST FROM SERVER ASKING US FOR CAMERA")
    server = request.json['server']
    print(server)
    #here we request the camera from another server running this software
    #store ip addresses and loop over this changing the server each time, we need to insert this to PIPELINE_DESC

    p = multiprocessing.Process(target=run_client_local, args=(server, ))
    p.start()
    #run_client_local(server)

if __name__ == '__main__':
    p = multiprocessing.Process(target=run_signaling_server)#, args=("run_signaling_server", ))
    p.start()
    import time
    time.sleep(1)
    server = 'wss://127.0.0.1:8765'
    servers = ['192.168.11.32:5000']
    for i in servers:#2 cameras
        camera = i.split(':')
        print(camera)
        p = multiprocessing.Process(target=run_client_local, args=(server, camera[0], camera[1]))
        #p.start()
    print('server pid: {}'.format(p.pid))
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain("/opt/cert/nginx-selfsigned.crt", "/opt/cert/nginx-selfsigned.key")
    #context = ('/opt/cert/nginx-selfsigned.crt', '/opt/cert/nginx-selfsigned.key')#certificate and key files
    app.run(host='127.0.0.1', debug=True, ssl_context=context, use_reloader=False)
    #app.run(host='127.0.0.1', debug=True, ssl_context=context)
