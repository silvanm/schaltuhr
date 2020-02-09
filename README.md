Schaltuhr [WIP]
===============

System which controls our light in the living room. At the moment it records our light usage via 
a light sensor. Eventually it will control a slave light via a IFTTT controlled switch.  

Sensors:
* Noise detection from Netatmo
* Light measurement using a ESP8266 (code is in `esp8266`)

Note: There's two tools in this repo. The one in /code/scheduler.py is a scheduler which 
uses the config in code/config.py to generate a static schedule without any connection to an
ESP8266. Eventually both could be connected.

Deploy the flask command to Google App Engine
---------------------------------------------

    gcloud app deploy app.yaml --project onyx-outpost-122619


Deploy the scheduler to openshift
---------------------------------

- Login to the openshift console
- Set the project to `mupo-silvan`
- Run `make deploy`    
