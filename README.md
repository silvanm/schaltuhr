Schaltuhr [WIP]
===============

System which controls our light in the living room. At the moment it records our light usage via 
a light sensor. Eventually it will control a slave light via a IFTTT controlled switch.  

Sensors:
* Noise detection from Netatmo
* Light measurement using a ESP8266 (code is in `esp8266`)


Deploy:
-------

    gcloud app deploy app.yaml --project onyx-outpost-122619

