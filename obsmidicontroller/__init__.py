import os
import time
import tkinter
import tkinter.ttk as ttk

import confuse
import mido
import obswebsocket
import obswebsocket.requests
import yaml
import pygame.mixer as mixer

class OBSMidi:
    client = None
    window = None
    controller = None
    config = None
    audiosources = None
    port=None
    outport=None
 
    def __init__(self, config):
        self.config = config
        self.initUI()
        #initialize MIDI Stack
        #mido.set_backend(name='mido.backends.rtmidi')
        #Initialize PyGaem Audio
        mixer.init()
        #Initialize MIDI Connections
        self.initMidi()
        #Initialize connection to OBS
        self.initOBS(self.hst.get(), self.prt.get(), self.pw.get())
        self.updateObsTree()

        self.window.mainloop()

    def initController(self):
        self.activeinputcontroller=self.config['controllers']['active-input'].get()
        self.activeoutputcontroller=self.config['controllers']['active-output'].get()
        for c in self.config['controllers']['inputs']:
            print(c['name'])
            if c['name'].get()==self.activeinputcontroller:
                self.controller=c
        print(self.controller)
        
    def initMidi(self):
        if self.port:
            self.port.close()
        if self.outport:
            self.outport.close()
        self.initController()
        self.port = mido.open_input(self.activeinputcontroller,callback=self.handleMidiMessage)
        self.outport = mido.open_output(self.activeoutputcontroller)

    def initializeAudiosources(self):
        scenes = self.client.call(obswebsocket.requests.GetSceneList())
        for s in scenes.getScenes():
            name = s['name']
        sourcetypes = self.client.call(
            obswebsocket.requests.GetSourceTypesList())
        self.audiotypes = []
        for st in sourcetypes.getTypes():
            stcap = st['caps']
            typid = st['typeId']
            if stcap['hasAudio']:
                self.audiotypes.append(typid)

    def initOBS(self, host, port, password):
        if self.client:
            self.client.disconnect()
        
        self.client = obswebsocket.obsws(host, port, password)
        self.client.connect()
        self.client.register(self.obsevent,obswebsocket.events.SwitchScenes)
        self.initializeAudiosources()

    def obsevent(self, event):
        print(event)

    def getAudioSourcesScene(self):
        if not self.audiosources:
            spsources = self.client.call(obswebsocket.requests.GetSpecialSources())
            sources = self.client.call(
                obswebsocket.requests.GetCurrentScene()).getSources()
            audiosources = []
            try:
                audiosources.append(spsources.getDesktop1())
            except:
                pass
            try:
                audiosources.append(spsources.getDesktop2())
            except:
                pass
            try:
                audiosources.append(spsources.getMic1())
            except:
                pass
            try:
                audiosources.append(spsources.getMic2())
            except:
                pass
            try:
                audiosources.append(spsources.getMic3())
            except:
                pass
            for s in sources:
                name = s['name']
                typ = s['type']
                if typ in self.audiotypes:
                    audiosources.append(name)
            self.audiosources=audiosources
        return self.audiosources

    def switchScenes(self,event):
        print(event)
        print("clearing cached scene audio sources")
        self.audiosources=None

    def clicked(self):
        self.initOBS(self.hst.get(), self.prt.get(), self.pw.get())

    def handleSceneChange(self,message,scenedefs):
        status = self.client.call(
            obswebsocket.requests.GetStudioModeStatus())
        scenes = self.client.call(
            obswebsocket.requests.GetSceneList()).getScenes()
        if scenedefs.index(message.note) < len(scenes):
            name = scenes[scenedefs.index(message.note)]['name']
            print(u"Switching to {}".format(name))
            if status.getStudioMode():
                self.client.call(
                    obswebsocket.requests.SetPreviewScene(name))
            else:
                self.client.call(
                    obswebsocket.requests.SetCurrentScene(name))

    def handleStreaming(self): 
        self.client.call(
            obswebsocket.requests.StartStopStreaming())

    def handleRecording(self):
        self.client.call(
                        obswebsocket.requests.StartStopRecording())

    def handleTransitions(self,message,transdefs):
        status = self.client.call(
            obswebsocket.requests.GetStudioModeStatus())
        trans = self.client.call(
            obswebsocket.requests.GetTransitionList()).getTransitions()
        if transdefs.index(message.note) < len(trans):
            name = trans[transdefs.index(message.note)]['name']
            self.client.call(
                obswebsocket.requests.SetCurrentTransition(name))
            if status.getStudioMode():
                self.client.call(
                    obswebsocket.requests.TransitionToProgram(name))

    def playSoundboard(self,fle):
        mixer.music.load(fle)
        mixer.music.play()

    def handleMidiMessage(self, message):
        self.outport.send(message)
        if message.type == "note_on":
            print(message)
            if int(message.channel) == self.controller['channel'].get():
                scenedefs = self.controller['notes']['scenes'].get()
                if message.note in scenedefs:
                    self.handleSceneChange(message,scenedefs)
                reqdefs = self.controller['notes']['recording'].get()
                if message.note in reqdefs:
                    self.handleRecording()
                streamdefs = self.controller['notes']['streaming'].get(
                )
                if message.note in streamdefs:
                    self.handleStreaming()
                transdefs = self.controller['notes']['transitions'].get(
                )
                if message.note in transdefs:
                    self.handleTransitions(message,transdefs)
                #mutedefs = self.controller['audio']['mute'].get()
                #if message.note in mutedefs:
                #    audiosources=self.getAudioSourcesScene()
                #    if mutedefs.index(message.note) < len(audiosources):
                #        name = audiosources[mutedefs.index(message.note)]
                #        self.client.call(
                #            obswebsocket.requests.ToggleMute(name))
                soundboard = self.controller['soundboard'].get()
                print(soundboard)
                for i in soundboard:
                    if message.note==i['id']:
                        print(i['file'])
                        self.playSoundboard(i['file'])
        #elif message.type == "control_change":
        #    if int(message.channel) == self.controller['channel']['id'].get():
        #        voldefs = self.controller['audio']['vol'].get()
        #        if message.control in voldefs:
        #            audiosources=self.getAudioSourcesScene()
        #            if voldefs.index(message.control) < len(audiosources):
        #                name = audiosources[voldefs.index(
        #                    message.control)]
        #                self.client.call(obswebsocket.requests.SetVolume(
        #                    name, (float(message.value)/127.0)))
        else:
            print(message)

    def saveConfig(self):
        pass

    def updateObsTree(self):
        self.obstree.delete('scenes')
        self.obstree.delete('transitions')
        self.obstree.delete('recording')
        self.obstree.delete('streaming')

        self.obstree.insert('', 'end', 'scenes', text='Scenes',open=True)
        self.obstree.insert('', 'end', 'transitions', text='Transitions',open=True)
        self.obstree.insert('', 'end', 'recording', text='Recording',open=True)
        self.obstree.insert('', 'end', 'streaming', text='Streaming',open=True)

        self.sbtree.delete(*self.sbtree.get_children())
        
        scenes = self.client.call( obswebsocket.requests.GetSceneList()).getScenes()
        scenedefs=self.controller['notes']['scenes'].get()
        for i in scenedefs:
            index=scenedefs.index(i)
            if index<len(scenes):
                name = scenes[index]['name']
                self.obstree.insert('scenes', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i))

        trans = self.client.call(
            obswebsocket.requests.GetTransitionList()).getTransitions()
        print(trans)
        transdefs = self.controller['notes']['transitions'].get(
                )
        print(transdefs)
        for i in transdefs:
            print(i)
            index=transdefs.index(i)
            print(index)
            if index<len(trans):
                name = trans[index]['name']
                print("inserting: %s"%name)
                self.obstree.insert('transitions', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i))
        reqdefs = self.controller['notes']['recording'].get()
        for i in reqdefs:
            name="req-%s"%i
            self.obstree.insert('recording', 'end', name, text=name,
                        values=(self.midiin.get(),self.chnl.get(),i))
        strmdefs = self.controller['notes']['streaming'].get()
        for i in strmdefs:
            name="strm-%s"%i
            self.obstree.insert('streaming', 'end', name, text=name,
                        values=(self.midiin.get(),self.chnl.get(),i))
        sounddefs=self.controller['soundboard'].get()
        for i in sounddefs:
            name=i['name']
            self.sbtree.insert('', 'end', name, text=name,
                        values=(self.midiin.get(),self.chnl.get(),i['id'],i['file']))
        

    def initUI(self):
        self.window = tkinter.Tk()
        self.window.title("OBS Midi Controller")
        self.initController()

        self.hst = tkinter.StringVar()
        self.hst.set(self.config['obsserver']['host'])
        self.prt = tkinter.StringVar()
        self.prt.set(self.config['obsserver']['port'])
        self.pw = tkinter.StringVar()
        self.pw.set(self.config['obsserver']['password'])
        self.chnl = tkinter.StringVar()
        self.chnl.set(self.controller['channel'])

        self.midiin = tkinter.StringVar()
        self.midiin.set(self.activeinputcontroller)
        self.midiout = tkinter.StringVar()
        self.midiout.set(self.activeoutputcontroller)


        tkinter.Label(self.window, text="OBS Server").grid(column=0, row=0)

        tkinter.Label(self.window, text="Host").grid(column=0, row=1)
        self.hstW = tkinter.Entry(self.window, width=10, textvariable=self.hst)
        self.hstW.grid(column=1, row=1)

        tkinter.Label(self.window, text="Port").grid(column=2, row=1)
        self.prtW = tkinter.Entry(self.window, width=10, textvariable=self.prt)
        self.prtW.grid(column=3, row=1)

        tkinter.Label(self.window, text="Password").grid(column=0, row=2)
        self.pwW = tkinter.Entry(self.window, width=10, textvariable=self.pw)
        self.pwW.grid(column=1, row=2)

        
        tkinter.Label(self.window, text="Midi Output").grid(column=0, row=3)
        self.midioutCombo=tkinter.ttk.Combobox(self.window,textvariable=self.midiout)

        self.midioutCombo.grid(column=1,row=3)
        self.midioutCombo['values'] = mido.get_output_names()

        tkinter.Label(self.window, text="Midi Input").grid(column=2, row=3)
        self.midiinCombo=tkinter.ttk.Combobox(self.window,textvariable=self.midiin)

        self.midiinCombo.grid(column=3,row=3)
        self.midiinCombo['values'] = mido.get_input_names()

        tkinter.Label(self.window, text="Input Channel").grid(column=2, row=4)
        self.chnlW = tkinter.Entry(
            self.window, width=10, textvariable=self.chnl)
        self.chnlW.grid(column=3, row=4)


        self.n = ttk.Notebook(self.window)
        self.obs = ttk.Frame(self.n)   # first page, which would get widgets gridded into it
        self.soundboard = ttk.Frame(self.n)   # second page
        self.n.add(self.obs, text='OBS Controls')
        self.n.add(self.soundboard, text='Soundboard')
        self.n.grid(column=0, row=5, columnspan=6)

        self.obstree = ttk.Treeview(
            self.obs, columns=('midi', 'channel', 'code'))
        self.obstree.heading("#0", text="Name", anchor=tkinter.W)
        self.obstree.heading("midi", text="Midi Device", anchor=tkinter.W)
        self.obstree.heading("channel", text="Channel", anchor=tkinter.W)
        self.obstree.heading("code", text="Code", anchor=tkinter.W)
        
        self.obstree.insert('', 'end', 'scenes', text='Scenes',
                         values=('15KB Yesterday mark'))
        self.obstree.insert('', 'end', 'transitions', text='Transitions',
                         values=('15KB Yesterday mark'))
        self.obstree.insert('', 'end', 'recording', text='Recording',
                         values=('15KB Yesterday mark'))
        self.obstree.insert('', 'end', 'streaming', text='Streaming',
                         values=('15KB Yesterday mark'))

        self.obstree.grid(column=0,row=0)

        self.sbtree = ttk.Treeview(
            self.soundboard, columns=('midi', 'channel', 'code','path'))
        self.sbtree.heading("#0", text="Name", anchor=tkinter.W)
        self.sbtree.heading("midi", text="Midi Device", anchor=tkinter.W)
        self.sbtree.heading("channel", text="Channel", anchor=tkinter.W)
        self.sbtree.heading("code", text="Code", anchor=tkinter.W)
        self.sbtree.heading("path", text="Path", anchor=tkinter.W)

        self.sbtree.grid(column=0,row=0)

        self.btn = tkinter.Button(
            self.window, text="Connect", command=self.clicked)
        self.btn.grid(column=1, row=6)
        
        self.btn = tkinter.Button(
            self.window, text="Save Config", command=self.saveConfig)
        self.btn.grid(column=3, row=6)

        


def main():
    print('configuration directory is', confuse.config_dirs())
    config = confuse.Configuration('obs-midi-controller', __name__)
    OBSMidi(config)
