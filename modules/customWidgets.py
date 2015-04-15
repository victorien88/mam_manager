# -*- coding: utf-8 -*-s
__author__ = 'fcp6'
from PyQt5 import QtCore, QtGui,QtWidgets
from .dataBase import *

class ProgressWidget(QtWidgets.QWidget):
    stopped_click = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal(int)
    paused_sig = QtCore.pyqtSignal(bool)
    error = QtCore.pyqtSignal(int,str)
    done = QtCore.pyqtSignal(int)

    def __init__(self,parent,card, category):
        super().__init__(self,parent)
        self.parent_widget=parent
        self.setupUi(parent)
        self.paused = False
        self.card = card
        self.category = category
        with db_session:
            self.card_name = get(c for c in Cards if c == card).name
            self.card_id = get(c for c in Cards if c == card).id

        if self.category == "copy":
            self.l_progress.setText("Copie de la carte %s <br> En attente d'une place disponible dans la file"%self.card_name)
        if self.category == "analyse":
            self.l_progress.setText("Analyse de la carte %s <br> En attente d'une place disponible dans la file"%self.card_name)



    def raise_error(self,chain):
        self.error.emit(self.card_id,chain)
        self.deleteLater()


    def done_pyqtSignal(self):
        self.done.emit(self.card_id)
        self.deleteLater()

    def setupUi(self,parent):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 39, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.l_progress = QtGui.QLabel(self)
        self.l_progress.setObjectName("l_progress")
        self.verticalLayout.addWidget(self.l_progress)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.prog_bar = QtGui.QProgressBar(self)
        self.prog_bar.setMaximum(0)
        self.prog_bar.setMinimum(0)
        self.prog_bar.setObjectName("prog_bar")
        self.horizontalLayout.addWidget(self.prog_bar)
        self.b_stop = QtGui.QToolButton(parent)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("images/ic_stop_black_18dp.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.b_stop.setIcon(icon)
        self.b_stop.setObjectName("b_stop")
        self.horizontalLayout.addWidget(self.b_stop)
        self.b_pause = QtGui.QToolButton()
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("images/ic_pause_black_18dp.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.b_pause.setIcon(icon1)
        self.b_pause.setObjectName("b_pause")
        self.horizontalLayout.addWidget(self.b_pause)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.b_pause.setEnabled(False)
        self.b_stop.setEnabled(False)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.b_pause.clicked.connect(self.pause)
        self.b_stop.clicked.connect(lambda : self.stopped_click.emit())


    def setProgress(self,value):
            self.prog_bar.setValue(value)
            return

    def show_warning(self,msg):
        from ._warning import Ui_Dialog
        self.dialog2 = QtGui.QDialog(self.parent_widget, QtCore.Qt.Tool)
        self.ui_dialog2 = Ui_Dialog()
        self.ui_dialog2.setupUi(self.dialog2)
        self.dialog2.setWindowTitle("Des Erreurs sont apprues pendant l'analyse")
        self.ui_dialog2.textEdit.setHtml(msg)
        self.ui_dialog2.buttonBox.rejected.connect(self.dialog2.reject)
        self.ui_dialog2.buttonBox.accepted.connect(self.dialog2.accept)
        a = self.dialog2.exec_()
        return a

    def generate_review(self,dictionaire):
        corps = ""
        fatal = 0
        warning = 0
        for clip in dictionaire['clips']:
            if clip["error"]:
                if clip['error-type'] == "fatal":
                    fatal += 1
                    corps = "%s%s"%(corps,"<h2>%s</h2><p><font color='red'>%s</font></p>"%(clip["name"],clip['error-desc']))
                else:
                    warning += 1
                    corps = "%s%s"%(corps,"<h2>%s</h2<p><font color='blue'>%s</font></p>"%(clip["name"],clip['error-desc']))
        corps = "%s%s"%("<h1>%s<br>%s erreur(s) et %s avertissements ont été détectés sur %s clips</h1>"%(
            dictionaire['name'], fatal,warning,len(dictionaire)),corps)
        a = self.show_warning(corps)
        return a

    def review(self,dictionaire):
        if dictionaire["all_ok"]:
            if dictionaire["audio"]:
                    self.add_audio_in_db(dictionaire["clips"],dictionaire['proxy'])
            else:
                    self.add_video_in_db(dictionaire["clips"],dictionaire['proxy'])
        else:
            response = self.generate_review(dictionaire)
            if response:
                if dictionaire["audio"]:
                    self.add_audio_in_db(dictionaire["clips"],dictionaire['proxy'])
                else:
                    self.add_video_in_db(dictionaire["clips"],dictionaire['proxy']
                                         )
            else:
                self.error.emit(self.card_id,"Vous avez annulé l'import.")
                self.deleteLater()


    def raise_stopped(self):
        self.stopped.emit(self.card_id)
        self.deleteLater()


    def started(self):
        self.prog_bar.setMaximum(100)
        self.prog_bar.setMinimum(0)
        if self.category == "copy":
            self.l_progress.setText("Copie de la carte %s"%self.card_name)
        if self.category == "analyse":
            self.l_progress.setText("Analyse de la carte %s"%self.card_name)
        self.b_pause.setEnabled(True)
        self.b_stop.setEnabled(True)

    def pause(self):
        if self.paused:
            self.b_stop.setEnabled(True)
            self.paused = False
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap("images/ic_pause_black_18dp.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.l_progress.setText(self.oldTitle)
            self.b_pause.setIcon(icon1)
            self.prog_bar.setMaximum(100)
            self.prog_bar.setMinimum(0)
            self.prog_bar.setValue(self.oldvalue)
            self.paused_sig.emit(False)
        else:
            self.b_stop.setEnabled(False)
            self.oldTitle = self.l_progress.text()
            self.l_progress.setText(self.oldTitle + " PAUSED")
            self.paused = True
            self.oldvalue = self.prog_bar.value()
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap("images/ic_play_circle_fill_black_24dp.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.b_pause.setIcon(icon1)
            self.prog_bar.setMaximum(0)
            self.prog_bar.setMinimum(0)
            self.paused_sig.emit(True)

    def add_audio_in_db(self,pre_processing,proxy):
        with db_session:

            try:
                card = Cards[self.card_id]
                for clip in pre_processing:
                    if clip["error"]:
                        if clip['error-type'] == "fatal":
                            continue

                    new_clip = Assets(name = clip["name"], tag = clip["tag"], comment = clip["comment"],
                                      hasProxy = False ,card = card, stat = 0, durationSec = clip["duration"],
                                      clipPath=clip["clipPath"], timeCode= clip["timecode"],videoCodec = clip["codec"],
                                      videoSize = clip["size"],proxyDisk=get(p for p in ProxyDrive if p == proxy),
                                      videoFps=clip["fps"], pays = clip["pays"], ville = clip["ville"],
                                      nb_audio_stream = clip["audiostr"],
                                      durationFrm = int(float(clip["fps"])*float(clip["duration"])))

                print("####EMITTIG DONE###")
                self.done.emit(self.card_id)
                self.progressWidget.deleteLater()
            except:

                self.error.emit(self.card_id,"Impossible d'ajouter la carte %s dans la base de données une"
                                             " erreur inconue est apparue"%self.card_name)
                self.deleteLater()

    def add_video_in_db(self, pre_processing,proxy):
        with db_session:
                try:
                        card = Cards[self.card_id]
                        for clip in pre_processing:
                            if clip["error"]:
                                if clip['error-type'] == "fatal":
                                    continue

                            new_clip = Assets(name = clip["name"], tag = clip["tag"], comment = clip["comment"], hasProxy = False ,card = card,
                                                          stat = 0, durationSec = clip["duration"],clipPath=clip["clipPath"],
                                                          timeCode= clip["timecode"],videoCodec = clip["codec"], videoSize = clip["size"],proxyDisk=get(p for p in ProxyDrive if p == proxy),
                                                          videoFps=clip["fps"], pays = clip["pays"], ville = clip["ville"], nb_audio_stream = clip["audiostr"],
                                                          durationFrm = int(float(clip["fps"])*float(clip["duration"])))

                        self.done.emit(self.card_id)
                        self.deleteLater()
                except:
                    self.error.emit(self.card_id,"Impossible d'ajouter la carte %s dans la base de données une"
                                                     " erreur inconue est apparue"%self.card_name)
                    self.deleteLater()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    container = QtGui.QWidget()
    a = ProgressWidget(container,"test")
    container.show()
    sys.exit(app.exec_())

