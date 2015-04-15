from PySide import QtGui, QtCore
import os
from .dataBase import *


class BackupThread(QtCore.QObject,QtCore.QRunnable):
    started = QtCore.Signal()
    finished = QtCore.Signal()
    def __init__(self, *args, **kwargs):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        with db_session:
            disk = get(d for d in Disk if d.current)

        self.delta = 0


    def run(self):
        self.started.emit()
        with db_session:
            drive = get(d for d in Disk if d.current )
            os.system("rsync -av --verbose --delete %s %s"%(drive.mountPoint, drive.backup.mountPoint))
            '''dirsync.sync(drive.mountPoint, drive.backup.mountPoint,"sync",verbose=True)'''

        self.finished.emit()



class Backuper(object):
    def __init__(self):
        self.started = False
        print(self.started)

    def start(self):
        print('im starting')
        thread = BackupThread()
        thread.started.connect(self.makeStarted)
        thread.finished.connect(self.makeStopped)
        QtCore.QThreadPool.globalInstance().start(thread,3)
    def makeStarted(self):
        self.started = True
    def makeStopped(self):
        self.started=False