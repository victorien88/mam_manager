__author__ = 'ingest'
from .dataBase import *
from PyQt5 import QtCore, QtGui
from modules.models import ListModel, GenericListModel, ProjectGroupModel,\
    CollectionModel , ProjectModel, CardModel, ClipModel, GroupModel, Clientmodel, Usermodel


class Selector(object):
    def __init__(self,collList, gList, pList, cList, clList, addcoll,removeColl,
                 addGroup, removeGroup, addProject,removeProject, moveGroup,
                 moveProject,addCard,removeCard,moveCard,metadatView,b_chg_rights, mainWin):
        self.b_chg_rights = b_chg_rights
        self.moveGroup = moveGroup
        self.removeColl = removeColl
        self.addcoll = addcoll
        self.addGroup = addGroup
        self.removeGroup = removeGroup
        self.addProject = addProject
        self.removeProject = removeProject
        self.moveProject = moveProject
        self.addCard = moveProject
        self.collView = collList
        self.removeCard = moveProject
        self.moveCard = moveProject
        self.groupView = gList
        self.projectView =pList
        self.cardView = cList
        self.clipView = clList
        self.addCard = addCard
        self.removeCard = removeCard
        self.MainWindow = mainWin
        self.moveCard = moveCard
        self.noModel = ListModel([],'')
        self.metadataView = metadatView
        self.initCollections()
        self.addGroup.setEnabled(False)


    def reInitCards(self):
        self.MainWindow.stackedWidget_3.setCurrentIndex(0)
        self.MainWindow.listView_3.selectionModel().clearSelection()
        model = ListModel(self.MainWindow.listView_2.model().get_children(self.MainWindow.listView_2.selectionModel().selectedIndexes()[0].row()), "card")
        self.cardView.setModel(model)
        pysidefix = self.cardView.selectionModel()
        self.cardView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.cardView))

    def reInitProjects(self):
        self.MainWindow.listView_2.selectionModel().clearSelection()
        model = ListModel(self.MainWindow.listView.model().get_children(self.MainWindow.listView.selectionModel().selectedIndexes()[0].row()), "project")
        self.projectView.setModel(model)
        pysidefix = self.projectView.selectionModel()
        self.projectView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.projectView))

    def initCollections(self):
        self.MainWindow.stackedWidget_3.setCurrentIndex(0)
        self.collView.setModel(ListModel(self.get_collections(),'collection'))
        a  = self.collView.selectionModel()
        self.collView.selectionModel().selectionChanged.connect(lambda : self.loadChild(self.collView))
    def reinitCollections(self):
        self.MainWindow.collection_list.selectionModel().clearSelection()
        self.MainWindow.stackedWidget_3.setCurrentIndex(0)
        self.collView.setModel(ListModel(self.get_collections(),'collection'))
        a  = self.collView.selectionModel()
        self.collView.selectionModel().selectionChanged.connect(lambda : self.loadChild(self.collView))




    def reInitGroups(self):
        self.MainWindow.listView.selectionModel().clearSelection()
        model = ListModel(self.MainWindow.collection_list.model().get_children(self.MainWindow.collection_list.selectionModel().selectedIndexes()[0].row()), "group")
        self.groupView.setModel(model)
        pysidefix = self.groupView.selectionModel()
        self.groupView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.groupView))


    def loadChild(self, widget):

        name = widget.objectName()

        if name == "collection_list":
            self.MainWindow.stackedWidget_3.setCurrentIndex(0)
            if widget.selectionModel().hasSelection():
                self.metadataView.setModel(CollectionModel(widget.model(),widget.model().getItems(
                self.MainWindow.collection_list.selectionModel().selectedIndexes()),['ID','Nom','Description']))
                self.metadataView.resizeColumnsToContents()
            else:
                self.metadataView.setModel(QtGui.QStandardItemModel())


        if name == "listView":
            self.MainWindow.stackedWidget_3.setCurrentIndex(0)
            if widget.selectionModel().hasSelection():
                self.metadataView.setModel(ProjectGroupModel(widget.model(),widget.model().getItems(
                self.MainWindow.listView.selectionModel().selectedIndexes()),['ID','Nom','Description',
                                                                         "Utilisateurs par défaut",
                                                                         "Clients par défaut"]))
                self.metadataView.resizeColumnsToContents()
            else:
                self.metadataView.setModel(CollectionModel(self.MainWindow.collection_list.model(),self.MainWindow.collection_list.model().getItems(
                self.MainWindow.collection_list.selectionModel().selectedIndexes()),['ID','Nom','Description']))
                self.metadataView.resizeColumnsToContents()
        if name == "listView_4":
            self.MainWindow.stackedWidget_3.setCurrentIndex(0)
            if widget.selectionModel().hasSelection():

                self.metadataView.setModel(ClipModel(widget.model(),widget.model().getItems(
                self.MainWindow.listView_4.selectionModel().selectedIndexes()),['id','nom','commentaires',"tags","Pays","Ville",'proxy généré', 'adresse du proxy',
                 "taille","framerate","durée en secondes", "Nombre d'images", "Time Code de départ", "codec"]))
                self.metadataView.resizeColumnsToContents()
            else:
                self.metadataView.setModel(QtGui.QStandardItemModel())
        if name == "listView_2":
            self.MainWindow.stackedWidget_3.setCurrentIndex(0)
            if widget.selectionModel().hasSelection():

                self.metadataView.setModel(ProjectModel(widget.model(),widget.model().getItems(
                self.MainWindow.listView_2.selectionModel().selectedIndexes()),['ID','Nom','Description','Réalisateur']))
                self.metadataView.resizeColumnsToContents()
            else:
                self.metadataView.setModel(ProjectGroupModel(self.groupView.model(),self.groupView.model().getItems(
                self.MainWindow.listView.selectionModel().selectedIndexes()),['ID','Nom','Description',
                                                                         "Utilisateurs par défaut",
                                                                         "Clients par défaut"]))
                self.metadataView.resizeColumnsToContents()

        if name == "listView_3":
            if widget.selectionModel().hasSelection():
                card = widget.model().getItems(self.MainWindow.listView_3.selectionModel().selectedIndexes())
                with db_session:
                    if card[0].stat == 0:
                        self.MainWindow.stackedWidget_3.setCurrentIndex(1)
                    else:
                        self.MainWindow.stackedWidget_3.setCurrentIndex(0)
                if len(self.MainWindow.listView_3.selectionModel().selectedIndexes()) > 1:
                    self.MainWindow.stackedWidget_3.setCurrentIndex(0)



                header = ['id','Nom','Description','Disque', 'Online','jri',"Date d'ingest","Date de Tournage","propriétaire","modèle de caméra","Copié"]
                self.metadataView.setModel(CardModel(widget.model(),widget.model().getItems(self.MainWindow.listView_3.selectionModel().selectedIndexes()),header))
                self.metadataView.resizeColumnsToContents()
            else:
                self.metadataView.setModel(ProjectGroupModel(self.groupView.model(),self.groupView.model().getItems(
                self.MainWindow.listView.selectionModel().selectedIndexes()),['ID','Nom','Description',
                                                                         "Utilisateurs par défaut",
                                                                         "Clients par défaut"]))
                self.metadataView.resizeColumnsToContents()

        if len(widget.selectionModel().selectedIndexes())>1: #multiple item selected

            if name == "collection_list":
                self.addGroup.setEnabled(False)
                self.removeGroup.setEnabled(False)
                self.moveGroup.setEnabled(False)
                self.removeCard.setEnabled(False)
                self.groupView.setModel(self.noModel)
                self.projectView.setModel(self.noModel)
                self.addProject.setEnabled(False)
                self.removeProject.setEnabled(False)
                self.moveProject.setEnabled(False)
                self.moveCard.setEnabled(False)
                self.addCard.setEnabled(False)
                self.cardView.setModel(self.noModel)
                self.clipView.setModel(self.noModel)




            if name == "listView":
                self.removeGroup.setEnabled(True)

                self.projectView.setModel(self.noModel)
                self.addProject.setEnabled(False)
                self.removeProject.setEnabled(False)
                self.moveProject.setEnabled(False)
                self.moveCard.setEnabled(False)
                self.addCard.setEnabled(False)
                self.cardView.setModel(self.noModel)
                self.clipView.setModel(self.noModel)

                self.moveGroup.setEnabled(True)


            if name == "listView_2":
                self.addProject.setEnabled(True)
                self.moveProject.setEnabled(True)
                self.removeProject.setEnabled(True)
                self.moveCard.setEnabled(False)
                self.addCard.setEnabled(False)
                self.cardView.setModel(self.noModel)
                self.clipView.setModel(self.noModel)


            if name == "listView_3":
                self.addCard.setEnabled(True)
                self.moveCard.setEnabled(True)
                self.removeCard.setEnabled(True)
                self.clipView.setModel(self.noModel)




        else:
            if len(widget.selectionModel().selectedIndexes()) == 1 : #Single selection



                if name == "collection_list":
                    self.removeColl.setEnabled(True)
                    self.addGroup.setEnabled(True)
                    model = ListModel(widget.model().get_children(self.MainWindow.collection_list.selectionModel().selectedIndexes()[0].row()), "group")

                    self.groupView.setModel(model)
                    a  = self.groupView.selectionModel()
                    self.groupView.selectionModel().selectionChanged.connect(lambda : self.loadChild(self.groupView))
                    self.addProject.setEnabled(False)
                    self.removeProject.setEnabled(False)
                    self.moveProject.setEnabled(False)
                    self.moveCard.setEnabled(False)
                    self.addCard.setEnabled(False)
                    self.removeCard.setEnabled(False)
                    self.projectView.setModel(self.noModel)
                    self.cardView.setModel(self.noModel)
                    self.clipView.setModel(self.noModel)

                if name == "listView_3":
                    model = ListModel(widget.model().get_children(self.MainWindow.listView_3.selectionModel().selectedIndexes()[0].row()), "clip")
                    self.clipView.setModel(model)
                    pysidefix = self.clipView.selectionModel()
                    self.clipView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.clipView))
                    self.removeCard.setEnabled(True)
                    self.moveCard.setEnabled(True)


                if name == "listView":
                    self.moveGroup.setEnabled(True)
                    model = ListModel(widget.model().get_children(self.MainWindow.listView.selectionModel().selectedIndexes()[0].row()), "project")
                    self.projectView.setModel(model)
                    pysidefix = self.projectView.selectionModel()
                    self.projectView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.projectView))
                    self.removeGroup.setEnabled(True)
                    self.b_chg_rights.setEnabled(True)
                    self.addProject.setEnabled(True)
                    self.removeProject.setEnabled(False)
                    self.moveProject.setEnabled(False)
                    self.moveCard.setEnabled(False)
                    self.addCard.setEnabled(False)
                    self.cardView.setModel(self.noModel)
                    self.clipView.setModel(self.noModel)

                else:
                    self.b_chg_rights.setEnabled(False)

                if name == "listView_2":
                    self.removeProject.setEnabled(True)
                    self.moveProject.setEnabled(True)
                    model = ListModel(widget.model().get_children(self.MainWindow.listView_2.selectionModel().selectedIndexes()[0].row()), "card")
                    self.cardView.setModel(model)
                    pysidefix = self.cardView.selectionModel()
                    self.cardView.selectionModel().selectionChanged.connect(lambda: self.loadChild(self.cardView))
                    self.addCard.setEnabled(True)
                    self.removeCard.setEnabled(False)

                    self.clipView.setModel(self.noModel)


            else: #No item selection###############################

                if name == "collection_list":
                    self.metadataView.setModel(self.noModel)
                    self.removeColl.setEnabled(False)
                    self.moveGroup.setEnabled(False)
                    self.addGroup.setEnabled(False)
                    self.groupView.setModel(self.noModel)
                    self.removeGroup.setEnabled(False)
                    self.projectView.setModel(self.noModel)
                    self.addProject.setEnabled(False)
                    self.removeProject.setEnabled(False)
                    self.moveProject.setEnabled(False)
                    self.moveCard.setEnabled(False)
                    self.removeCard.setEnabled(False)
                    self.addCard.setEnabled(False)
                    self.cardView.setModel(self.noModel)
                    self.clipView.setModel(self.noModel)



                if name == "listView":
                    self.moveGroup.setEnabled(False)
                    self.removeGroup.setEnabled(False)
                    self.projectView.setModel(self.noModel)
                    self.addProject.setEnabled(False)
                    self.removeProject.setEnabled(False)
                    self.moveProject.setEnabled(False)
                    self.moveCard.setEnabled(False)
                    self.removeCard.setEnabled(False)
                    self.addCard.setEnabled(False)
                    self.cardView.setModel(self.noModel)
                    self.clipView.setModel(self.noModel)


                if name == "listView_2":
                    self.removeProject.setEnabled(False)
                    self.moveProject.setEnabled(False)
                    self.moveCard.setEnabled(False)
                    self.removeCard.setEnabled(False)
                    self.addCard.setEnabled(False)
                    self.cardView.setModel(self.noModel)
                    self.clipView.setModel(self.noModel)

                if name =="listView_3":
                    self.moveCard.setEnabled(False)
                    self.removeCard.setEnabled(False)
                    self.clipView.setModel(self.noModel)

    @db_session
    def get_projects_groups(self):
            qu = select(c for c in ProjectGroup)[:]
            return qu
    @db_session
    def get_collections(self):
        qu = select(c for c in Collection).order_by(Collection.id)[:]
        return qu
