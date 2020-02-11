# rpi-camera-webrtc-gstreamer

## Instructions:
### install websockets
```
sudo -H pip3 install websockets
```
***You must have minimum gstreamer1.0 version 1.14.2***
follow this: http://lifestyletransfer.com/how-to-install-gstreamer-on-ubuntu/
**don't install gstreamer1.0-plugins-bad**

You must have gstreamer1.0-plugins-bad compiled with the `--enable-introspection` flag, you may need to compile it yourself.
### gobject and pyobject:

```sh
sudo apt remove python3-gi python3-pygobject
sudo apt install libgirepository1.0-dev
sudo apt install libcairo2-dev
sudo -H pip3 install pygi pygobject
```

### How to compile gstreamer1.0-plugins-bad
#### Dependencies:
```sh
sudo apt install libtool checkinstall libssl-dev gtk-doc-tools libgstreamer-plugins-base1.0-dev

LIBNICE_VERSION="0.1.16" # libnice (v>=0.1.14) needed for webrtcbin
LIBSRTP_VERSION="2.2.0" # libsrtp (v>=2.2.0) required for srtp plugin
WEBRTCAUDIO_VERSION="0.3.1" # webrtc-audio-processing required for webrtcdsp
USRSCTP_VERSION="0.9.3.0" # usrsctp required for webrtc data channels (sctp)

# libnice
PACKAGE=libnice
wget https://nice.freedesktop.org/releases/$PACKAGE-$LIBNICE_VERSION.tar.gz
tar xvf $PACKAGE-$LIBNICE_VERSION.tar.gz
cd $PACKAGE-$LIBNICE_VERSION
./configure --prefix=/usr --enable-compile-warnings=minimum
make
echo $PACKAGE > description-pak
sudo checkinstall -y --fstrans=no
sudo ldconfig
cd ..

dependencies for plugins:
# libsrtp
PACKAGE=libsrtp
wget https://github.com/cisco/$PACKAGE/archive/v$LIBSRTP_VERSION.tar.gz -O $PACKAGE-$LIBSRTP_VERSION.tar.gz
tar xzf $PACKAGE-$LIBSRTP_VERSION.tar.gz
cd $PACKAGE-$LIBSRTP_VERSION
./configure --prefix=/usr
make
echo $PACKAGE > description-pak
sudo checkinstall -y --fstrans=no
sudo ldconfig
cd ..

# webrtc audio processing
PACKAGE=webrtc-audio-processing
wget http://freedesktop.org/software/pulseaudio/$PACKAGE/$PACKAGE-$WEBRTCAUDIO_VERSION.tar.xz
tar xvf $PACKAGE-$WEBRTCAUDIO_VERSION.tar.xz
cd $PACKAGE-$WEBRTCAUDIO_VERSION
./configure --prefix=/usr
make
echo $PACKAGE > description-pak
sudo checkinstall -y --fstrans=no
sudo ldconfig
cd ..

# usrsctp
PACKAGE=usrsctp
wget https://github.com/sctplab/$PACKAGE/archive/$USRSCTP_VERSION.tar.gz -O $PACKAGE-$USRSCTP_VERSION.tar.gz
tar xzf $PACKAGE-$USRSCTP_VERSION.tar.gz
cd $PACKAGE-$USRSCTP_VERSION
./bootstrap
./configure --prefix /usr/
make
echo $PACKAGE > description-pak
sudo checkinstall -y --fstrans=no
sudo ldconfig
cd ..
```

### Build gstreamer1.0-plugins-bad
```sh
git clone https://github.com/GStreamer/gst-plugins-bad.git
cd gst-plugins-bad
git checkout 1.14.2 #Set you correct verion by checking what version of gstreamer you currently have.
./autogen.sh --enable-introspection 2>&1 | tee config_log.txt
make
sudo make install
sudo cp ./gst-libs/gst/webrtc/GstWebRTC-1.0.typelib /usr/lib/girepository-1.0/
```

```sh
export GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0:/usr/lib/gstreamer-1.0
export OPENSSL_CONF=""
#(you may want to put this in your .bashrc file)
```
There may be more details here: https://github.com/centricular/gstwebrtc-demos/issues/37#issuecomment-409437153

### You also need a https server and you need to generate your own certs:
```sudo apt install nginx```
Here is how to generate the certs https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-18-04

# How to run server
`python3 httpserver.py`

# How to run client
`Follow the bash commands to run in terminal using current pipelines`

# Current pipelines:

#This works for server
```sh
gst-launch-1.0 -v videotestsrc ! x264enc key-int-max=1 speed-preset=ultrafast ! "video/x-h264,profile=constrained-baseline,width=1280,height=720,stream-format=byte-stream,level=(string)3.1" ! rtph264pay config-interval=1 ! udpsink port=7001
```
#### If you want to get it to work on multiple clients you would want to use tee:
```sh
gst-launch-1.0 -v videotestsrc is-live=1 pattern=ball flip=true ! x264enc speed-preset=ultrafast tune=zerolatency key-int-max=1 ! "video/x-h264,profile=constrained-baseline,width=1280,height=720,stream-format=byte-stream,level=(string)3.1" ! rtph264pay ! tee name=t t. ! queue ! udpsink auto-multicast=true port=7000 t. ! queue ! udpsink auto-multicast=true port=7000 t. ! queue ! udpsink auto-multicast=true port=7000 t. ! queue ! udpsink auto-multicast=true port=7000 t. ! queue ! udpsink auto-multicast=true port=7000
```
The previous code gives us 5 different udp streams

#This works for client in bash

```sh
gst-launch-1.0 udpsrc port=7001 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink
```

#This works for webrtcclient
```sh
PIPELINE_DESC = '''
	webrtcbin name=sendrecv bundle-policy=max-bundle
        udpsrc port=7001 caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay !
        h264parse ! rtph264pay config-interval=-1 !
        queue ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! rtpjitterbuffer ! sendrecv.'''

```
### If you want to use the camera, run this on the camera setting your host to the correct ip address of the server consuming the stream

```
gst-launch-1.0 -v rpicamsrc bitrate=1000000 keyframe-interval=1 ! "video/x-h264,profile=constrained-baseline,width=1280,height=720,stream-format=byte-stream,level=(string)3.1" ! rtph264pay config-interval=1 ! udpsink host=192.168.XXX.XXX port=7001
```
# Credit:
https://github.com/centricular/gstwebrtc-demos
