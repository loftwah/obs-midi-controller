import mido
import obswebsocket, obswebsocket.requests
import time
import tkinter
import confuse
import tkinter.ttk

class OBSMidi:
  client=None
  window=None
  sceneBegin=8

  def __init__(self):
      print(mido.get_input_names())
      self.initUI()
      self.port = mido.open_input(callback=self.print_message)
      self.window.mainloop()
    
  def initOBS(self,host,port,password):
    print(host)
    print(port)
    print(password)
    self.client = obswebsocket.obsws(host,port,password)
    self.client.connect()
    self.client.register(self.obsevent)
    scenes=self.client.call(obswebsocket.requests.GetSceneList())
    print(scenes)
    for s in scenes.getScenes():
      name=s['name']
      print(name)
    print("----")
    sourcetypes=self.client.call(obswebsocket.requests.GetSourceTypesList())
    audiotypes=[]
    for st in sourcetypes.getTypes():
      stcap=st['caps']
      typid=st['typeId']
      if stcap['hasAudio']:
        audiotypes.append(typid)
        print("%s (%s): %s" % (st['displayName'],typid,stcap['hasAudio']))
    sources=self.client.call(obswebsocket.requests.GetSourcesList())
    print('-------')
    for s in sources.getSources():
      name=s['name']
      typ=s['type']
      typid=s['typeId']
      if typid in audiotypes:
        print(s)
        print("%s: %s (%s)" % (name,typ,typid))
        vol=self.client.call(obswebsocket.requests.GetVolume(name))
        print(vol)


  def obsevent(self,event):
    print(event)
  
  def clicked(self):
      self.initOBS(self.hst.get(),self.prt.get(),self.pw.get())

  def print_message(self,message):
    print(message)
    print(message.channel)
    print(message.note)
    if (message.note>=self.sceneBegin):
      status=self.client.call(obswebsocket.requests.GetStudioModeStatus())
      scenes=self.client.call(obswebsocket.requests.GetSceneList()).getScenes()
      name=scenes[message.note-self.sceneBegin]['name']
      print(u"Switching to {}".format(name))
      if status.getStudioMode():
        self.client.call(obswebsocket.requests.SetPreviewScene(name))
      else:
        self.client.call(obswebsocket.requests.SetCurrentScene(name))


  def initUI(self):
      self.window = tkinter.Tk()
      self.window.title("OBS Midi Controller")

      self.window.geometry('350x200')
      self.hst=tkinter.StringVar()  
      self.prt=tkinter.StringVar()  
      self.pw=tkinter.StringVar()  
      self.chnl=tkinter.StringVar()  
      self.hst.set("localhost")
      self.prt.set("4444")
      self.pw.set("password")
      self.chnl.set("10")


      tkinter.Label(self.window, text="host").grid(column=0, row=0)
      self.hstW = tkinter.Entry(self.window,width=10,textvariable=self.hst)
      self.hstW.grid(column=1, row=0)

      tkinter.Label(self.window, text="port").grid(column=2, row=0)
      self.prtW = tkinter.Entry(self.window,width=10,textvariable=self.prt)
      self.prtW.grid(column=3, row=0)

      tkinter.Label(self.window, text="password").grid(column=0, row=1)
      self.pwW = tkinter.Entry(self.window,width=10,textvariable=self.pw)
      self.pwW.grid(column=1, row=1)

      self.btn = tkinter.Button(self.window, text="Connect", command=self.clicked)
      self.btn.grid(column=2,row=2)

      tkinter.Label(self.window, text="channel").grid(column=0, row=4)
      self.chnlW = tkinter.Entry(self.window,width=10,textvariable=self.chnl)
      self.chnlW.grid(column=1, row=4)

if __name__ == "__main__":
    # execute only if run as a script
    OBSMidi()