import time
import os
import obswebsocket
import obswebsocket.requests
import pygame.time


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

    def startStreaming(self, client):
        client.call(
            obswebsocket.requests.StartStreaming())
    
    def stopStreaming(self, client):
        client.call(
            obswebsocket.requests.StopStreaming())
    
    def startRecording(self, client):
        client.call(
            obswebsocket.requests.StartRecording())
    
    def stopRecording(self, client):
        client.call(
            obswebsocket.requests.StopRecording())
    
    def pauseRecording(self, client):
        client.call(
            obswebsocket.requests.PauseRecording())
   
    def resumeRecording(self, client):
        client.call(
            obswebsocket.requests.ResumeRecording())
    
    def getSourceSettings(self,client,item=None):
        print(client.call(obswebsocket.requests.GetSceneItemProperties(item)))
        print(client.call(obswebsocket.requests.GetSourceSettings(item)))
    
    def resetSceneItem(self,client,item=None):
        client.call(obswebsocket.requests.ResetSceneItem(item))

    def renderSceneItem(self,client,item=None,render=True):
        client.call(obswebsocket.requests.SetSceneItemRender(item,render))
    
    def setSceneItemPosition(self,client,item=None,x=0,y=0):
        client.call(obswebsocket.requests.SetSceneItemPosition(item,x,y))
    
    def setSceneItemTraansform(self,client,item=None,x_scale=0,y_scale=0,rotation=0):
        client.call(obswebsocket.requests.SetSceneItemTransform(item,x_scale,y_scale,rotation))
    
    def setSceneItemCrop(self,client,item=None,top=0,bottom=0,left=0,right=0):
        client.call(obswebsocket.requests.SetSceneItemCrop(item,bottom,left,right))
    
    #Kinda too slow.
    def animate(self,client,frames=0,items=[]):
        state=[]
        for s in items:
            print(s)
            istate={'item':s['item'],'startx':s['startx'],'starty':s['starty'],'endx':s['endx'],'endy':s['endy'],'speedx':(s['endx']-s['startx'])/frames,'speedy':(s['endy']-s['starty'])/frames,'curx':s['startx'],'cury':s['starty']}
            state.append(istate)
            client.call(obswebsocket.requests.SetSceneItemPosition(s['item'],istate['curx'],istate['cury']))
        for i in range(0,frames-1):
            starttime=pygame.time.get_ticks()
            for s in state:
                s['curx']+=s['speedx']
                s['cury']+=s['speedy']
                print(s['item'])
                client.call(obswebsocket.requests.SetSceneItemPosition(s['item'],s['curx'],s['cury']))
            endtime=pygame.time.get_ticks()
            print("Elapsed %d" % (endtime-starttime))
            pygame.time.wait(16)
        for s in state:
            client.call(obswebsocket.requests.SetSceneItemPosition(s['item'],s['endx'],s['endy']))
    
    
    
    