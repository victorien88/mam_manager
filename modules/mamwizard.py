# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/user1/MamManager/mamwizard.ui'
#
# Created: Wed Oct 22 21:50:15 2014
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Wizard(object):
    def setupUi(self, Wizard):
        Wizard.setObjectName("Wizard")
        Wizard.resize(833, 672)
        Wizard.setWizardStyle(QtGui.QWizard.ModernStyle)
        Wizard.setOptions(QtGui.QWizard.CancelButtonOnLeft|QtGui.QWizard.HaveHelpButton|QtGui.QWizard.NoBackButtonOnStartPage)
        self.wizardPage1 = QtGui.QWizardPage()
        self.wizardPage1.setObjectName("wizardPage1")
        self.verticalLayout = QtGui.QVBoxLayout(self.wizardPage1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.wizardPage1)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayoutc = QtGui.QHBoxLayout()
        self.horizontalLayoutc.setObjectName("horizontalLayoutc")
        self.l_cardpath = QtGui.QLineEdit(self.wizardPage1)
        self.l_cardpath.setEnabled(False)
        self.l_cardpath.setObjectName("l_cardpath")
        self.horizontalLayoutc.addWidget(self.l_cardpath)
        self.b_browse = QtGui.QPushButton(self.wizardPage1)
        self.b_browse.setObjectName("b_browse")
        self.horizontalLayoutc.addWidget(self.b_browse)
        self.verticalLayout.addLayout(self.horizontalLayoutc)
        Wizard.addPage(self.wizardPage1)
        self.wizardPage2 = QtGui.QWizardPage()
        self.wizardPage2.setObjectName("wizardPage2")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.wizardPage2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.groupBox = QtGui.QGroupBox(self.wizardPage2)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.l_name = QtGui.QLineEdit(self.groupBox)
        self.l_name.setObjectName("l_name")
        self.gridLayout.addWidget(self.l_name, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.l_jri = QtGui.QLineEdit(self.groupBox)
        self.l_jri.setObjectName("l_jri")
        self.gridLayout.addWidget(self.l_jri, 1, 1, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.ch_h264 = QtGui.QCheckBox(self.groupBox)
        self.ch_h264.setChecked(True)
        self.ch_h264.setObjectName("ch_h264")
        self.horizontalLayout.addWidget(self.ch_h264)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_5.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(self.wizardPage2)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_4.addWidget(self.label_6)
        self.t_desc = QtGui.QPlainTextEdit(self.groupBox_2)
        self.t_desc.setObjectName("t_desc")
        self.verticalLayout_4.addWidget(self.t_desc)
        self.horizontalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_9 = QtGui.QLabel(self.groupBox_2)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_3.addWidget(self.label_9)
        self.l_key = QtGui.QLineEdit(self.groupBox_2)
        self.l_key.setObjectName("l_key")
        self.verticalLayout_3.addWidget(self.l_key)
        self.label_11 = QtGui.QLabel(self.groupBox_2)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_3.addWidget(self.label_11)
        self.dateEdit = QtGui.QDateEdit(self.groupBox_2)
        self.dateEdit.setDate(QtCore.QDate(2014, 1, 17))
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setObjectName("dateEdit")
        self.verticalLayout_3.addWidget(self.dateEdit)
        self.label_7 = QtGui.QLabel(self.groupBox_2)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_3.addWidget(self.label_7)
        self.t_model = QtGui.QComboBox(self.groupBox_2)
        self.t_model.setEditable(True)
        self.t_model.setObjectName("t_model")
        self.verticalLayout_3.addWidget(self.t_model)
        self.checkBox_2 = QtGui.QCheckBox(self.groupBox_2)
        self.checkBox_2.setChecked(True)
        self.checkBox_2.setObjectName("checkBox_2")
        self.verticalLayout_3.addWidget(self.checkBox_2)
        self.label_8 = QtGui.QLabel(self.groupBox_2)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_3.addWidget(self.label_8)
        self.l_own = QtGui.QLineEdit(self.groupBox_2)
        self.l_own.setEnabled(False)
        self.l_own.setObjectName("l_own")
        self.verticalLayout_3.addWidget(self.l_own)
        self.horizontalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_5.addWidget(self.groupBox_2)
        Wizard.addPage(self.wizardPage2)
        self.wizardPage = QtGui.QWizardPage()
        self.wizardPage.setObjectName("wizardPage")
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.wizardPage)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_10 = QtGui.QLabel(self.wizardPage)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_6.addWidget(self.label_10)
        self.t_clips = QtGui.QTableView(self.wizardPage)
        self.t_clips.setObjectName("t_clips")
        self.verticalLayout_6.addWidget(self.t_clips)
        Wizard.addPage(self.wizardPage)

        self.retranslateUi(Wizard)
        QtCore.QMetaObject.connectSlotsByName(Wizard)
        Wizard.setTabOrder(self.l_name, self.l_jri)
        Wizard.setTabOrder(self.l_jri, self.ch_h264)
        Wizard.setTabOrder(self.ch_h264, self.t_desc)
        Wizard.setTabOrder(self.t_desc, self.l_key)
        Wizard.setTabOrder(self.l_key, self.checkBox_2)
        Wizard.setTabOrder(self.checkBox_2, self.l_own)
        Wizard.setTabOrder(self.l_own, self.l_cardpath)
        Wizard.setTabOrder(self.l_cardpath, self.b_browse)

    def retranslateUi(self, Wizard):
        Wizard.setWindowTitle(QtGui.QApplication.translate("Wizard", "Wizard", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage1.setTitle(QtGui.QApplication.translate("Wizard", "Utilitaire d\'ingest MamIngester", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage1.setSubTitle(QtGui.QApplication.translate("Wizard", "Cet utilitaire vous permettra de suavegarder vos cartes de tournage dans votre MaM et de remplir les métadonnées associées. ", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Wizard", "Choisissez la carte à importer", None, QtGui.QApplication.UnicodeUTF8))
        self.b_browse.setText(QtGui.QApplication.translate("Wizard", "Parcourir…", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage2.setTitle(QtGui.QApplication.translate("Wizard", "Métadonnées e la carte", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage2.setSubTitle(QtGui.QApplication.translate("Wizard", "À cette étape vous devez remplir les informations essentielles de la carte. Les champs marqués d\'un * sont obligatoire", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Wizard", "Info. de base", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Wizard", "Nom de la carte*", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Wizard", "JRI*", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Wizard", "Dans le projet :", None, QtGui.QApplication.UnicodeUTF8))
        self.ch_h264.setText(QtGui.QApplication.translate("Wizard", "Créer un proxy h264", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("Wizard", "Avancé", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Wizard", "Description", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("Wizard", "Mots clés", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("Wizard", "Date de tournage", None, QtGui.QApplication.UnicodeUTF8))
        self.dateEdit.setDisplayFormat(QtGui.QApplication.translate("Wizard", "dd/MM/yyyy", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("Wizard", "Modèle de la camera", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_2.setText(QtGui.QApplication.translate("Wizard", "Propriété de Galaxie Presse*", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Wizard", "Propriétaire", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage.setTitle(QtGui.QApplication.translate("Wizard", "Liste des clips", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPage.setSubTitle(QtGui.QApplication.translate("Wizard", "Voici les cips détectés sur la carte", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("Wizard", "Métadonnées des clips.", None, QtGui.QApplication.UnicodeUTF8))

