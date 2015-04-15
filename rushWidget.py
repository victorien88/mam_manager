__author__ = 'ingest'
from PyQt5 import QtCore
from PyQt5 import  QtWidgets

class RushWidget(QtWidgets.QColumnView):
    def __init__(self,parent=None):
        super(RushWidget,self).__init__(parent)

    def createColumn(self, **kwargs):
        return 0