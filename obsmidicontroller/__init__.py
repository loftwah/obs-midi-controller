import os
import time
import tkinter
import tkinter.ttk

import confuse
import mido
import obswebsocket
import obswebsocket.requests
import yaml


class OBSMidi:
    client = None
    window = None
    controllers = None
    sceneBegin = 8
    config = None
    audiosources = None

    def __init__(self, config):
        self.config = config
        self.controllers = mido.get_input_names()
        print(self.controllers)
        self.initUI()
        self.port = mido.open_input(callback=self.print_message)
        self.window.mainloop()

    def initializeAudiosources(self):
        scenes = self.client.call(obswebsocket.requests.GetSceneList())
        print(scenes)
        for s in scenes.getScenes():
            name = s['name']
            print(name)
        print("----")
        sourcetypes = self.client.call(
            obswebsocket.requests.GetSourceTypesList())
        self.audiotypes = []
        for st in sourcetypes.getTypes():
            stcap = st['caps']
            typid = st['typeId']
            if stcap['hasAudio']:
                self.audiotypes.append(typid)
                print("%s (%s): %s" %
                      (st['displayName'], typid, stcap['hasAudio']))

    def initOBS(self, host, port, password):
        print(host)
        print(port)
        print(password)
        self.client = obswebsocket.obsws(host, port, password)
        self.client.connect()
        #self.client.register(self.obsevent)
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

    def print_message(self, message):
        if message.type == "note_on":
            print(message)
            if int(message.channel) == self.config['controller']['channel']['id'].get():
                scenedefs = self.config['controller']['notes']['scenes'].get()
                if message.note in scenedefs:
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
                reqdefs = self.config['controller']['notes']['recording'].get()
                if message.note in reqdefs:
                    self.client.call(
                        obswebsocket.requests.StartStopStreaming())
                streamdefs = self.config['controller']['notes']['streaming'].get(
                )
                if message.note in streamdefs:
                    self.client.call(
                        obswebsocket.requests.StartStopRecording())
                transdefs = self.config['controller']['notes']['transitions'].get(
                )
                if message.note in transdefs:
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
                mutedefs = self.config['controller']['audio']['mute'].get()
                if message.note in mutedefs:
                    audiosources=self.getAudioSourcesScene()
                    if mutedefs.index(message.note) < len(audiosources):
                        name = audiosources[mutedefs.index(message.note)]
                        self.client.call(
                            obswebsocket.requests.ToggleMute(name))
        elif message.type == "control_change":
            if int(message.channel) == self.config['controller']['channel']['id'].get():
                voldefs = self.config['controller']['audio']['vol'].get()
                if message.control in voldefs:
                    audiosources=self.getAudioSourcesScene()
                    if voldefs.index(message.control) < len(audiosources):
                        name = audiosources[voldefs.index(
                            message.control)]
                        self.client.call(obswebsocket.requests.SetVolume(
                            name, (float(message.value)/127.0)))
        else:
            print(message)

    def initUI(self):
        self.window = tkinter.Tk()
        self.window.title("OBS Midi Controller")

        self.window.geometry('350x200')
        self.hst = tkinter.StringVar()
        self.prt = tkinter.StringVar()
        self.pw = tkinter.StringVar()
        self.chnl = tkinter.StringVar()
        self.hst.set("localhost")
        self.prt.set("4444")
        self.pw.set("password")
        self.chnl.set("10")
        self.initOBS(self.hst.get(), self.prt.get(), self.pw.get())

        tkinter.Label(self.window, text="OBS Server").grid(column=0, row=0)

        tkinter.Label(self.window, text="host").grid(column=0, row=1)
        self.hstW = tkinter.Entry(self.window, width=10, textvariable=self.hst)
        self.hstW.grid(column=1, row=1)

        tkinter.Label(self.window, text="port").grid(column=2, row=1)
        self.prtW = tkinter.Entry(self.window, width=10, textvariable=self.prt)
        self.prtW.grid(column=3, row=1)

        tkinter.Label(self.window, text="password").grid(column=0, row=2)
        self.pwW = tkinter.Entry(self.window, width=10, textvariable=self.pw)
        self.pwW.grid(column=1, row=2)

        tkinter.Label(self.window, text="channel").grid(column=0, row=3)
        self.chnlW = tkinter.Entry(
            self.window, width=10, textvariable=self.chnl)
        self.chnlW.grid(column=1, row=3)

        self.btn = tkinter.Button(
            self.window, text="Connect", command=self.clicked)
        self.btn.grid(column=2, row=4)

        self.tree = tkinter.ttk.Treeview(
            self.window, columns=('size', 'modified', 'owner'))
        self.tree.heading("#0", text="Name", anchor=tkinter.W)
        self.tree.heading("size", text="Date modified", anchor=tkinter.W)
        self.tree.heading("modified", text="Type", anchor=tkinter.W)
        self.tree.heading("owner", text="Size", anchor=tkinter.W)
        self.tree.grid(column=1, row=5, columnspan=3)

        self.tree.insert('', 'end', 'widgets', text='Listbox',
                         values=('15KB Yesterday mark'))


def main():
    print('configuration directory is', confuse.config_dirs())
    print(__name__)
    config = confuse.Configuration('obs-midi-controller', __name__)
    print(config.modname)
    print(config._package_path)
    print(os.path.join(config._package_path, 'config_default.yaml'))
    print(config['version'])
    print(config['obsserver'])
    OBSMidi(config)
