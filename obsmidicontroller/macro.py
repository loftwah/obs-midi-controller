import time
import os
import obswebsocket
import obswebsocket.requests


class macro():
    def sleep(self, client, num=1):
        time.sleep(num)

    def switchScene(self, client, name=None):
        if name:
            status = client.call(
                obswebsocket.requests.GetStudioModeStatus())
            if status.getStudioMode():
                client.call(
                    obswebsocket.requests.SetPreviewScene(name))
            else:
                client.call(
                    obswebsocket.requests.SetCurrentScene(name))

    def transitionScene(self, client, name=None, duration=300):
        if name:
            status = client.call(obswebsocket.requests.GetStudioModeStatus())
        client.call(
            obswebsocket.requests.SetCurrentTransition(name))
        if status.getStudioMode():
            client.call(
                obswebsocket.requests.TransitionToProgram(name, with_transition_duration=duration))

    def setVolume(self, client, source=None, vol=300):
        client.call(
            obswebsocket.requests.SetVolume(source, vol))

    def setMute(self, client, source=None, mute=False):
        client.call(
            obswebsocket.requests.SetMute(source, mute))

    def setBrowserSource(self, client, source=None, url=None):
        client.call(
            obswebsocket.requests.SetBrowserSourceProperties(source, url=url))
