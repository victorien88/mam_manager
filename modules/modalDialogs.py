# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
__author__ = 'fcp6'
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from .models import GenericListModel, IngestClipModel, DiskModel, ListModel, DiskListModel, UserAndGroupModel, \
    ClientAnGroupModel
from .dataBase import *
from .ingestWizard import Ui_Wizard
import os
import subprocess
import shlex
import json
import psutil
import uuid
import datetime
from .DiskManager import *
import logging
from . import choosedisk
from . import passwdChange

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

class Wizard(QtWidgets.QWizard):
    def __init__(self, parent = None):
        super(Wizard, self).__init__(parent)

    def setup_ui(self):
        return uic.loadUi('ui/IngestWizard.ui', self)


class ModalWindow(QtWidgets.QDialog):
    def __init__(self, parent = None, ui_file = None):
        '''
        :param parent: parent widget of this widget
        :param ui_file: path to UI file to load (optional)
        '''
        super(ModalWindow, self).__init__(parent)
        if ui_file is not None:
            uic.loadUi(ui_file, self)






class IngestWizard(object):
    def __init__(self, MainWindow, proj):
        self.audio = False
        self.MainWindow = MainWindow
        self.Project = proj
        self.sub = None
        self.avc = False
        with db_session:
            pays = select(a.pays for a in Assets).distinct()[:]
            cyties = select(a.ville for a in Assets).distinct()[:]
            jri = select(a.jri for a in Cards).distinct()[:]
            self.cityCompleter = QtWidgets.QCompleter(cyties)
            self.countryCompleter = QtWidgets.QCompleter(pays)
            self.jriCompleter = QtWidgets.QCompleter(jri)
            self.countryCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.jriCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.cityCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)


    # noinspection PySimplifyBooleanCheck
    def choose_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self.dialog, "Choisir votre carte", self.dialog.previous_path)
        if not self.audio:
            if folder:
                if self.folder_is_card(folder):
                    self.ui_dialog.l_cardpath.setText(folder)
                    self.fileList = self.get_video_files(folder)
                else:
                    a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Modèle non référencé",
                                          "Mam ingester n'arrive pas à déterminer le modèle de votre caméra.<br>",
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                          self.MainWindow)
                    a.setInformativeText(
                        "Voulez-vous que MaMingester essaye de trouver tous les fichiers vidéo de l'arbre"
                        "assurez vous d'avoir sélectionné une carte ?")
                    ret = a.exec_()
                    if ret == QtWidgets.QMessageBox.Yes:
                        self.fileList = self.get_raw_three(folder)
                        if not self.fileList:
                            a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Modèle non référencé",
                                                  "Mam ingester n'a trouvé aucun clip.<br>",
                                                  QtWidgets.QMessageBox.Ok,
                                                  self.MainWindow)
                            a.setInformativeText("Impossible de continuer")
                            a.exec_()
                            return
                        self.ui_dialog.l_cardpath.setText(folder)
                        self.dialog.setField("cardType", "UNKNOWN")
                    else:
                        return
            else:
                return
        else:
            if folder:
                self.fileList = self.get_raw_audio_three(folder)
                logging.warning("Files found : %s" % self.fileList)
                if self.fileList == []:
                    a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Modèle non référencé",
                                          "Mam ingester n'a trouvé aucun clip.<br>",
                                          QtWidgets.QMessageBox.Ok,
                                          self.MainWindow)
                    a.setInformativeText("Impossible de continuer")
                    a.exec_()
                    return
                else:
                    self.ui_dialog.l_cardpath.setText(folder)
                    self.dialog.setField("cardType", "GENERIC AUDIO CARD")

    def get_raw_audio_three(self, folder):
        self.mode = None
        self.xpath = None
        exts = ('.aif', '.AIF', ".aiff", ".AIFF", ".mp3", ".MP3", ".wav", ".WAV", ".wave", ".WAVE",
                ".aac", ".AAC", ".m4a", ".M4A",".FLAC",".flac")
        fileList = []

        progress = QtWidgets.QProgressDialog("Analyse des fichiers...", "Anuler", 0,0)
        progress.setWindowModality(QtCore.Qt.WindowModal)


        for root, dirs, files in os.walk(folder, topdown=True):
            i =+ 1

            for name in set(files):
                if progress.wasCanceled():
                    fileList = []
                    break
                if os.path.splitext(name)[1] in exts and not os.path.splitext(name)[0][0] == '.' \
                        and ".AppleDouble" not in root and ".AppleSingle" not in root:
                    fileList.append(os.path.join(root, name))

        return sorted(fileList)

    def get_raw_three(self, folder):
        self.mode = None
        self.xpath = None
        exts = (
            '.mxf', '.MXF', ".mts", ".MTS", ".m2t", ".M2T", ".mov", ".MOV", ".mp4", ".MP4", ".avi", ".AVI", ".mpg",
            ".MPG",
            ".mpeg", ".MPEG", ".mkv", ".MKV", ".M4V", ".m4v")
        fileList = []
        for root, dirs, files in os.walk(folder, topdown=True):

            for name in set(files):
                if os.path.splitext(name)[1] in exts and not os.path.splitext(name)[0][0] == '.' \
                        and not os.path.splitext(name)[0].endswith("S01") \
                        and not ".AppleDouble" in root and not ".AppleSingle" in root:
                    fileList.append(os.path.join(root, name))
        return sorted(fileList)

    def get_video_files(self, folder):
        fileList = []
        for root, dirs, files in os.walk(folder, topdown=True):
            for name in set(files):
                if os.path.splitext(name)[1] == self.cardRosetta['clipExt'] and not os.path.splitext(name)[0][0] == '.' \
                        and not os.path.splitext(name)[0].endswith("S01") \
                        and ".AppleDouble" not in root and ".AppleSingle" not in root:
                    fileList.append(os.path.join(root, name))
        sortFileList = sorted(fileList)
        self.fileList = sortFileList
        return sortFileList

    def folder_is_card(self, folder):
        for card in self.cardDB:
            checkPath = folder + card['checkDir']
            if os.path.isdir(checkPath):
                self.cardRosetta = card
                self.dialog.setField("cardType", card['name'])
                try:
                    self.mode = card['tcMode']
                    self.xpath = card['Xpath']
                except KeyError:
                    print("no mode __ freestyle=")
                    self.mode = None
                    self.xpath = None
                self.avc = ""
                return True
        return False

    def enable_source(self):
        if self.ui_dialog.checkBox_2.isChecked():
            self.ui_dialog.l_own.setReadOnly(True)
            self.ui_dialog.l_own.setText("Galaxie Presse")
        else:
            self.ui_dialog.l_own.setReadOnly(False)
            self.ui_dialog.l_own.setText("")

    @db_session
    def check_name(self, id):
        if id == 1:
            self.dialog.setField('name', os.path.basename(self.dialog.field('cardPath')))
            self.dialog.setField("owner", "Galaxie Presse")
        if id == 2:
            if exists(c for c in Cards if c.name == self.dialog.field("name")):
                alert = QtWidgets.QMessageBox(self.dialog)
                alert.setText("Une carte avec le même nom existe déjà")
                alert.setWindowTitle("Attention")
                alert.setInformativeText("Merci de choisir un autre nom pour votre carte")
                alert.setIcon(QtWidgets.QMessageBox.Critical)
                alert.exec_()
                self.dialog.back()
            else:
                self.setupModel()

    def readFile(self, row):
        if self.sub:
            self.sub.terminate()
        cmd = "ffplay " + "-autoexit " + "-i " + "'" + self.ui_dialog.t_clips.model().arraydata[int(row)][0] \
              + "'" + " -vf " + "scale=320:240"
        args = shlex.split(cmd)
        self.sub = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

    def setupModel(self):
        data = [[a, os.path.basename(a), '', '', ''] for a in self.fileList]
        model = IngestClipModel(data, ['Path', 'Name', 'Tags', 'Description', 'View'])
        a = []
        self.ui_dialog.t_clips.setModel(model)
        for i in range(0, len(model.arraydata)):
            a.append(QtWidgets.QLabel())
            a[i].setPixmap(QtGui.QPixmap("images/ic_play_circle_fill_black_24dp.png"))
            a[i].setText("<a href='%s'>lire le clip</a>" % i)
            a[i].linkActivated[str].connect(self.readFile)
            self.ui_dialog.t_clips.setIndexWidget(self.ui_dialog.t_clips.model().index(i, 4), a[i])

    def setupUi(self):
        self.audio = False
        self.dialog = Wizard()
        self.ui_dialog = self.dialog.setup_ui()
        self.dialog.currentIdChanged[int].connect(self.check_name)
        self.ui_dialog.wizardPage1.registerField("cardPath*", self.ui_dialog.l_cardpath)
        self.ui_dialog.wizardPage2.registerField("owner*", self.ui_dialog.l_own)
        self.ui_dialog.wizardPage2.registerField("name*", self.ui_dialog.l_name)
        self.ui_dialog.wizardPage2.registerField("jri*", self.ui_dialog.l_jri)
        self.ui_dialog.wizardPage2.registerField("cardType", self.ui_dialog.t_model)
        self.ui_dialog.wizardPage2.registerField("comment", self.ui_dialog.t_desc)
        self.ui_dialog.wizardPage2.registerField("pays", self.ui_dialog.l_key)
        self.ui_dialog.wizardPage2.registerField("ville", self.ui_dialog.l_city)
        self.ui_dialog.wizardPage2.registerField("datetourn", self.ui_dialog.dateEdit)
        self.dialog.setField("owner", "Galaxie Presse")
        self.ui_dialog.b_browse.clicked.connect(self.choose_folder)
        self.ui_dialog.dateEdit.setDate(QtCore.QDate.currentDate())
        self.ui_dialog.checkBox_2.stateChanged.connect(self.enable_source)
        self.ui_dialog.label_4.setText("Dans le projet : <b>%s</b>" % self.Project.name)
        self.ui_dialog.l_key.setCompleter(self.countryCompleter)
        self.ui_dialog.l_city.setCompleter(self.cityCompleter)
        self.ui_dialog.l_city.setCompleter(self.cityCompleter)
        self.ui_dialog.l_jri.setCompleter(self.jriCompleter)
        self.dialog.previous_path = ""
        self.audio = False
        self.ui_dialog.radioButton.toggled[bool].connect(self.set_audio)

        with db_session:
            a = select(a for a in Assets if a.card.project.id == self.Project.id).order_by(desc(Assets.id))[:]
            if len(a):
                self.dialog.setField("jri", a[0].card.jri)
                self.dialog.setField("datetourn", str(a[0].card.tournageDate))
                self.dialog.setField("pays", a[0].pays)
                self.dialog.setField("ville", a[0].ville)
                self.dialog.previous_path = os.sep.join(a[0].card.originalPath.split(os.sep)[:-1])
        try:
            with open('CameraDB', 'rb') as fp:
                self.cardDB = json.load(fp)

        except IOError:
            a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "Erreur",
                                  "Impossible de charger la description des cartes. "
                                  "<br> Vérifiez que le fichier est présent.",
                                  QtWidgets.QMessageBox.Ok, self.MainWindow)
            a.exec_()
            return False, '', '', '', '', '', '', '', '', '', '', ''

        a = self.dialog.exec_()
        return a, self.dialog.field("cardPath"), self.dialog.field("name"), self.dialog.field('jri'), \
               self.ui_dialog.ch_h264.isChecked(), self.ui_dialog.t_desc.toPlainText(), self.dialog.field("pays"), \
               self.dialog.field("ville"), self.dialog.field("datetourn"), self.dialog.field("cardType"), \
               self.dialog.field(
                   "owner"), self.ui_dialog.t_clips.model().arraydata if self.ui_dialog.t_clips.model() else '',\
               self.avc, self.mode if self.mode else False, self.xpath if self.xpath else False, self.audio


    def set_audio(self, value):
        self.ui_dialog.l_cardpath.setText("")
        self.fileList = []
        self.audio = value


class ModalDialog(object):
    def __init__(self, MainWindow):
        self.MainWindow = MainWindow

    def load_combo_project(self, id):
        self.ui_dialog.c_proj.setModel(ListModel(
            self.ui_dialog.c_group.model().get_children(self.ui_dialog.c_group.currentIndex()), "project"))
        if not self.ui_dialog.c_proj.model().hasList():
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)


    def load_combo_groups(self, id, cartes=True):
        self.ui_dialog.c_group.setModel(ListModel(
            self.ui_dialog.c_coll.model().get_children(self.ui_dialog.c_coll.currentIndex()), "group"))
        if cartes:
            self.ui_dialog.c_proj.setCurrentIndex(0)
            self.ui_dialog.c_proj.setModel(ListModel(
                self.ui_dialog.c_group.model().get_children(self.ui_dialog.c_group.currentIndex()), "project"))

        if not self.ui_dialog.c_proj.model().hasList():
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def load_combo_groups_for_2(self, id, cartes=True):
        self.ui_dialog.c_group.setModel(ListModel(
            self.ui_dialog.c_coll.model().get_children(self.ui_dialog.c_coll.currentIndex()), "group"))
        if not self.ui_dialog.c_group.model().hasList():
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
    @db_session
    def text_ch(self,sorte):
        self.dialog.warn.setVisible(False)
        if self.dialog.l_name.text() == "":
            self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        if sorte == "coll":
            if exists(c for c in Collection if c.name == self.dialog.l_name.text()):
                self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
                self.dialog.warn.setVisible(True)
        elif sorte =="group":
            if exists(c for c in ProjectGroup if c.name == self.dialog.l_name.text()):
                self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
                self.dialog.warn.setVisible(True)
    @db_session
    def showChGroup(self, collection_model, project):
        print("#####################")
        print("project :::::: %s" % project)
        self.dialog = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.dialog.setWindowTitle("Changer de groupe")
        self.ui_dialog = loadUiWidget('chgGroup2Dialog.ui', parent=self.dialog)
        self.ui_dialog.label.setText("<b>Où déplacer :</b><br> %s" % (', <br>'.join([a.name for a in project])))
        self.ui_dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.ui_dialog.buttonBox.accepted.connect(self.dialog.accept)
        self.ui_dialog.c_coll.setModel(collection_model)
        self.ui_dialog.c_group.setCurrentIndex(0)
        self.load_combo_groups_for_2(0)
        self.ui_dialog.c_coll.currentIndexChanged[int].connect(self.load_combo_groups_for_2)
        a = self.dialog.exec_()
        return a, self.ui_dialog.c_group.model().getItem(self.ui_dialog.c_group.currentIndex())


    def showChProj(self, collectionModel, project_model, project):
        self.dialog = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.dialog.setWindowTitle("Changer de Groupe")
        self.ui_dialog = loadUiWidget('chgProjDialog.ui', parent=self.dialog)
        self.ui_dialog.label.setText("<b>Où déplacer :</b><br> %s" % (', <br>'.join([a.name for a in project])))
        self.ui_dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.ui_dialog.buttonBox.accepted.connect(self.dialog.accept)
        self.ui_dialog.c_coll.setModel(collectionModel)
        self.ui_dialog.c_group.setModel(project_model)
        self.load_combo_groups(0)
        self.ui_dialog.c_group.currentIndexChanged[int].connect(self.load_combo_project)
        self.ui_dialog.c_coll.currentIndexChanged[int].connect(self.load_combo_groups)
        self.ui_dialog.c_proj.setCurrentIndex(0)
        a = self.dialog.exec_()
        return a, self.ui_dialog.c_proj.model().getItem(self.ui_dialog.c_proj.currentIndex())

    @db_session
    def showChColl(self, model, projects):
        self.dialog = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.dialog.setWindowTitle("Changer de collection")
        self.ui_dialog = loadUiWidget('chgGroupDialog.ui', parent=self.dialog)
        self.ui_dialog.label.setText("<b>Où déplacer :</b><br> %s" % (',<br>'.join([a.name for a in projects])))
        self.ui_dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.ui_dialog.buttonBox.accepted.connect(self.dialog.accept)
        self.ui_dialog.comboBox.setModel(model)
        a = self.dialog.exec_()
        return a, self.ui_dialog.comboBox.currentIndex()


    def show_disk_info(self):
        self.dialog.b_current.setEnabled(False)
        name, online, default, mountPoint, sav_online, used = self.dialog.listView.model().getAttrib(
            self.dialog.listView.selectionModel().selectedIndexes()[0])
        self.dialog.label.setText(
            "<b>%s</b><br>Statut : %s<br> Disponible : %s Mo<br><span style='color:#92000d;'> %s</span>" %
            (name,
             "<span style='color:#008000;'>online</span>" if online else "<span style='color:#92000d;'>offline</span>",
             psutil.disk_usage(mountPoint).free if online else "N.D.",
             "Disque par défaut" if default else ""))
        if not default and online:
            self.dialog.b_current.setEnabled(True)


    def make_current(self):
        will_do = False
        with db_session:
            running_card = select(c for c in Cards if c.disk == self.pool.current_disk and c.stat < 2)[:]
            if not len(running_card) == 0:
                a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Copies en cours",
                                      "Attention, des copies sont en cours sur le disque. Vous ne pourrez débrancher les disques que lorsque la copie sera terminée;",
                                      QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                      self.MainWindow)
                ret = a.exec_()
                if ret == QtWidgets.QMessageBox.Yes:
                    will_do = True
            else:
                will_do = True
        if will_do:
            self.dialog.listView.model().setCurrent(self.dialog.listView.selectionModel().selectedIndexes()[0])
            self.show_disk_info()

    def validate_selected_drive(self):
        if self.dialog2.driveView.selectionModel().hasSelection():
            self.dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def showDiskChooserDialog(self, model):
        self.dialog2 = ModalWindow(self.MainWindow,"ui/choosedisk.ui")
        #self.dialog.setVisible(False)
        self.dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.dialog2.buttonBox.rejected.connect(self.dialog2.reject)
        self.dialog2.buttonBox.accepted.connect(self.dialog2.accept)
        self.dialog2.driveView.setModel(model)
        e = self.dialog2.driveView.selectionModel()
        e.selectionChanged.connect(self.validate_selected_drive)
        # self.MainWindow.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.dialog_ok)
        v = self.dialog2.exec_()

        if v:
            return model.getItemFromIndex(e.selectedIndexes()[0])
        else:
            return None, None

    def add_disk(self):
        self.pool = DiskPool(self.MainWindow)
        selected_main_part = self.showDiskChooserDialog(DiskListModel(self.pool.get_addable_disks()))
        logging.debug('you choose : {0:s}'.format(selected_main_part['path']))
        if selected_main_part:
            if os.access(selected_main_part["path"], os.W_OK):
                # self.pool.add_disk(selected_sav_part,selected_main_part)
                self.pool.add_disk(selected_main_part["path"])
                with db_session:

                    self.dialog.listView.setModel(DiskModel(self.pool,select(d for d in Disk)))
                    self.dialog.listView.selectionModel().selectionChanged.connect(self.show_disk_info)
            else:
                a = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Pas de droit d'accès",
                                      "Ce disque est en lecture seule. Vous devez choisir un disque pour lequel vous avez des droits d'accès en écriture",
                                      QtWidgets.QMessageBox.Ok,
                                      self.MainWindow)
                a.exec_()

    def showAddGroupDialog(self, title, header, description):
        self.dialog = ModalWindow(self.MainWindow,"ui/add_group.ui")
        self.dialog.setWindowTitle(title)
        self.dialog.ltitle.setText("<b>%s</b>" % (str(header)))
        self.dialog.ldesc.setText("<i>%s</i>" % description)
        self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        model = UserAndGroupModel()
        self.dialog.listView.setModel(model)
        self.dialog.warn.setVisible(False)
        clientmodel = ClientAnGroupModel()
        self.dialog.listView_2.setModel(clientmodel)
        self.dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.dialog.buttonBox.accepted.connect(self.dialog.accept)
        # self.MainWindow.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.dialog_ok)
        self.dialog.l_name.textEdited.connect(lambda : self.text_ch("group"))
        a = self.dialog.exec_()
        return self.dialog.l_name.text(), self.dialog.l_desc.toPlainText(), clientmodel, model, a

    def showAddCollDialog(self, title, header, description):
        self.dialog = ModalWindow(self.MainWindow,"ui/add_coll.ui")
        self.dialog.setWindowTitle(title)
        self.dialog.ltitle.setText("<b>%s</b>" % (str(header)))
        self.dialog.ldesc.setText("<i>%s</i>" % description)
        self.dialog.warn.setVisible(False)
        self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.dialog.buttonBox.accepted.connect(self.dialog.accept)
        self.dialog.l_name.textEdited.connect(lambda : self.text_ch("coll"))
        a = self.dialog.exec_()
        return self.dialog.l_name.text(), self.dialog.l_desc.toPlainText(), a

    def refresh(self):
        self.pool = DiskPool(self.MainWindow)
        self.dialog.listView.model().refresh()

    @db_session
    def showAddAssetDisk(self, pool):
        self.pool = pool
        self.pool = DiskPool(self.MainWindow)
        self.dialog = ModalWindow(self.MainWindow,"ui/assetDisk_add.ui")
        self.dialog.setWindowTitle("Ajouter un disque")
        diskModel = DiskModel(self.pool)
        self.dialog.listView.setModel(diskModel)
        a = self.dialog.listView.selectionModel()
        self.dialog.listView.selectionModel().selectionChanged.connect(self.show_disk_info)
        self.dialog.b_current.clicked.connect(self.make_current)
        self.dialog.b_add_disk.clicked.connect(self.add_disk)
        self.dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.dialog.buttonBox.accepted.connect(self.dialog.accept)
        self.dialog.B_refresh.clicked.connect(self.refresh)
        # self.MainWindow.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.dialog_ok)
        a = self.dialog.exec_()
        return self.dialog.listView.model().getData(), a

    def chk_passw(self):
        if self.ui_dialog2.lineEdit.text() == self.ui_dialog2.lineEdit_2.text() and len(
                self.ui_dialog2.lineEdit.text()) > 5:
            self.dialog2.accept()
        else:
            ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "Erreur",
                                   str("Mot de passe trop court ou non concordants."),
                                   QtWidgets.QMessageBox.Ok, self.MainWindow)
            ok.exec_()
            self.dialog2.reject()


    def check_mail(self):
        if not self.ui_dialog2.lineEdit.text() == "" and self.ui_dialog2.plainTextEdit.toPlainText() == "":
            self.ui_dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.ui_dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def show_send_mail(self, title, label):
        from .mailDialog import Ui_Dialog as ui_mail

        self.dialog2 = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.ui_dialog2 = ui_mail()
        self.ui_dialog2.setupUi(self.dialog2)
        self.dialog2.setWindowTitle(title)
        self.ui_dialog2.label.setText(label)
        self.ui_dialog2.buttonBox.rejected.connect(self.dialog2.reject)
        self.ui_dialog2.lineEdit.textChanged.connect(self.check_mail)
        self.ui_dialog2.plainTextEdit.textChanged.connect(self.check_mail)
        self.ui_dialog2.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        a = self.dialog2.exec_()
        return a, self.ui_dialog2.lineEdit.text(), self.ui_dialog2.plainTextEdit.toPlainText()

    def show_ch_passwd(self):
        self.dialog2 = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.ui_dialog2 = passwdChange.Ui_Dialog()
        self.ui_dialog2.setupUi(self.dialog2)
        self.dialog2.setWindowTitle("Changer le mot de passe")
        self.ui_dialog2.buttonBox.rejected.connect(self.dialog2.reject)
        self.ui_dialog2.buttonBox.accepted.connect(self.chk_passw)
        a = self.dialog2.exec_()
        return a, self.ui_dialog2.lineEdit_2.text()

    def show_right_dialog(self, group):
        from ._rightChooser import Ui_Dialog as ui_right

        self.dialog5 = QtGui.QDialog(self.MainWindow, QtCore.Qt.Tool)
        self.ui_dialog5 = ui_right()
        self.ui_dialog5.setupUi(self.dialog5)
        model = UserAndGroupModel(group=group)
        clientmodel = ClientAnGroupModel(group)
        self.ui_dialog5.listView.setModel(model)
        self.ui_dialog5.listView_2.setModel(clientmodel)
        self.dialog5.accepted.connect(lambda: (model.insert_in_db(), clientmodel.insert_in_db()))
        a = self.dialog5.exec_()

    def showAddProjectDialog(self, title, header, description):
        self.dialog = ModalWindow(self.MainWindow,'ui/add_proj.ui')
        self.dialog.setWindowTitle(title)
        self.dialog.ltitle.setText("<b>%s</b>" % (str(header)))
        self.dialog.ldesc.setText("<i>%s</i>" % description)
        self.dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.dialog.buttonBox.rejected.connect(self.dialog.reject)
        self.dialog.buttonBox.accepted.connect(self.dialog.accept)
        # self.MainWindow.ui_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.dialog_ok)
        self.dialog.l_name.textEdited.connect(self.text_ch)
        a = self.dialog.exec_()
        return self.dialog.l_name.text(), self.dialog.l_desc.toPlainText(), self.dialog.l_real.text(), a
