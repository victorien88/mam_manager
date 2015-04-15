# -*- coding: utf-8 -*-

__author__ = 'fcp6'
import time
from .ffprober import FFProber, AudioFFprober, ZeroTimecodeError,ZeroDimentionError,\
    ZeroAudioTrackError,ZeroDurationError,ZeroFpsError,ZeroVideoCodecError,NoVideoFileError
from PyQt5 import QtGui, QtCore
from .dataBase import *
from .customWidgets import ProgressWidget
import time
import logging
logging.basicConfig( format='%(asctime)s %(message)s', level=logging.DEBUG)


class Analyzer(QtCore.QObject,QtCore.QRunnable):
    updateStatut = QtCore.pyqtSignal(int)
    cancelled = QtCore.pyqtSignal()
    started = QtCore.pyqtSignal()
    paused = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str,)
    review = QtCore.pyqtSignal(dict)
    def __init__(self, card,clips, ville, pays,objectdrive,mode, xpath,audio):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.audio = audio
        self.card = card
        self.stopped = False
        self.paused = False
        self.objectdrive = objectdrive
        self.ville = ville
        self.pays = pays
        self.id = card.id
        self.name = card.name
        self.clips = clips
        self.mode = mode
        self.xpath = xpath
        self.pgname = self.card.name


    def cancel(self):
        self.stopped = True

    def pause(self,stat):
        self.paused = stat


    def run(self):
        self.started.emit()
        if self.audio:
            self.analyse_audio()
        else:
            self.analyse_video()

    def analyse_audio(self):
        with db_session:
            i = 0
            card = Cards[self.id]
            print("#### CHECKING RUSHES ON CARD %s ####"%(self.id))
            card.stat = 0
            warning = False
            error = False
            self.pre_processing = []
            for clip in self.clips:
                    _clip = {'name':clip[1], "tag" : clip[2], "comment" : clip[3], "error": False,
                             "clipPath" : clip[0].replace(self.card.originalPath,'')}
                    if self.paused:
                        while self.paused:
                            time.sleep(1)

                    if self.stopped:
                        print("#### DELETING CARD %s ###"%(self.id))
                        oldfree = card.disk.free
                        card.disk.free = str(int(oldfree)-int(card.poids))
                        card.delete()
                        self.cancelled.emit(card.name)
                        return
                    else:
                        i += 1
                        self.updateStatut.emit(i/len(self.clips)*100)
                        try:
                            mdata = AudioFFprober(clip[0],self.mode,self.xpath)
                        except NoVideoFileError:
                            error = True
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible d'analyser le clip %s. " \
                                                  "Aucune piste audio ou vidéo. Soit le fichier est corrompu " \
                                                  "soit il ne s'agit pas d'un fichier vidéo. Le fichier sera quand même sauvegardé," \
                                                  " mais ils ne sera pas ajouté à la base de données" % clip[1]
                            self.pre_processing.append(_clip)
                            continue

                        try:
                            _clip['duration'] = mdata.get_duration_sec()
                        except ZeroDurationError:
                            error = True
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Le fichier a un durée nulle %s. " \
                                                  "Soit le fichier est corrompu " \
                                                  "soit il ne s'agit pas d'un fichier audio. Le fichier sera quand même sauvegardé," \
                                                  " mais ils ne sera pas ajouté à la base de données" %clip [1]
                            self.pre_processing.append(_clip)
                            continue
                        try:
                            _clip['codec'] = mdata.get_audio_codec()
                        except ZeroVideoCodecError:
                            error = True
                            codec = "NA"
                            logging.warning("can't get codec of %s"%clip[0])
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible de déterminer les codec du clip %s. " \
                                                  "Le fichier sera  sauvegardé, mais il ne sera pas ajouté à la base de données"%clip [1]
                            self.pre_processing.append(_clip)
                            continue
                        _clip['size']="1920 X 1080"
                        _clip['fps']= str(mdata.get_video_fps())
                        _clip['timecode'] = "00:00:00:00"
                        try:
                            _clip['audiostr']= mdata.get_audio_tracks_nb()
                        except ZeroAudioTrackError:
                            warning = True
                            _clip['audiostr']=0
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible de lire les pistes audio du clip %s. " \
                                                  "Soit le fichier ne dispose d'aucune piste audio " \
                                                  "soit MaMManager n'est pas parvenu à les indentifier. Le fichier ne sera " \
                                                  "ajouté à la base de données, mais il sera sauvegardé."%clip [1]


                        _clip['comment']= mdata.get_mdata()
                        _clip['pays'] = self.pays
                        _clip["ville"] = self.ville


                        self.pre_processing.append(_clip)
            self.review.emit({"id":card.id, "name":card.name, "clips":self.pre_processing,
                              "audio":True,"all_ok":False if error or warning else True,"proxy":self.objectdrive})

    def analyse_video(self):
        with db_session:
            i = 0
            card = Cards[self.id]
            print("#### CHECKING RUSHES ON CARD %s ####"%(self.id))
            card.stat = 0
            warning = False
            error = False
            self.pre_processing = []
            for clip in self.clips:
                    _clip = {'name':clip[1], "tag" : clip[2], "comment" : clip[3], "error": False,
                             "clipPath" : clip[0].replace(self.card.originalPath,'')}

                    if self.paused:
                        while self.paused:
                            time.sleep(1)

                    if self.stopped:
                        print("#### DELETING CARD %s ###"%(self.id))
                        oldfree = card.disk.free
                        card.disk.free = str(int(oldfree)-int(card.poids))
                        card.delete()
                        self.cancelled.emit()
                        return
                    else:
                        i += 1
                        self.updateStatut.emit((i/len(self.clips))*100)
                        try:
                            mdata = FFProber(clip[0],self.mode,self.xpath)
                        except NoVideoFileError:
                            error = True
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible d'analyser le clip %s. " \
                                                  "Aucune piste audio ou vidéo. Soit le fichier est corrompu " \
                                                  "soit il ne s'agit pas d'un fichier vidéo. Le fichier sera quand même sauvegardé," \
                                                  " mais ils ne sera pas ajouté à la base de données" % clip[1]
                            self.pre_processing.append(_clip)
                            continue

                        try:
                            _clip['duration'] = mdata.get_duration_sec()
                        except ZeroDurationError:
                            error = True
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Le fichier vidéo a un durée nulle %s. " \
                                                  "Soit le fichier est corrompu " \
                                                  "soit il ne s'agit pas d'un fichier vidéo. Le fichier sera quand même sauvegardé," \
                                                  " mais ils ne sera pas ajouté à la base de données" %clip [1]
                            self.pre_processing.append(_clip)
                            continue
                        try:
                            _clip['codec'] = mdata.get_video_codec()
                        except ZeroVideoCodecError:
                            error = True
                            codec = "NA"
                            logging.warning("can't get codec of %s"%clip[0])
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible de déterminer les codec du clip %s. " \
                                                  "Le fichier sera  sauvegardé, mais il ne sera pas ajouté à la base de données"%clip [1]
                            self.pre_processing.append(_clip)
                            continue
                        try:
                            _clip['size']=mdata.get_video_size()
                        except ZeroDimentionError:
                            error = True
                            logging.warning("can't get video size of %s"%clip[0])
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible de déterminer la taille de l'image du clip %s. " \
                                                  "Le fichier sera  sauvegardé, mais il ne sera pas ajouté à la base de données"%clip [1]
                            self.pre_processing.append(_clip)
                            continue
                        try:
                            _clip['fps']= mdata.get_video_fps()
                        except ZeroFpsError:
                            error = True
                            #self.error.emit(u"Impossible de determiner le framerate de %s"%clip[1], card.id)
                            logging.warning("can't get fps of %s"%clip[0])

                            logging.warning("can't get video size of %s"%clip[0])
                            _clip['error'] = True
                            _clip['error-type'] = "fatal"
                            _clip['error-desc'] = "Impossible de déterminer le framerate du clip %s. " \
                                                  "Le fichier sera  sauvegardé, mais il ne sera pas ajouté à la base de données"%clip [1]
                            self.pre_processing.append(_clip)
                            continue

                        try:

                            _clip['timecode'] = mdata.get_time_code()
                        except ZeroTimecodeError:
                            warning = True
                            _clip['error'] = True
                            _clip['error-type'] = "warning"
                            _clip['error-desc'] = "Impossible de déterminer le timecode du clip %s. " \
                                                  "Soit le fichier ne dispose d'aucune information de timecode "  \
                                                  "soit MaMManager n'est pas parvenu à l'indentifier. Le fichier sera " \
                                                  "ajouté à la base de données, mais sont timecode commencera à 01:00:00:00"%clip [1]
                            _clip['timecode'] = "01:00:00:00"
                            logging.warning("can't get timecode of %s"%clip[0])

                        try:

                            _clip['audiostr']= mdata.get_audio_tracks_nb()
                        except ZeroAudioTrackError:
                            warning = True
                            _clip['audiostr']=0
                            _clip['error'] = True
                            _clip['error-type'] = "warning"
                            _clip['error-desc'] = "Impossible de lire les pistes audio du clip %s. " \
                                                  "Soit le fichier ne dispose d'aucune piste audio " \
                                                  "soit MaMManager n'est pas parvenu à les indentifier. Le fichier sera " \
                                                  "ajouté à la base de données, mais il n'aura pas de son."%clip [1]

                        _clip["pays"] = self.pays
                        _clip["ville"] = self.ville
                        self.pre_processing.append(_clip)

        self.review.emit({"id":card.id, "name":card.name, "clips":self.pre_processing,"audio":False,
                          "all_ok":False if error or warning else True, "proxy":self.objectdrive})


class AnalyseFunction:
    def __init__(self,copier,MainWin,selection):
        self.threads = 0
        self.pool = QtCore.QThreadPool()
        self.copier =  copier
        self.MainWin = MainWin
        self.selection = selection
        self.proxyDrive = None

    def addClips(self,card,clips,ville, pays, proxyDrive,mode,xpath,audio):
        self.proxyDrive = proxyDrive
        objectdrive = get(p for p in ProxyDrive if p.path == proxyDrive)
        with db_session:
            card = get(c for c in Cards if c == card)
            name = card.firsName
        newThread = Analyzer(card,clips, ville, pays,objectdrive,mode, xpath,audio)
        progressWidget = ProgressWidget(self.MainWin.sc_copy,card,"analyse")
        self.MainWin.verticalLayout_15.addWidget(progressWidget)
        newThread.updateStatut[int].connect(progressWidget.setProgress, QtCore.Qt.QueuedConnection)
        newThread.review[dict].connect(progressWidget.review)
        newThread.cancelled.connect(progressWidget.raise_stopped)
        newThread.started.connect(progressWidget.started)
        newThread.error[str].connect(progressWidget.raise_error)
        progressWidget.paused_sig[bool].connect(newThread.pause)
        progressWidget.stopped_click.connect(newThread.cancel)
        progressWidget.stopped[int].connect(self.cancelled)
        progressWidget.error[int,str].connect(self.error_handler)
        progressWidget.done[int].connect(self.done)
        self.threads = self.threads + 1
        self.MainWin.lab_analyse.setVisible(False)
        self.pool.globalInstance().start(newThread,3)
        return

    def done(self,id):
        self.copier.addCopy(id,self.proxyDrive)
        self.threads = self.threads - 1
        self.selection.reInitProjects()
        if self.threads == 0:
                self.MainWin.lab_analyse.setVisible(True)
        return

    def cancelled(self, name):
            self.threads = self.threads - 1
            if self.threads == 0:
                self.MainWin.lab_analyse.setVisible(True)
                self.MainWin.selection.reInitProjects()


    def error_handler(self,id,msg):
        ok = QtGui.QMessageBox(QtGui.QMessageBox.Critical,"Erreur",
                                      str("Error"),
                                      QtGui.QMessageBox.Ok)
        ok.setInformativeText(str(msg))
        ok.exec_()
        with db_session:
            card = Cards[id]
            oldfree = card.disk.free
            card.disk.free = str(int(oldfree)-int(card.poids))
            card.delete()
        self.MainWin.selection.reInitProjects()