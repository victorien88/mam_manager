
import xmlrpc.server
import subprocess
import re
import sys
import json
from PyQt5 import QtGui, QtCore
import os
from pony.orm import *
from .dataBase import *
import time
import pexpect
from pipes import quote



class Encoder(QtCore.QRunnable,QtCore.QObject):
    done = QtCore.pyqtSignal()
    updateProxStatut = QtCore.pyqtSignal(str,int)
    error = QtCore.pyqtSignal(str)
    def __init__(self,assetPath, cmd_withfiler, duration,asset, ppath,MainWindow,unquotedPath):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.assetPath = assetPath
        self.cmd_withfilter = cmd_withfiler
        self.ppath = ppath
        self.uppath=unquotedPath
        self.duration = duration
        self.asset = asset
        self.progress = QtGui.QProgressBar(MainWindow.sc_proxy)
        self.labprogress = QtGui.QLabel(MainWindow.sc_proxy)
        self.labprogress.setText("Encodage de %s - <i>sur la carte %s</i>"%(self.asset.name,self.asset.card.name))
        MainWindow.verticalLayout_22.addWidget(self.labprogress)
        MainWindow.verticalLayout_22.addWidget(self.progress)
        self.progress.setObjectName(str(self.asset.id))
        self.labprogress.setObjectName(str(self.asset.id))
        self.pgname = str(self.asset.id)
        print('init')


    def finish_conversion(self, stat):
        if not stat:
            with db_session:
                ass = get(a for a in Assets if a == self.asset_)
                try:
                        while not os.path.exists(self.uppath):
                            time.sleep(1)
                            print("---------- bloque  :::::::::: %s " %self.asset_.proxyPath)
                        ass.progression = 100
                        ass.stat = 3
                        ass.hasProxy = True
                        print ("----- optimizing header")
                        subprocess.call(["qtfaststart", self.uppath])
                        print ("------optimizing done")
                        print ("------generating thumnail")

                        imgfile = self.uppath+".jpg"

                        subprocess.call(["ffmpegthumbnailer", "-i", self.uppath, '-o', imgfile])

                        print("generating %s proxy done !"%self.asset_.name)
                        self.progress.deleteLater()
                        self.labprogress.deleteLater()
                        self.done.emit()
                        commit()


                except:
                        self.found_error()
        else:
            self.found_error()
        return

    def found_error(self):
        with db_session:
            ass = get(a for a in Assets if a == self.asset_)
            print(sys.exc_info())
            ass.progression = 100
            ass.stat = 2
            ass.hasProxy = False
            print ("------ AN ERROR HAS OCCURED IN CONVERSION")
            print("generating %s proxy error !"%self.asset_.name)
            self.progress.deleteLater()
            self.error.emit(str(self.asset.id))
            commit()



    def run(self):
        print('run')

        #card.locked = True
        with db_session:
            self.asset_= get(a for a in Assets if a == self.asset)
            print("generating proxy %s"%self.asset_.name)
            thread2 = pexpect.spawn(self.cmd_withfilter)

            cpl = thread2.compile_pattern_list([
                    pexpect.EOF,
                    "frame= *\d+", '(.+)'])
            get(a for a in Assets if a == self.asset_).stat = 2
            commit()
        while True:

                i = thread2.expect_list(cpl, timeout=None)

                if i == 0:  # EOF
                            stat = thread2.exitstatus
                            break

                elif i == 1:

                    frame_number = thread2.match.group(0)
                    #try :
                    a = re.findall(r'\b\d+\b', frame_number)


                    prog = int(int(a[0])/int(self.duration)*100)
                    self.updateProxStatut.emit(self.pgname,prog)



                elif i == 2:
                    unknown_line = thread2.match.group(0)
                    #print unknown_line
        self.finish_conversion(stat)




class EncodeFunction:

    def __init__(self,MainWindow):
        self.threads = 0
        self.pool = QtCore.QThreadPool()
        self.MainWindow = MainWindow


    def start_thread(self,th):
        print('istart')
        self.pool.globalInstance().start(th)



    def get_v_size(self,size):
        '''
        Return x y 1920 X 1080 + fontsize
        :param size:
        :return:
        '''
        return int(size.split(" X ")[0])/2,int(size.split(" X ")[1])/20,int(size.split(" X ")[1])*0.08
    @db_session
    def addEncoder(self,id,proxyDrive):
        print("### ENCODER LANCHED ###")

        card = get(c for c in Cards if c.id == id)
        print(card)
        print(proxyDrive)
        out_dir = "%s/%s"%(proxyDrive,card.id)
        print(out_dir)
        assets = card.child
        try :
            os.mkdir(out_dir)
        except:
            print(sys.exc_info())




        for asset in assets:

            if not asset.nb_audio_stream == 0:
                amix="-filter_complex amix=%s"%asset.nb_audio_stream
            else:
                amix = ""
            assetPath = "%s/%s/%s%s"%(Raid[0].mountPoint,asset.card.id,asset.card.firsName,asset.clipPath)
            print(assetPath, "path")
            tc = asset.timeCode.split(":")
            x,y,font = self.get_v_size(asset.videoSize)
            cmd_withfilter = """ffmpeg -y %s -i %s\
            -vcodec libx264 -s 480*270  -acodec aac -strict -2 -b:a 64k -b:v 300k  %s \
            -movflags +faststart  -pix_fmt yuv420p -threads 1  \
            -vf drawtext="fontsize=%s:fontfile=DroidSansMono.ttf:\
            timecode='%s\:%s\:%s\:%s':rate=%s:text='FC' TCR:':\
            fontsize=%s:fontcolor='white':boxcolor=0x000000AA:\
            box=1:x=%s-text_w/2:y=%s" %s %s"""%("-loop 1 -i audio.jpg" if asset.card.audio else "", quote(assetPath),
                                             amix,int(font),tc[0],tc[1],tc[2],tc[3],str(asset.videoFps),int(font),x,y,
                                             "-shortest" if asset.card.audio else "",quote("%s/%s.mp4"%(out_dir,asset.name)))
            print(cmd_withfilter)
            duration = asset.durationFrm
            asset.stat = 1
            asset.proxyPath = quote("%s/%s.mp4"%(out_dir,asset.name))
            a = Encoder(assetPath,cmd_withfilter,duration,asset,quote("%s/%s.mp4"%(out_dir,asset.name)),self.MainWindow,"%s/%s.mp4"%(out_dir,asset.name))
            a.updateProxStatut[str,int].connect(self.updatePGBcopy)
            a.error[str].connect(self.error)
            a.done.connect(self.done)
            self.MainWindow.lab_proxy.setVisible(False)
            self.threads = self.threads +1
            self.pool.globalInstance().start(a, 0)
            commit()


        return "go"
    def done(self):
        self.threads = self.threads - 1
        if self.threads == 0:
            self.MainWindow.lab_proxy.setVisible(True)
        return


    def error(self,name):
        label = self.MainWindow.sc_proxy.findChild(QtGui.QLabel,name)

        label.setText(label.text()+" ERROR !")


    def updatePGBcopy(self,name,value):
            print(name)
            progBar = self.MainWindow.sc_proxy.findChild(QtGui.QProgressBar,name)
            progBar.setValue(value)

    def fixProxies(self):
        print("test")
        with db_session:
            clips = select(c for c in Assets if c.hasProxy == False and c.card.copied == True)
            try :
                proxyDrive = get(p for p in ProxyDrive if p.default == True)
            except:
                print("error in proxy drive")
                return


        th = {}
        i=0
        #cmd_withfilter = """ffmpeg -y -i '/Volumes/Image disque/32/2014_03_30_Lyon_SXS13eqd/Clip/458_1196.MXF' -vcodec
        # libx264 -s 480*270  -acodec aac -strict -2 -b:a 64k -b:v 150k
        #    -movflags +faststart  -pix_fmt yuv420p -threads 1 '/Users/victorientronche/proxy/32/458_1196.MXF.mp4'"""

        #duration = 9.240000 *25
        #a =
        #self.start_thread(Encoder('/Volumes/Image disque/32/2014_03_30_Lyon_SXS13eqd/Clip/458_1196.MXF' ,
        # cmd_withfilter,duration))
        #return
        with db_session:

            for asset in clips:


                out_dir = "%s/%s"%(proxyDrive.path,asset.card.id)
                print(out_dir)
                try :
                    os.mkdir(out_dir)
                    os.remove("%s/%s"%(out_dir,asset.name))
                except:
                    print(sys.exc_info())

                x,y, font = self.get_v_size(asset.videoSize)
                tc = asset.timeCode.split(":")
                assetPath = "%s/%s/%s%s"%(Raid[0].mountPoint,asset.card.id,asset.card.firsName,asset.clipPath)


                if not asset.nb_audio_stream == 0:
                    amix="-filter_complex amix=%s"%asset.nb_audio_stream
                else:
                    amix = ""
                cmd_withfilter = """ffmpeg -y %s -i  %s\
                -vcodec libx264 -s 480*270  -acodec aac -strict -2 %s -b:a 64k -b:v 300k \
                -movflags +faststart  -pix_fmt yuv420p -threads 1  \
                -vf drawtext="fontsize=%s:fontfile=DroidSansMono.ttf:\
                timecode='%s\:%s\:%s\:%s':rate=%s:text='FC' TCR:':\
                fontsize=%s:fontcolor='white':boxcolor=0x000000AA:\
                box=1:x=%s-text_w/2:y=%s" %s %s"""%("-loop 1 -i audio.jpg" if asset.card.audio else "",quote(assetPath),
                                                 amix,int(font),tc[0],tc[1],tc[2],tc[3],str(asset.videoFps),int(font),
                                                 x,y,"-shortest" if asset.card.audio else "",
                                                 quote("%s/%s.mp4"%(out_dir,asset.name)))
                print(cmd_withfilter)
                duration = asset.durationFrm
                asset.stat = 1
                asset.proxyPath = "%s/%s.mp4"%(out_dir,asset.name)
                asset.proxyDisk = proxyDrive
                a = Encoder(assetPath,cmd_withfilter,duration,asset,quote("%s/%s.mp4"%(out_dir,asset.name)),self.MainWindow,"%s/%s.mp4"%(out_dir,asset.name))
                a.updateProxStatut[str,int].connect(self.updatePGBcopy)
                a.done.connect(self.done)
                a.error[str].connect(self.error)
                self.MainWindow.lab_proxy.setVisible(False)
                self.threads = self.threads +1
                self.pool.globalInstance().start(a, 0)
                commit()
        return "go"
