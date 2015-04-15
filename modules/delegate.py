__author__ = 'ingest'

from PyQt5.QtCore import QModelIndex, Qt, QDate
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QApplication, QItemDelegate, QSpinBox, QTableView,QDateEdit


class SpinBoxDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)


        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, Qt.EditRole)
        normalize = value.split("-")
        date = QDate(int(normalize[2]),int(normalize[1]),int(normalize[0]))
        print(date)
        spinBox.setDate(date)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.date()

        model.setData(index, value.toString("yyyy-MM-dd"), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)