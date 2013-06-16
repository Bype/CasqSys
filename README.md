CasqSys
=======

A full duplex video exchange for Raspberry Pi using a WebCam.

3 processes are involved
------------------------ 
- [mjpegstreamer](http://code.google.com/p/mjpg-streamer/) an http server that passes ram mjpeg frame from webcam to http client.
- curl_mjpeg allow switching from a server to another and pipes the frame to [omxplayer](https://github.com/huceke/omxplayer) an hardware mjpeg decoder.
- avahiBrowser : discover and check new server

Standards linux services used
-----------------------------
- [redis]() : servers ip address are maintain in a set with the key 'ip'
- [avahi](http://avahi.org/) : Avahi is a system which facilitates service discovery on a local network via the mDNS/DNS-SD protocol suite. Server announce itself to provide _casqsys._tcp service type
