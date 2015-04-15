__author__ = 'ingest'
from PyQt5 import QtCore, QtGui, QtWidgets
from .dataBase import *


class NCollectionModel(QtCore.QAbstractTableModel):
    dbChanged = QtCore.pyqtSignal()
    def __init__(self,indexes,tree, parent = None,  *args):
        QtCore.QAbstractTableModel.__init__(self)
        self.origindexes = indexes
        self.arraydata = self.initData()
        self.headers = self.get_headers()
        self.tree = tree
        self.layoutChanged.emit()
    @db_session
    def initData(self):
        return [a.internalPointer().itemData[0] for a in self.origindexes]

    def refresh_data(self):
        self.layoutAboutToBeChanged.emit()
        self.initData()
        self.layoutChanged.emit()

    def get_headers(self):
        return ["ID", "Nom", "Commentaires"]

    def setHorizontalHeaderLabels(self,headers):

        if len(headers) < self.columnCount():
            raise ImportWarning
        else:
            self.headers = headers
            self.layoutChanged.emit()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.arraydata)

    def columnCount(self,parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.arraydata[index.row()].id
            elif index.column() == 1:
                return self.arraydata[index.row()].name
            elif index.column() == 2:
                return self.arraydata[index.row()].comment
        else:
            return

    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        self.tree.layoutAboutToBeChanged.emit()
        celld = select(g for g in Collection if g == self.arraydata[index.row()]).prefetch(Collection.child)[:]
        cell = celld[0]
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        elif index.column()==1:
            cell.name = value
            self.arraydata[index.row()] = cell
            commit()
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        else:
            return False




    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return "  "
        return

    def flags(self, index):
        if not index.isValid():
            return 0
        if index.column() in [1, 2]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class NProjectGroupModel(NCollectionModel):
    def __init__(self,indexes,tree, parent = None,  *args):
        NCollectionModel.__init__(self, indexes, tree)

    @db_session
    def initData(self):
        return [select(p for p in ProjectGroup if p == a.internalPointer().
            itemData[0]).prefetch(ProjectGroup.clientDefault,
                                  ProjectGroup.defaultFollowingUser)[:][0] for a in self.origindexes]

    def get_headers(self):
        return ["ID", "Nom", "Commentaires","Clients par défaut","Superviseurs par défaut"]
    @db_session
    def data(self, index, role):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole or role==QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.arraydata[index.row()].id
            elif index.column() == 1:
                return self.arraydata[index.row()].name
            elif index.column() == 2:
                return self.arraydata[index.row()].comment
            elif index.column() == 3:
                return ",".join(c.name for c in self.arraydata[index.row()].clientDefault)
            elif index.column() == 4:
                return ",".join(c.name for c in self.arraydata[index.row()].defaultFollowingUser)
        else:
            return



    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        self.tree.layoutAboutToBeChanged.emit()
        celld = select(p for p in ProjectGroup if p == self.arraydata[index.row()]).prefetch(ProjectGroup.child, ProjectGroup.defaultFollowingUser,ProjectGroup.clientDefault)[:]
        cell = celld[0]
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        elif index.column()==1:
            cell.name = value
            self.arraydata[index.row()] = cell
            commit()
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        else:
            return False

class NProjectModel(NCollectionModel):
    def __init__(self,indexes,tree):
        NCollectionModel.__init__(self,indexes,tree)

    def get_headers(self):
        return ["ID","Nom","Commentaire","Réalisteaur"]

    def initData(self):
        return [a.internalPointer().itemData[0] for  a in self.origindexes]


    @db_session
    def data(self, index, role):
        if not index.isValid():
            return None



        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.arraydata[index.row()].id
            elif index.column() == 1:
                return self.arraydata[index.row()].name
            elif index.column() == 2:
                return self.arraydata[index.row()].comment
            elif index.column() == 3:
                return self.arraydata[index.row()].real
        else:
            return

    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        self.tree.layoutAboutToBeChanged.emit()
        celld = select(p for p in Project if p == self.arraydata[index.row()]).prefetch(Project.child)[:]
        cell = celld[0]
        if index.column()==3:
            cell.real = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        elif index.column()==1:
            cell.name = value
            self.arraydata[index.row()] = cell
            commit()
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        else:
            return False

    def flags(self, index):
        if not index.isValid():
            return 0
        if index.column() in (1, 2,3):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class NCardsModel(NCollectionModel):
    def __init__(self,indexes,tree):
        NCollectionModel.__init__(self,indexes,tree)

    def get_headers(self):
        return ["ID","Nom","Commentaires",'JRI',"En Ligne" ,"Date de tournage", "Carte Audio","Disque de Sauvegarde",
                "Date d'ingest","Propriétaire des images","Caméra","Ingesté par"]

    @db_session
    def initData(self):
         return [select(c for c in Cards if c == a.internalPointer().
            itemData[0]).prefetch(Cards.disk)[:][0] for a in self.origindexes]
    @db_session
    def data(self, index, role):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.arraydata[index.row()].id
            elif index.column() == 1:
                return self.arraydata[index.row()].name
            elif index.column() == 2:
                return self.arraydata[index.row()].comment
            elif index.column() == 3:
                return self.arraydata[index.row()].jri
            elif index.column() == 4:
                return "OUI" if self.arraydata[index.row()].on_raid else "NON"
            elif index.column() == 5:
                date = unicode(self.arraydata[index.row()].tournageDate).split('-')
                return "%s-%s-%s"%(date[2],date[1],date[0])
            elif index.column() == 6:
                return "OUI" if self.arraydata[index.row()].audio else "NON"
            elif index.column() == 7:
                return self.arraydata[index.row()].disk.name
            elif index.column() == 8:
                date = unicode(self.arraydata[index.row()].ingestDate).split('-')
                return "%s-%s-%s"%(date[2],date[1],date[0])
            elif index.column() == 9:
                return self.arraydata[index.row()].owner
            elif index.column() == 10:
                return self.arraydata[index.row()].cameraModel
            elif index.column() == 11:
                return self.arraydata[index.row()].ingestedBy
        else:
            return

    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        self.tree.layoutAboutToBeChanged.emit()
        celld = select(g for g in Cards if g == self.arraydata[index.row()]).prefetch(Cards.child,Cards.disk)[:]
        cell = celld[0]
        if index.column()==9:
            cell.owner = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        if index.column()==5:
            cell.tournageDate = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        if index.column()==3:
            cell.jri = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()] = cell
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            commit()
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        elif index.column()==1:
            cell.name = value
            self.arraydata[index.row()] = cell
            commit()
            self.origindexes[index.row()].internalPointer().setData(0,cell)
            self.tree.layoutChanged.emit()
            self.layoutChanged.emit()
            return True
        else:
            return False


    def flags(self, index):
        if not index.isValid():
            return 0
        if index.column() in (1,2,3,5,9):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class NClipsModel(NCollectionModel):
    def __init__(self,indexes, tree):
        NCollectionModel.__init__(self,indexes,tree)

    def get_headers(self):
        return ["ID", "Nom", "Commentaires",'Tags',"pays","ville",'Proxy Généré',"Taille de la vidéo",
                'FPS',"Time Code start","Duréé","Codec","Pistes audio"]

    @db_session
    def initData(self):
         return [select(c for c in Assets if c == a.internalPointer().
            itemData[0]).prefetch(Assets.tag)[:][0] for a in self.origindexes]
