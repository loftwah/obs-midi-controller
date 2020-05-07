import os
import time
import tkinter
import tkinter.ttk as ttk
from PIL import Image, ImageTk


import confuse
import mido
import obswebsocket
import obswebsocket.requests
import yaml
import pygame.mixer as mixer
import math
import importlib
import obsmidicontroller.macro

class OBSMidi:
    client = None
    window = None
    controller = None
    config = None
    audiosources = None
    port=None
    outport=None
    page=0
    mode=None
    transdefs=None

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
        if self.controller:
            self.mode=self.controller['defaultmode'].get()
            print("mode set to: %s"%self.mode)
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
        self.client.register(self.newtreeobsevent,obswebsocket.events.ScenesChanged)
        self.client.register(self.newtreeobsevent,obswebsocket.events.SceneCollectionChanged)
        self.client.register(self.newtreeobsevent,obswebsocket.events.SceneCollectionListChanged)
        self.client.register(self.newtreeobsevent,obswebsocket.events.ProfileChanged)
        self.client.register(self.newtreeobsevent,obswebsocket.events.ProfileListChanged)
        self.client.register(self.newtreeobsevent,obswebsocket.events.TransitionListChanged)


        self.initializeAudiosources()

    def newtreeobsevent(self,event):
        print("^%$^%$^%$^ tree updating *(*(&^*&^*&^")
        self.window.after(1,self.updateObsTree)

    def obsevent(self, event):
        print(event)
        self.audiosources=None

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

    def modeChanged(self,mode):
        def modeChangedHandler():
            print(mode)
            self.mode=mode
            self.updateObsTree()
        return modeChangedHandler

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

    def handleTransitions(self,i):
        status = self.client.call(
            obswebsocket.requests.GetStudioModeStatus())
        print(i)
        print(self.transdefs)
        print(i in self.transdefs)
        if i in self.transdefs:
            name = self.transdefs[i]
            print(name)
            self.client.call(
                obswebsocket.requests.SetCurrentTransition(name))
            if status.getStudioMode():
                self.client.call(
                    obswebsocket.requests.TransitionToProgram(name))

    def playSoundboard(self,fle):
        mixer.music.load(fle)
        mixer.music.play()

    def doMacro(self,m):
        macroObj=obsmidicontroller.macro.macro()
        for s in m['steps']:
            print("---")
            print(s)
            print(s['command'])
            method = getattr(obsmidicontroller.macro.macro,s['command'])
            print(method)
            kwargs=s.copy()
            del kwargs['command']
            print(kwargs)
            method(macroObj,self.client, **kwargs)

    def handleMidiMessage(self, message):
        self.outport.send(message)
        if message.type == "note_on":
            print(message)
            if int(message.channel) == self.controller['channel'].get():
                try:
                    scenedefs = self.controller['modes'][self.mode]['notes']['scenes'].get()
                    if message.note in scenedefs:
                        self.handleSceneChange(message,scenedefs)
                except:
                    pass
                try:
                    reqdefs = self.controller['modes'][self.mode]['notes']['recording'].get()
                    if message.note in reqdefs:
                        self.handleRecording()
                except:
                    pass
                try:
                    streamdefs = self.controller['modes'][self.mode]['notes']['streaming'].get(
                    )
                    if message.note in streamdefs:
                        self.handleStreaming()
                except:
                    pass
                try:
                        self.handleTransitions(message.note)
                except:
                    pass
                try:
                    soundboard = self.controller['modes'][self.mode]['soundboard'].get()
                    print(soundboard)
                    for i in soundboard:
                        if message.note==i['id']:
                            print(i['file'])
                            self.playSoundboard(i['file'])
                except:
                    pass
                try:
                    macro = self.controller['modes'][self.mode]['macros'].get()
                    print(macro)
                    for i in macro:
                        if message.note==i['id']:
                            self.doMacro(i)
                except:
                    pass
        else:
            print(message)

    def saveConfig(self):
        pass

    def updateObsTree(self):
        try:
            self.obstree.delete('scenes')
        except:
            pass
        try:
            self.obstree.delete('transitions')
        except:
            pass
        try:
            self.obstree.delete('recording')
        except:
            pass
        try:
            self.obstree.delete('streaming')
        except:
            pass

        self.sbtree.delete(*self.sbtree.get_children())
        self.macrotree.delete(*self.macrotree.get_children())

        try:
            scenes = self.client.call( obswebsocket.requests.GetSceneList()).getScenes()
            scenedefs=self.controller['modes'][self.mode]['notes']['scenes'].get()
            self.obstree.insert('', 'end', 'scenes', text='Scenes',open=True)
            for i in scenedefs:
                index=scenedefs.index(i)
                if index<len(scenes):
                    name = scenes[index]['name']
                    self.obstree.insert('scenes', 'end', name, text=name,
                                values=(self.midiin.get(),self.chnl.get(),i))
        except Exception as e:
            print(e)
            pass

        try:
            trans = self.client.call(
                obswebsocket.requests.GetTransitionList()).getTransitions()
            transconfig = self.controller['modes'][self.mode]['notes']['transitions'].get(
                    )
            self.obstree.insert('', 'end', 'transitions', text='Transitions',open=True)
            
            ind=0
            self.transdefs={}
            inserted=[]
            for i in transconfig:
                print(i)
                print(i['id'])

                if 'name' in i:
                    name=i['name']
                    inserted.append(name)
                    self.transdefs[i['id']]=name
                    self.obstree.insert('transitions', 'end', name, text=name,
                                    values=(self.midiin.get(),self.chnl.get(),i['id']))                    
                else:
                    if ind<len(trans):
                        while True:
                            name=trans[ind]['name']
                            print(name)
                            print(inserted)
                            print(ind)
                            ind+=1
                            if not name in inserted:
                                break
                        inserted.append(name)
                        self.transdefs[i['id']]=name

                        print("inserting: %s"%name)
                        self.obstree.insert('transitions', 'end', name, text=name,
                                    values=(self.midiin.get(),self.chnl.get(),i['id']))                    
        except Exception as e:
            print(e)
            pass

        try:
            reqdefs = self.controller['modes'][self.mode]['notes']['recording'].get()
            self.obstree.insert('', 'end', 'recording', text='Recording',open=True)
            for i in reqdefs:
                name="req-%s"%i
                self.obstree.insert('recording', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i))
        except Exception as e:
            print(e)
            pass

        try:
            strmdefs = self.controller['modes'][self.mode]['notes']['streaming'].get()
            self.obstree.insert('', 'end', 'streaming', text='Streaming',open=True)
            for i in strmdefs:
                name="strm-%s"%i
                self.obstree.insert('streaming', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i))
        except Exception as e:
            print(e)
            pass

        try:
            sounddefs=self.controller['modes'][self.mode]['soundboard'].get()
            for i in sounddefs:
                name=i['name']
                self.sbtree.insert('', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i['id'],i['file']))
        except Exception as e:
            print(e)
            pass
        try:
            macdefs=self.controller['modes'][self.mode]['macros'].get()
            for i in macdefs:
                name=i['name']

                self.macrotree.insert('', 'end', name, text=name,
                            values=(self.midiin.get(),self.chnl.get(),i['id'],i['description']))
        except Exception as e:
            print(e)
            pass

    def mouseClick(self,event):
        print(event)

    def initUI(self):
        self.window = tkinter.Tk()
        self.window.title("OBS Midi Controller")
        self.initController()

        self.mainui = ttk.Notebook(self.window)
        self.obsconf = ttk.Frame(self.mainui)   # first page, which would get widgets gridded into it
        self.midiconf = ttk.Frame(self.mainui)   # second page
        self.mainui.add(self.midiconf, text='MIDI Interface')
        self.mainui.add(self.obsconf, text='OBS Configuration')
        self.mainui.pack()

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

        tkinter.Label(self.obsconf, text="Host").grid(column=0, row=1, sticky='w', padx=5, pady=5)
        self.hstW = tkinter.Entry(self.obsconf, width=10, textvariable=self.hst)
        self.hstW.grid(column=1, row=1,sticky="we", padx=5, pady=5)

        tkinter.Label(self.obsconf, text="Port").grid(column=2, row=1, sticky='w', padx=5, pady=5)
        self.prtW = tkinter.Entry(self.obsconf, width=10, textvariable=self.prt)
        self.prtW.grid(column=3, row=1,sticky="we", padx=5, pady=5)

        tkinter.Label(self.obsconf, text="Password").grid(column=0, row=2, sticky='w', padx=5, pady=5)
        self.pwW = tkinter.Entry(self.obsconf, width=10, textvariable=self.pw)
        self.pwW.grid(column=1, row=2,sticky="we", padx=5, pady=5)


        tkinter.Label(self.midiconf, text="Midi Output").grid(column=0, row=1, sticky='w', padx=5, pady=5)
        self.midioutCombo=tkinter.ttk.Combobox(self.midiconf,textvariable=self.midiout)

        self.midioutCombo.grid(column=1,row=1,sticky="we", padx=5, pady=5)
        self.midioutCombo['values'] = mido.get_output_names()

        tkinter.Label(self.midiconf, text="Midi Input").grid(column=2, row=1, sticky='w', padx=5, pady=5)
        self.midiinCombo=tkinter.ttk.Combobox(self.midiconf,textvariable=self.midiin)

        self.midiinCombo.grid(column=3,row=1,sticky="we", padx=5, pady=5)
        self.midiinCombo['values'] = mido.get_input_names()

        tkinter.Label(self.midiconf, text="Input Channel").grid(column=2, row=2, sticky='w', padx=5, pady=5)
        self.chnlW = tkinter.Entry(
            self.midiconf, width=10, textvariable=self.chnl)
        self.chnlW.grid(column=3, row=2,sticky="we", padx=5, pady=5)


        load = Image.open(".\X-TOUCH-MINI.png")
        render = ImageTk.PhotoImage(load)

        self.img = tkinter.Label(self.midiconf, image=render)
        self.img.image=render
        self.img.grid(column=0, columnspan=5, row=3, padx=5, pady=5)
        self.img.bind( "<Button>", self.mouseClick )


        print("Working on Control buttons")
        lf = ttk.Labelframe(self.midiconf, text='Control Modes')
        print("modes ----")
        print(self.controller['modes'])
        for m in self.controller['modes']:
            print("----")
            print(m)
            print(self.controller['modes'][m])
            print(self.controller['modes'][m]['name'])
            btn=tkinter.Button(lf, text=self.controller['modes'][m]['name'], command=self.modeChanged(m))
            btn.pack(side=tkinter.LEFT, padx=5, pady=5)
        lf.grid(column=0, columnspan=5,row=4,sticky='we')
        print("----modes")


        self.n = ttk.Notebook(self.midiconf)
        self.obs = ttk.Frame(self.n)   # first page, which would get widgets gridded into it
        self.soundboard = ttk.Frame(self.n)   # second page
        self.macro = ttk.Frame(self.n)   # second page
        self.n.add(self.obs, text='OBS Controls')
        self.n.add(self.soundboard, text='Soundboard')
        self.n.add(self.macro, text='Macros')
        self.n.grid(column=0, row=5, columnspan=6,sticky="we", padx=5, pady=5)

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

        self.obstree.grid(column=0,row=0,sticky='nsew')

        self.sbtree = ttk.Treeview(
            self.soundboard, columns=('midi', 'channel', 'code','path'))
        self.sbtree.heading("#0", text="Name", anchor=tkinter.W)
        self.sbtree.heading("midi", text="Midi Device", anchor=tkinter.W)
        self.sbtree.heading("channel", text="Channel", anchor=tkinter.W)
        self.sbtree.heading("code", text="Code", anchor=tkinter.W)
        self.sbtree.heading("path", text="Path", anchor=tkinter.W)

        self.sbtree.grid(column=0,row=0,sticky='nsew')

        self.macrotree = ttk.Treeview(
            self.macro, columns=('midi', 'channel', 'code','description'))
        self.macrotree.heading("#0", text="Name", anchor=tkinter.W)
        self.macrotree.heading("midi", text="Midi Device", anchor=tkinter.W)
        self.macrotree.heading("channel", text="Channel", anchor=tkinter.W)
        self.macrotree.heading("code", text="Code", anchor=tkinter.W)
        self.macrotree.heading("description", text="Description", anchor=tkinter.W)

        self.macrotree.grid(column=0,row=0,sticky='nsew')


def main():
    print('configuration directory is', confuse.config_dirs())
    config = confuse.Configuration('obs-midi-controller', __name__)
    OBSMidi(config)
