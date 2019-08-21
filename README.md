# rpi-camera-webrtc-gstreamer

## Instructions:

You must have minimum gstreamer1.0 version 1.14.2
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
git checkout 1.14.2
./autogen.sh --enable-introspection 2>&1 | tee config_log.txt
make
sudo make install
sudo cp ./gst-libs/gst/webrtc/GstWebRTC-1.0.typelib /usr/lib/girepository-1.0/
```

```sh
export GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0
export OPENSSL_CONF=""
#(you may want to put this in your .bashrc file)
```
There may be more details here: https://github.com/centricular/gstwebrtc-demos/issues/37#issuecomment-409437153

### You also need a https server and you need to generate your own certs:
```sudo apt install nginx```
Here is how to generate the certs https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-18-04

