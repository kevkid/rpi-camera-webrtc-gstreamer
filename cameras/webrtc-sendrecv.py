import random
import ssl
import websockets
import asyncio
import os
import sys
import json
import argparse
import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp

''' this profile works: profile-level-id=42e01e 
profile_idc 0x42 == 66 so it is Baseline profile, 
profile-iop 0xe0 = 224 High 4:4:4 Intra Profile (244 with constraint set 3)
level 0x1e = 30 = level is 3.0

'''

#This works on both chome and ff
PIPELINE_DESC = '''
webrtcbin name=sendrecv bundle-policy=max-bundle
  videotestsrc is-live=true ! x264enc tune=zerolatency  bitrate=5000 speed-preset=ultrafast  ! queue !  rtph264pay config-interval=-1 ! 
 queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! rtpjitterbuffer ! sendrecv.

'''

'''
webrtcbin name=sendrecv bundle-policy=max-bundle
  rpicamsrc bitrate=10000000 ! video/x-h264,profile=constrained-baseline,width=1280,height=720,level=3.0 ! queue ! h264parse ! rtph264pay config-interval=-1 ! 
 queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! rtpjitterbuffer ! sendrecv.

'''


'''
webrtcbin name=sendrecv bundle-policy=max-bundle
  videotestsrc pattern=snow is-live=true ! x264enc tune=zerolatency  bitrate=1000 speed-preset=ultrafast ! video/x-h264,profile=constrained-baseline,width=176,height=144 ! queue ! rtph264pay config-interval=-1 pt=96 ! queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
'''


'''
webrtcbin name=sendrecv bundle-policy=max-bundle
  tcpclientsrc host=192.168.11.32 port=5000 ! gdpdepay ! rtph264depay ! video/x-h264,profile=baseline,width=640,height=360,framerate=20/1 ! queue max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 ! queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
'''
#############################################
'''
webrtcbin name=sendrecv 
 rpicamsrc bitrate=1000000 ! video/x-h264,profile=baseline,width=640,height=360,framerate=20/1,level=3.1 ! queue max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
'''

'''
webrtcbin name=sendrecv 
 rpicamsrc bitrate=600000 annotation-mode=12 preview=false ! video/x-h264,profile=baseline,width=640,height=360,framerate=20/1,level=3.1 ! queue max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 ! application/x-rtp,media=video,encoding-name=H264,payload=100 ! sendrecv.
'''

'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 tcpclientsrc host=192.168.11.32 port=5000 ! gdpdepay ! rtph264depay ! avdec_h264 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay ! queue ! application/x-rtp,media=video,encoding-name=VP8,payload=97 ! sendrecv.
'''


'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 videotestsrc pattern=snow is-live=true ! x264enc tune=zerolatency  bitrate=1000 speed-preset=ultrafast  ! queue !  rtph264pay config-interval=1 ! 
 queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
 audiotestsrc is-live=true wave=red-noise ! audioconvert ! audioresample ! queue ! opusenc ! rtpopuspay !
 queue ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! sendrecv.
'''



'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 tcpclientsrc host=192.168.11.32 port=5000 ! gdpdepay ! rtph264depay ! avdec_h264 ! videoconvert ! queue ! x264enc tune=zerolatency  bitrate=2000 speed-preset=ultrafast ! h264parse ! rtph264pay config-interval=-1 ! queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
'''

'''
webrtcbin name=sendrecv 
 tcpclientsrc host=192.168.11.32 port=5000 ! gdpdepay ! rtph264depay ! video/x-h264,profile=constrained-baseline,width=640,height=360,level=3.0 ! queue max-size-time=100000000 ! h264parse ! rtph264pay config-interval=-1 name=payloader ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! sendrecv.
'''

'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 videotestsrc is-live=true ! x264enc tune=zerolatency  bitrate=5000 speed-preset=ultrafast  ! queue !  rtph264pay config-interval=-1 ! 
 queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! rtpjitterbuffer ! sendrecv.
 audiotestsrc is-live=true wave=red-noise ! audioconvert ! audioresample ! queue ! opusenc ! rtpopuspay !
 queue ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! sendrecv.
'''
#this works videotestsrc h264enc on firefox, chrome gives artifacts















'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 tcpclientsrc host=192.168.11.32 port=5000 ! gdpdepay ! rtph264depay ! avdec_h264 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
 queue ! application/x-rtp,media=video,encoding-name=VP8,payload=97 ! sendrecv.
 audiotestsrc is-live=true wave=red-noise ! audioconvert ! audioresample ! queue ! opusenc ! rtpopuspay !
 queue ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! sendrecv.
'''

'''
webrtcbin name=sendrecv bundle-policy=max-bundle
 videotestsrc is-live=true pattern=snow ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
 queue ! application/x-rtp,media=video,encoding-name=VP8,payload=97 ! sendrecv.
 audiotestsrc is-live=true wave=red-noise ! audioconvert ! audioresample ! queue ! opusenc ! rtpopuspay !
 queue ! application/x-rtp,media=audio,encoding-name=OPUS,payload=96 ! sendrecv.
'''




class WebRTCClient:
    def __init__(self, id_, peer_id, server):
        self.id_ = id_
        self.conn = None
        self.pipe = None
        self.webrtc = None
        self.peer_id = peer_id
        self.server = server or 'wss://webrtc.nirbheek.in:8443'

    async def connect(self):
        sslctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self.conn = await websockets.connect(self.server, ssl=sslctx)
        await self.conn.send(json.dumps({'type': 'login', 'name': our_id, 'payload': {'location':'python'}}) )

    async def setup_call(self):
        await self.conn.send('SESSION {}'.format(self.peer_id))

    def send_sdp_offer(self, offer):
        sdp = offer.sdp.as_text()
        print ('Sending offer:\n%s' % sdp)
        payload = {'type': 'offer', 'sdp':sdp}
        msg = json.dumps({'type': 'offer', "sentTo":self.peer_id, "name":self.id_, 'payload': payload})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(msg))

    def on_offer_created(self, promise, _, __):
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value('offer')
        promise = Gst.Promise.new()
        self.webrtc.emit('set-local-description', offer, promise)
        promise.interrupt()
        self.send_sdp_offer(offer)

    def on_negotiation_needed(self, element):
        print("on_negotiation_needed")
        print("This is the element!: {}".format(element))#goes in here
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, None)
        element.emit('create-offer', None, promise)

    def send_ice_candidate_message(self, _, mlineindex, candidate):
        icemsg = json.dumps({"type":"candidate", 'candidate': candidate, 'sdpMLineIndex': mlineindex, "sentTo":self.peer_id, "name":self.id_})
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(icemsg))



    def on_incoming_stream(self, _, pad):
        if pad.direction != Gst.PadDirection.SRC:
            return

        decodebin = Gst.ElementFactory.make('decodebin')
        decodebin.connect('pad-added', self.on_incoming_decodebin_stream)
        self.pipe.add(decodebin)
        decodebin.sync_state_with_parent()
        self.webrtc.link(decodebin)

    def start_pipeline(self):
        self.pipe = Gst.parse_launch(PIPELINE_DESC)
        self.webrtc = self.pipe.get_by_name('sendrecv')
        self.webrtc.connect('on-negotiation-needed', self.on_negotiation_needed)
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message)
        self.webrtc.connect('pad-added', self.on_incoming_stream)
        self.pipe.set_state(Gst.State.PLAYING)

    async def handle_sdp(self, message):
        #assert (self.webrtc) #may not need this 
        msg = json.loads(message)
        print("here is our message:!!!!:!!!:!!! {}".format(message))#it isnt finding the stuff in the message!
        if msg['type'] == "answer":
            print("Got into if 'sdp' in msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            payload = msg['payload']
            assert(payload['type'] == 'answer')#make sure its an answer
            sdp = payload['sdp']
            print ('Received answer:\n%s' % sdp)
            res, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            promise = Gst.Promise.new()
            self.webrtc.emit('set-remote-description', answer, promise)
            promise.interrupt()
        elif msg['type'] == "candidate":
            candidate = msg["candidate"]
            sdpmlineindex = msg["sdpMLineIndex"]
            print("Got into if 'ice' in msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("candidate: {}, sdpMLineIndex: {}".format(candidate, sdpmlineindex))
            self.webrtc.emit('add-ice-candidate', sdpmlineindex, candidate)
        elif msg['type'] == "peer_id":
            self.peer_id = msg["peer_id"]#set peer id remotely
            print("the peer id: {}".format(self.peer_id))

    async def loop(self):
        assert self.conn
        print(self.conn)
        async for message in self.conn:
            if message == 'HELLO':
                await self.setup_call()
            elif message == 'SESSION_OK':
                print("starting pipeline")
                self.start_pipeline()
            elif message == "WAITING_FOR_PEER":
                print("WAITING FOR PEER")
            elif message.startswith('ERROR'):
                print (message)
                return 1
            else:
                await self.handle_sdp(message)
        return 0


def check_plugins():
    needed = ["opus", "vpx", "nice", "webrtc", "dtls", "srtp", "rtp",
              "rtpmanager", "videotestsrc", "audiotestsrc"]
    missing = list(filter(lambda p: Gst.Registry.get().find_plugin(p) is None, needed))
    if len(missing):
        print('Missing gstreamer plugins:', missing)
        return False
    return True

if __name__=='__main__':
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument('peerid', help='String ID of the peer to connect to')
    parser.add_argument('--server', help='Signalling server to connect to, eg "wss://127.0.0.1:8443"')
    args = parser.parse_args()
    print(args)
    our_id = random.randrange(10, 10000)
    c = WebRTCClient(our_id, args.peerid, args.server)
    asyncio.get_event_loop().run_until_complete(c.connect())
    res = asyncio.get_event_loop().run_until_complete(c.loop())
    sys.exit(res)
