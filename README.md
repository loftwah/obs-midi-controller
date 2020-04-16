# obs-midi-controller
Sidecar application to control obs studio from a midi deck communicating to obs studio using obs-websocket api.

This glue application allows you to use your MIDI deck with OBS studio, and using the loopmidi dirver to republisg midi events to a loopback midi interface so other tools can use them.

My audio pipeline happens in VoiceMeter Potato and the video pipeline is managed by OBS Studio. Combining these with the virtual cam plugin linked below this can be used to create snazzy live stream like video feed for meetings.

Pieces I'm using this with:
* OBS Studio
* https://github.com/Palakis/obs-websocket
* http://www.tobias-erichsen.de/software/loopmidi.html
* https://www.vb-audio.com/Voicemeeter/potato.htm
* Behringer XTouch Mini
* https://github.com/CatxFish/obs-virtual-cam
