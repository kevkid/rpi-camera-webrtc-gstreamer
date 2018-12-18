import random
import ssl
import websockets
import asyncio
import os
import sys
import json
import argparse

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp

PIPELINE_DESC = '''
webrtcbin name=sendrecv bundle-policy=max-bundle
 tcpclientsrc host=192.168.11.31 port=5000 ! gdpdepay ! rtph264depay !avdec_h264 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
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
        await self.conn.send(json.dumps({'type': 'login', 'name': our_id, 'location':'python'}) )

    async def setup_call(self):
        await self.conn.send('SESSION {}'.format(self.peer_id))

    def send_sdp_offer(self, offer):
        text = offer.sdp.as_text()
        print ('Sending offer:\n%s' % text)
        msg = json.dumps({'type': 'offer', 'offer': text, "sentTo":self.peer_id, "name":self.id_})
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
        assert (self.webrtc)
        msg = json.loads(message)
        print("here is our message:!!!!:!!!:!!! {}".format(message))#it isnt finding the stuff in the message!
        if msg['type'] == "answer":
            print("Got into if 'sdp' in msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            sdp = msg['answer']
            assert(sdp['type'] == 'answer')
            sdp = sdp['sdp']
            print ('Received answer:\n%s' % sdp)
            res, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            promise = Gst.Promise.new()
            self.webrtc.emit('set-remote-description', answer, promise)
            print("got to ice promise")
            promise.interrupt()
        elif msg['type'] == "candidate":
            msg = msg['candidate']
            print("Got into if 'ice' in msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            
            candidate = msg['candidate']['candidate']
            print("candidate: {}".format(candidate))
            sdpmlineindex = msg['candidate']['sdpMLineIndex']
            self.webrtc.emit('add-ice-candidate', sdpmlineindex, candidate)

    async def loop(self):
        assert self.conn
        async for message in self.conn:
            if message == 'HELLO':
                await self.setup_call()
            elif message == 'SESSION_OK':
                print("starting pipeline")
                self.start_pipeline()
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
