# -*- coding: utf-8 -*-

__author__ = 'fcp6'
import hashlib
import shutil
import binascii
# from https://libbits.wordpress.com/2011/04/09/get-total-rsync-progress-using-python/
import logging
from PyQt5 import QtGui, QtCore
import os
from pony.orm import *
from .dataBase import *
import time
from .customWidgets import ProgressWidget
import shutil
logging.basicConfig( format='%(asctime)s %(message)s', level=logging.DEBUG)

class Signaler(QtCore.QObject):
    updateStatut = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(str, int)
    updatePh = QtCore.pyqtSignal(str)
    def __init__(self,**kwds):
        QtCore.QObject.__init__(self)


class BackupThread(QtCore.QRunnable):

    def __init__(self,**kwds):
        QtCore.QRunnable.__init__(self,**kwds)
        self.signaller = Signaler()
        self.updateStatut = self.signaller.updateStatut
        self.error = self.signaller.error
        self.updatePh = self.signaller.updatePh
        self.currentRunning = None
        self.process = []
        self.quitloop = False
        self.totalsize = float("0.0")
        self.read = 0
        self.isRunning = False
    def add_copy(self,id):
        logging.debug("Adding card : %s"%id)
        self.process.append(id)
        self.update_stat()

    def stop(self):
        self.quitloop = True


    def update_stat(self):
        if self.process:
            with db_session:
                disks = []
                for cid in self.process:
                    disks.append(Cards[cid].disk.name)
            sdisks = []
            for a in disks:
                if not a in sdisks:
                    sdisks.append(a)
            with db_session:
                stat = "Copie restante sur... "
                for disk in sdisks:
                    stat = stat + disk + " : "
                    stat = stat + str(len(select(c for c in Cards if c.disk.name == disk and c.stat == 2)))
            self.updatePh.emit(str(stat))
        else:
            self.updatePh.emit("Aucune copie en cours...")

    def run(self):
        while True:

            if not self.quitloop:
                if self.process == []:

                    self.updateStatut.emit(100)
                    self.updateStr = "Aucune copie en cours..."
                    time.sleep(0.5)
                else:
                    self.update_stat()
                    id = self.process[0]
                    logging.debug("Starting backup of card : %s"%id)
                    self.currentRunning = id
                    self.isRunning=True
                    try:
                        self.make_folderstrucure(id)
                        self.runcopy(id)
                        with db_session:
                            Cards[id].stat = 3

                        self.process.remove(id)
                        logging.debug("Backup of card : %s done"%id)
                        self.update_stat()
                        self.isRunning=False
                    except:

                        logging.error("An errot has occured during copy of card %s" %id)
                        with db_session:
                            self.error.emit("Un erreur s'est produite pendant la copie de la carte %s sur le disque %s. Assurez vous de brancher le disque avant d'appuyer sur OK"%(Cards[id].name,Cards[id].disk.name),id)
                        self.process.remove(id)
                        self.update_stat()
                        self.isRunning=False

            else:
                break
        return




    def make_folderstrucure(self,id):
        logging.debug("Making folder structure of : %s"%id)
        with db_session:
            card = Cards[id]

            try:

                os.mkdir("%s/%s/"%(card.disk.mountPoint,card.id))
                os.mkdir("%s/%s/%s"%(card.disk.mountPoint,card.id,card.firsName))

            except:
                logging.debug("folder strucure of card %s already done."%id)
        return

    @db_session
    def runcopy(self,id):
        card = get(c for c in Cards if c.id == id)

        self.totalsize += float(card.poids)
        self.updateStatut.emit(int(self.read/ self.totalsize *100))
        logging.debug("Starting copy of card %s"%id)

        self.copytree("%s/%s/%s"%(Raid[0].mountPoint,card.id,card.firsName),"%s/%s/%s"%(card.disk.mountPoint,card.id,card.firsName))



    def copytree(self,src, dst, symlinks=False, ignore=None):

            names = os.listdir(src)
            if ignore is not None:
                ignored_names = ignore(src, names)
            else:
                ignored_names = set()

            if not os.path.isdir(dst): # This one line does the trick
                os.makedirs(dst)


            for name in names:

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

                                i += 1
                                chunk = source.read(8*2048)
                                self.read = self.read + len(chunk)

                                if not chunk:
                                    break
                                target.write(chunk)
                                if i%1000 == 0:
                                    self.updateStatut.emit(int(self.read/ self.totalsize *100))
                    target.close()


