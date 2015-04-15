# -*- coding: utf-8 -*-


__author__ = 'fcp6'
import hashlib
import shutil
import binascii
# from https://libbits.wordpress.com/2011/04/09/get-total-rsync-progress-using-python/

from PyQt5 import QtGui, QtCore
import os
from pony.orm import *
from .dataBase import *
import time
from .customWidgets import ProgressWidget
import shutil

class RsyncThread(QtCore.QObject,QtCore.QRunnable):
    done = QtCore.pyqtSignal()
    updateStatut = QtCore.pyqtSignal(int)
    cancelled = QtCore.pyqtSignal()
    started = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    ##### TO DO : add cancel and erase data
    def __init__(self, folderToCopy, destFolder,name):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.folderToCopy = folderToCopy
        self.destFolder = destFolder
        self.read = 0
        self.total = 0
        self.card = name
        self.stopped = False
        self.paused = False
        self.pgname = self.card.name


    def stop(self):
        self.stopped = True


    def pause(self, stat):
        self.paused = stat

    def get_size(self,start_path):
        total_size = 0
        seen = {}
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                except OSError:
                    continue
                try:
                    seen[stat.st_ino]
                except KeyError:
                    seen[stat.st_ino] = True
                else:
                    continue
                total_size += stat.st_size
        return total_size

    @db_session
    def run(self):
        card = get(c for c in Cards if c == self.card)
        #try:
        self.started.emit()
        card.stat = 1 #started
        card.locked = True
        commit()
        self.total = float(card.poids)
        print(self.total)
        self.read = 0
        try:
            self.copytree(self.folderToCopy,self.destFolder)
        except:
            self.error.emit("Un erreur s'est produite pendant la copie pour des raisons de sécurité la carte %s, va être effacée de la base de donnée.")
            return
        card = get(c for c in Cards if c == self.card)
        if self.stopped:
            self.cancelled.emit()
            return
        else:
            card.stat = 2
            card.copied = True
            card.locked = False
            print('\rFinished')
            commit()
            self.done.emit()

    def cancel(self):
        self.cancelled.emit()


    def copytree(self,src, dst, symlinks=False, ignore=None):
            if self.stopped:
                return
            names = os.listdir(src)
            if ignore is not None:
                ignored_names = ignore(src, names)
            else:
                ignored_names = set()
            if not os.path.isdir(dst): # This one line does the trick
                os.makedirs(dst)
            errors = []
            for name in names:
                if self.stopped:
                                break
                if name in ignored_names:
                    continue
                try :
                    srcname = os.path.join(src, name)
                    dstname = os.path.join(dst, name)

                except:
                    srcname = os.path.join(str(src), str(name))
                    dstname = os.path.join(str(dst), str(name))
                if symlinks and os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    self.copytree(srcname, dstname,symlinks, ignore)
                else:
                    # Will raise a SpecialFileError for unsupported file types
                    source = open(srcname, "rb")
                    target = open(dstname, "wb")
                    i =0
                    while True:
                        if self.paused:
                            while self.paused:
                                time.sleep(1)
                        if self.stopped:
                            self.cancel()
                            break
                        else:
                            if self.stopped:
                                break
                            else:
                                i += 1
                                chunk = source.read(2048)
                                self.read = self.read + len(chunk)

                                if not chunk:
                                    break
                                target.write(chunk)
                                if i%1000 == 0:
                                    self.updateStatut.emit(int(self.read/ self.total *100))
                    target.close()
                    #os.chown(dstname,1002 , 100)
                    #os.chmod(dstname,444)


    def CRC32_from_file(self,filename):
        buf = open(filename,'rb').read()
        buf = (binascii.crc32(buf) & 0xFFFFFFFF)
        return "%08X" % buf

class CRCCheckError(Exception):
    pass

class CopyFunction:
    def __init__(self,rpc,MainWin):
        self.threads = 0
        self.pool = QtCore.QThreadPool()
        self.rpc = rpc
        self.MainWin = MainWin
        self.proxyDrive = None

    @db_session
    def addCopy(self,id,proxydrive):
        self.proxyDrive = proxydrive
        print("### Copy launched copy ###")
        raid = Raid[0].mountPoint
        card = get(c for c in Cards if c.id == id)
        name = card.firsName
        disk = card.disk.mountPoint
        #CREATE DIRECTORY ON RAID
        try:
            os.mkdir("%s/%s/"%(raid,card.id))
            os.mkdir("%s/%s/%s"%(raid,card.id,card.firsName))
        except OSError:
            self.error_handler("impossible d'écrire sur le Raid",card.id)
            return

        dest = "%s/%s/%s"%(raid,card.id,card.firsName)
        source = card.originalPath
        newThread = RsyncThread(source,dest,card)
        progressWidget = ProgressWidget(self.MainWin.sc_copy,card,"copy")
        self.MainWin.verticalLayout_21.addWidget(progressWidget)
        newThread.updateStatut[int].connect(progressWidget.setProgress, QtCore.Qt.QueuedConnection)
        newThread.done.connect(progressWidget.done_pyqtSignal)
        newThread.cancelled.connect(progressWidget.raise_stopped)
        newThread.started.connect(progressWidget.started)
        newThread.error[str].connect(progressWidget.raise_error)
        progressWidget.paused_sig[bool].connect(newThread.pause)
        progressWidget.stopped_click.connect(newThread.cancel)
        progressWidget.stopped[int].connect(self.cancelled)
        progressWidget.error[int,str].connect(self.error_handler)
        progressWidget.done[int].connect(self.done)
        self.threads = self.threads + 1
        self.MainWin.lab_copy.setVisible(False)
        self.pool.globalInstance().start(newThread,2)
        return

    def done(self,id):
        print("### launching encoder ###")
        self.rpc.addEncoder(id,self.proxyDrive)
        self.MainWin.bckupThread.add_copy(id)
        self.threads = self.threads - 1
        if self.threads == 0:
            self.MainWin.lab_copy.setVisible(True)
        return

    def cancelled(self,id):
        print("~~~~~~~~~~~~ID %s"%id)
        with db_session:
            card = get(c for c in Cards if c.id==id)
            if card:
                oldfree = card.disk.free
                card.disk.free = str(int(oldfree)-int(card.poids))
                shutil.rmtree("%s/%s/"%(Raid[0].mountPoint,card.id))
                card.delete()
                self.threads = self.threads - 1
                if self.threads == 0:
                    self.MainWin.lab_copy.setVisible(True)
                self.MainWin.selection.reInitProjects()

    def error_handler(self,msg,id):
        ok = QtGui.QMessageBox(QtGui.QMessageBox.Critical,"Erreur",
                                      str("Error"),
                                      QtGui.QMessageBox.Ok)
        ok.setInformativeText(str(msg))
        ok.exec_()
        with db_session:
            card = Cards[id]
            oldfree = card.disk.free
            card.disk.free = str(int(oldfree)-int(card.poids))
            shutil.rmtree("%s/%s/"%(Raid[0].mountPoint,card.id))
            self.threads = self.threads - 1
            if self.threads == 0:
                self.MainWin.lab_copy.setVisible(True)
            card.delete()


#hashlib.md5(open("/media/backup1/mam_rushes_1/184/2014_03_30_Lyon_SXS13hhh/Clip/458_1190.MXF").read()).hexdigest()
#'7cdbaaa8c9dea0a7cb6ca0398db6138b'
