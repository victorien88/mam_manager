# -*- coding: utf-8 -*-

__author__ = 'fcp6'
from PyQt5 import QtCore, QtGui
from .dataBase import *
import datetime


class Usermodel(QtCore.QAbstractTableModel):

    Mimetype = 'application/vnd.row.list'

    def __init__(self, parent=None):
        super(Usermodel, self).__init__(parent)
        with db_session:
            self.__data = select(u for u in Users if not u.system).order_by(Users.id)[:]

    def getUsername(self,index):
        if index.column() == 1:
                return self.__data[index.row()].name


    def getItemFromIndex(self,index):
        print(self.__data)
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]

    def refresh(self):
        self.layoutAboutToBeChanged.emit()
        with db_session:
            self.__data = select(u for u in Users if not u.system).order_by(Users.id)[:]
        self.layoutChanged.emit()

    def getSubModel(self,index):
        print("submodel")
        a = GroupModel(user=self.__data[index.row()])
        return a

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() > len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return self.__data[index.row()].name
            if index.column() == 1:
                return self.__data[index.row()].mail
            if index.column() == 2:
                return self.__data[index.row()].passw
            if index.column() == 3:
                return 3 if self.__data[index.row()].admin else 0
            if index.column() == 4:
                return 3 if self.__data[index.row()].canValidate else 0
            if index.column() == 5:
                return 3 if self.__data[index.row()].canSeeMasters else 0

        return None

    def flags(self, index):
        if index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsDropEnabled


    def insertRows(self, row, count, parent=QtCore.QModelIndex()):

        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [''] * count
        self.endInsertRows()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
            if index.isValid()], key=lambda index: index.row())
        encodedData = '\n'.join(self.data(index, QtCore.Qt.DisplayRole)
                for index in sortedIndexes)
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, encodedData)
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def columnCount(self, parent=QtCore.QModelIndex()):

            with db_session:
                try :
                    c1 = Client[1]
                    return len(list(c1.to_dict().keys()))
                except:
                    return 1




    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        with db_session:
            if index.column() == 0:
                get(u for u in Users if u == self.__data[index.row()]).name = value
            if index.column() == 1:
                get(u for u in Users if u == self.__data[index.row()]).mail = value
            if index.column() == 2:
                get(u for u in Users if u == self.__data[index.row()]).passw = value
            if index.column() == 3:
                get(u for u in Users if u == self.__data[index.row()]).admin = value
            if index.column() == 4:
                get(u for u in Users if u == self.__data[index.row()]).canValidate = value
            if index.column() == 5:
                print("master TRIGGERED")
                get(u for u in Users if u == self.__data[index.row()]).canSeeMasters = value
        self.layoutAboutToBeChanged.emit()
        self.refresh()
        self.layoutChanged.emit()
        return True
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction



class UserAndGroupModel(Usermodel):
    def __init__(self,group=None):
        print(group)
        with db_session:

            super(UserAndGroupModel,self).__init__()
            if group:
                self.group =  get(g for g in ProjectGroup if g ==group)
                self.__data = self.get_data()
            else:
                self.group = None
                self.__data = self.get_default()
                print(self.__data)

    def save_default(self,group):
        with db_session:
            group = get(g for g in ProjectGroup if g == group)
            print(self.__data)
            for user in self.__data:
                if user['right'] == 2:
                    get(c for c in Users if c.name == user['name']).defaulValidationGroup.add(group)
                else:
                    get(c for c in Users if c.name == user['name']).defaulValidationGroup.remove(group)
    def get_default(self):
        users = select(u for u in Users if not u.system).order_by(Users.id)[:]
        data = []
        for u in users:
                line = {}
                line["name"] = u.name
                line['right'] = 0
                data.append(line)
        return data


    def get_data(self):
            users = select(u for u in Users if not u.system).order_by(Users.id)[:]
            data = []
            for u in users:
                line = {}
                line["name"] = u.name
                line['right'] = 2 if self.group in u.defaulValidationGroup else 0
                data.append(line)
            return data

    def insert_in_db(self):
        with db_session:
            group = get(g for g in ProjectGroup if g == self.group)
            for user in self.__data:
                if user['right'] == 2:
                    get(u for u in Users if u.name == user['name']).defaulValidationGroup.add(group)
                else:

                    get(u for u in Users if u.name == user['name']).defaulValidationGroup.remove(group)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
         if index.isValid():
                self.layoutAboutToBeChanged.emit()
                print(value)
                self.__data[index.row()]['right'] = value
                self.layoutChanged.emit()
                return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        with db_session:
            if not index.isValid():
                return None
            if index.row() > len(self.__data):
                return None
            
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if index.column() == 0:
                    return self.__data[index.row()]['name']
            if role == QtCore.Qt.CheckStateRole:
                    return QtCore.Qt.Checked if self.__data[index.row()]['right'] == 2 else QtCore.Qt.Unchecked

        return None

    
    def flags(self, index):

        if index.isValid():
            #flags |= QtCore.Qt.ItemIsEditable
            return QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable
        else:
            return QtCore.Qt.ItemIsDropEnabled

class ClientAnGroupModel(UserAndGroupModel):
    def __init__(self, group=None):
        with db_session:

            super(ClientAnGroupModel, self).__init__(group)
            if group:
                self.group = get(g for g in ProjectGroup if g == group)
                self.__data = self.get_data()
            else:
                self.group = None
                self.__data = self.get_default()
    def save_default(self,group):
        with db_session:
            group = get(g for g in ProjectGroup if g == group)
            for user in self.__data:
                if user['right'] == 2:
                    get(c for c in Client if c.name == user['name']).defaultGroup.add(group)
                else:
                    get(c for c in Client if c.name == user['name']).defaultGroup.remove(group)
    def get_default(self):
        users = select(u for u in Client).order_by(Client.id)[:]
        data = []
        for u in users:
                line = {}
                line["name"] = u.name
                line['right'] = 0
                data.append(line)
        return data

    def get_data(self):
            data = []
            users = select(u for u in Client).order_by(Client.id)[:]
            for u in users:
                line = {}
                line["name"] = u.name
                line['right'] = 2 if self.group in u.defaultGroup else 0
                data.append(line)
            return data

    def insert_in_db(self):
         print(self.__data)
         with db_session:
            group = get(g for g in ProjectGroup if g == self.group)
            for user in self.__data:
                if user['right'] == 2:
                    get(c for c in Client if c.name == user['name']).defaultGroup.add(group)
                else:
                    get(c for c in Client if c.name == user['name']).defaultGroup.remove(group)
    def setData(self, index, value, role=QtCore.Qt.EditRole):
         if index.isValid():
                self.layoutAboutToBeChanged.emit()
                print(value)
                self.__data[index.row()]['right'] = value
                self.layoutChanged.emit()
                return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        with db_session:
            if not index.isValid():
                return None
            if index.row() > len(self.__data):
                return None

            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if index.column() == 0:
                    return self.__data[index.row()]['name']
            if role == QtCore.Qt.CheckStateRole:
                    return QtCore.Qt.Checked if self.__data[index.row()]['right'] == 2 else QtCore.Qt.Unchecked

        return None






class Clientmodel(QtCore.QAbstractTableModel):

    Mimetype = 'application/vnd.row.list'

    def __init__(self, parent=None):
        super(Clientmodel, self).__init__(parent)
        with db_session:
            self.__data = select(c for c in Client).order_by(Client.id)[:]



    def getItemFromIndex(self,index):
        print(self.__data)
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]

    def refresh(self):
        self.layoutAboutToBeChanged.emit()
        with db_session:
            self.__data = select(c for c in Client).order_by(Client.id)[:]
        self.layoutChanged.emit()

    def getSubModel(self,index):
        print("submodel")
        a = GroupModel(client=self.__data[index.row()])
        return a

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() > len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:

            if index.column() == 0:
                return self.__data[index.row()].name
            if index.column() == 1:
                return self.__data[index.row()].completeName
            if index.column() == 2:
                return self.__data[index.row()].passWord
            if index.column() == 3:
                return self.__data[index.row()].company
            if index.column() == 4:
                return self.__data[index.row()].mail
            if index.column() == 5:
                return GroupModel()

        return None

    def flags(self, index):
        if index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsDropEnabled



    def insertRows(self, row, count, parent=QtCore.QModelIndex()):

        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [''] * count
        self.endInsertRows()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
            if index.isValid()], key=lambda index: index.row())
        encodedData = '\n'.join(self.data(index, QtCore.Qt.DisplayRole)
                for index in sortedIndexes)
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, encodedData)
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def columnCount(self, parent=QtCore.QModelIndex()):

            with db_session:
                try :
                    c1 = Client[1]
                    return len(list(c1.to_dict().keys()))
                except:
                    return 1



    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        with db_session:
            if index.column() == 0:
                get(c for c in Client if c == self.__data[index.row()]).name = value

            if index.column() == 1:
                get(c for c in Client if c == self.__data[index.row()]).completeName = value
            if index.column() == 2:
                get(c for c in Client if c == self.__data[index.row()]).passWord = value
            if index.column() == 3:
                get(c for c in Client if c == self.__data[index.row()]).company = value
            if index.column() == 4:
                get(c for c in Client if c == self.__data[index.row()]).mail = value
        self.layoutAboutToBeChanged.emit()
        self.refresh()
        self.layoutChanged.emit()
        return True
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction





class GroupModel(QtCore.QAbstractListModel):

    Mimetype = 'application/vnd.row.list'

    def __init__(self, client = None, user=None, parent=None):
        super(GroupModel, self).__init__(parent)
        self.client = client
        self.user = user
        with db_session:
            self.__data = []
            data = select(g for g in ProjectGroup).order_by(ProjectGroup.id)[:]

            if client:
                print("client : %s"%client)
                cli = get(c for c in Client if c == client)
                if cli.defaultGroup:
                    for i in data:
                        stat = 2 if i in cli.defaultGroup else 0
                        self.__data.append({'object':i,'state':stat})
                else:
                    for i in data:
                        self.__data.append({'object':i,'state':0})
            elif user:
                print("user : %s"%user)
                cli = get(u for u in Users if u == user)
                if cli.defaulValidationGroup:
                    for i in data:
                        stat = 2 if i in cli.defaulValidationGroup else 0
                        self.__data.append({'object':i,'state':stat})
                else:
                    for i in data:
                        self.__data.append({'object':i,'state':0})
            else:
                for i in data:
                    self.__data.append({'object':i,'state':0})

    def instertInDb(self):
        if self.client:
            with db_session:
                client = get(c for c in Client if c == self.client)
                for line in self.__data:
                    if line['state'] == 2:
                        group = get(g for g in ProjectGroup if g == line['object'])
                        client.defaultGroup.add(group)
                    else:
                        group = get(g for g in ProjectGroup if g == line['object'])
                        client.defaultGroup.remove(group)
        if self.user:
            with db_session:
                user = get(u for u in Users if u == self.user)
                for line in self.__data:
                    if line['state'] == 2:
                        group = get(g for g in ProjectGroup if g == line['object'])
                        user.defaulValidationGroup.add(group)
                    else:
                        group = get(g for g in ProjectGroup if g == line['object'])
                        user.defaulValidationGroup.remove(group)

    def getItemFromIndex(self,index):
        print(self.__data)
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]

    def setData(self,index,value,role=QtCore.Qt.EditRole):
            if index.isValid():
                self.layoutAboutToBeChanged.emit()
                print(value)
                self.__data[index.row()]['state'] = value
                self.layoutChanged.emit()
                return True
            return False


    def get_dict(self):
        return self.__data
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:

            if not index.isValid():
                return None

            if index.row() > len(self.__data):
                return None

            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                return self.__data[index.row()]['object'].name

        if role == QtCore.Qt.CheckStateRole:
            if self.__data[index.row()]['state'] == 2:
                return QtCore.Qt.Checked

            else:
                return QtCore.Qt.Unchecked
    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return True
        if not data.hasFormat(self.Mimetype):
            return False
        if column > 0:
            return False

        strings = str(data.data(self.Mimetype)).split('\n')
        self.insertRows(row, len(strings))
        for i, text in enumerate(strings):
            self.setData(self.index(row + i, 0), text)

        return True





    def flags(self, index):

        if index.isValid():
            #flags |= QtCore.Qt.ItemIsEditable
            return QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable
        else:
            return QtCore.Qt.ItemIsDropEnabled



    def insertRows(self, row, count, parent=QtCore.QModelIndex()):

        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [''] * count
        self.endInsertRows()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
            if index.isValid()], key=lambda index: index.row())
        encodedData = '\n'.join(self.data(index, QtCore.Qt.DisplayRole)
                for index in sortedIndexes)
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, encodedData)
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)




    def supportedDropActions(self):
        return QtCore.Qt.MoveAction


class DiskModel(QtCore.QAbstractTableModel):
    def __init__(self,pool,data=None, parent=None):
        super(DiskModel, self).__init__(parent)

        self.pool = pool
        print(self.pool)
        self.__data = []
        self.current = None
        self.refresh()
        print(self.current)
        print(data)

    def refresh(self):
        with db_session:
            disks = select(d for d in Disk)[:]
            self.__data = [[a.name, a.online, a.current, a.mountPoint,a.verificationKey,a.id,False,a.free,a]
                           for a in disks]
            try:
                self.current = [i for i in range(0,len(self.__data)) if self.__data[i][2]][0]
            except:
                self.current = None

    def get_disk(self,index):
        '''
        :returns disk object according to QModelIndex
        '''
        return self.__data[index.row()][8]


    def getData(self):
        return self.__data

    def setCurrent(self,row):
        self.layoutAboutToBeChanged.emit()
        try:
            self.__data[self.current][2]=False
        except TypeError:
            pass

        self.current = row.row()
        self.pool.set_default(self.__data[self.current][8])

        self.__data[row.row()][2]=True

        self.layoutChanged.emit()
        print(self.current)



    def rowCount(self, index=QtCore.QModelIndex()):
        """ Returns the number of rows the model holds. """
        return len(self.__data)

    def columnCount(self, index=QtCore.QModelIndex()):
        """ Returns the number of columns the model holds. """
        return len(self.__data[0]) if self.__data else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None (PySide equivalent of QT's
            "invalid QVariant").
        """
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole:
            if self.__data[index.row()][1] == True:
                if self.__data[index.row()][2] == True:
                    return "%s - Par défaut"%(self.__data[index.row()][index.column()])
                else:
                    return self.__data[index.row()][index.column()]
            else:
                return "%s - offline"%(self.__data[index.row()][index.column()])

        if role == QtCore.Qt.EditRole:
            return self.__data[index.row()][index.column()]




        if role == QtCore.Qt.ForegroundRole:

            if self.__data[index.row()][2]:
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.red))
            if self.__data[index.row()][1]:

                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.black))
            else:
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.gray))





        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed. """
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Name"


        return None

    def getAttrib(self,index):
        return self.__data[index.row()][0],self.__data[index.row()][1],self.__data[index.row()][2],\
               self.__data[index.row()][3],self.__data[index.row()][6],self.__data[index.row()][7]

    def insertRows(self, position,data, rows=1, index=QtCore.QModelIndex()):
        """ Insert a row into the model. """
        self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)

        for row in range(rows):
            print(row)
            self.__data.insert(position + row, data)
            try:
                self.__data[self.current+1][2]=False
            except:
                pass
            self.current = row


            self.__data[row][2]=True

        self.endInsertRows()
        self.layoutChanged.emit()
        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        """ Remove a row from the model. """
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows - 1)

        del self.__data[position:position+rows]

        self.endRemoveRows()
        return True

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Adjust the data (set it to <value>) depending on the given
            index and role.
        """
        if role != QtCore.Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(self.__data):
            address = self.__data[index.row()]
            if index.column() == 0:
                address["name"] = value
            elif index.column() == 1:
                address["address"] = value
            else:
                return False

            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return QtCore.Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index))

class GenericListModel(QtCore.QAbstractListModel):

    Mimetype = 'application/vnd.row.list'

    def __init__(self,  data, parent=None):
        super(GenericListModel, self).__init__(parent)
        self.__data = data

    def getItemFromIndex(self,index):
        print(self.__data)
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]

            return [self.__data[a.row()] for a in indexes]
    def refresh(self):
        self.layoutAboutToBeChanged.emit()
        self.__data = select(u for u in Users)[:]
        self.layoutChanged.emit()


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() > len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.__data[index.row()].name

        return None

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return True
        if not data.hasFormat(self.Mimetype):
            return False
        if column > 0:
            return False

        strings = str(data.data(self.Mimetype)).split('\n')
        self.insertRows(row, len(strings))
        for i, text in enumerate(strings):
            self.setData(self.index(row + i, 0), text)

        return True

    def flags(self, index):
        flags = super(GenericListModel, self).flags(index)

        if index.isValid():
            #flags |= QtCore.Qt.ItemIsEditable
            flags |= QtCore.Qt.ItemIsDragEnabled
        else:
            flags = QtCore.Qt.ItemIsDropEnabled

        return flags

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):

        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [''] * count
        self.endInsertRows()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
            if index.isValid()], key=lambda index: index.row())
        encodedData = '\n'.join(self.data(index, QtCore.Qt.DisplayRole)
                for index in sortedIndexes)
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, encodedData)
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)


    @db_session
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if self.type == "group":
            cell = select(g for g in ProjectGroup)[:]
            cell[index.row()].name = value
            self.__data[index.row()] = cell[index.row()]
        if self.type == "project":

            cell = get(p for p in Project if p == self.__data[index.row()])
            cell.name = value
            self.__data[index.row()] = cell
        if self.type == "card":

            cell = get(c for c in Cards if c == self.__data[index.row()])
            cell.name = value
            self.__data[index.row()] = cell
        commit()
        self.dataChanged.emit()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction



class DiskListModel(GenericListModel):
    def __init__(self,  data, parent=None):
        super(DiskListModel, self).__init__(parent)
        self.__data = data
        print(self.__data)
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if index.row() > len(self.__data):
            return None
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.__data[index.row()]['path']

        return None


    def flags(self, index):

        if self.__data[index.row()]['empty']and not  self.__data[index.row()]['used']  :
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return
    def getItemFromIndex(self,index):
        print(self.__data)
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]


class ListModel(QtCore.QAbstractListModel):

    Mimetype = 'application/vnd.row.list'

    def __init__(self,  data, type, parent=None):
        super(ListModel, self).__init__(parent)
        self.__data = data
        self.type = type
    def refresh(self):
        if self.type == "collection":
            self.layoutAboutToBeChanged.emit()
            self.__data = select(c for c in Collection).order_by(Collection.id)[:]
            self.layoutChanged.emit()


        if self.type == "group":
            self.layoutAboutToBeChanged.emit()
            self.__data = select(c for c in ProjectGroup)[:]
            self.layoutChanged.emit()
        if self.type == "project":
            self.layoutAboutToBeChanged.emit()
            new_data = select(p for p in Project if p in self.__data)[:]
            self.__data = new_data
            self.layoutChanged.emit()
        if self.type == "card" :
            self.layoutAboutToBeChanged.emit()
            new_data = select(c for c in Cards if c in self.__data)[:]
            self.__data = new_data
            self.layoutChanged.emit()
        if self.type == "clip" :
            self.layoutAboutToBeChanged.emit()
            new_data = select(a for a in Assets if a in self.__data).order_by(Assets.name)[:]
            self.__data = new_data
            self.layoutChanged.emit()






    def hasList(self):
        if len(self.__data)>0:
            return True
        else:
            return False
    @db_session
    def get_children(self,index):
        if self.type == "collection":


            return select(g for g in ProjectGroup if g.collection == self.__data[index])[:]
        if self.type == "group":
            print("selecting projects")
            print(select(p for p in Project if p.group == self.__data[index])[:])
            return select(p for p in Project if p.group == self.__data[index])[:]
        if self.type == "project":

            return select(c for c in Cards if c.project == self.__data[index])[:]
        if self.type == "card":
            return select(a for a in Assets if a.card == self.__data[index]).order_by(Assets.name)[:]

    def getItem(self,index):
        try:
            return self.__data[index.row()]
        except:
            return self.__data[index]
    def getItems(self,indexes):

            return [self.__data[a.row()] for a in indexes]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() > len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.__data[index.row()].name

        return None

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return True
        if not data.hasFormat(self.Mimetype):
            return False
        if column > 0:
            return False

        strings = str(data.data(self.Mimetype)).split('\n')
        self.insertRows(row, len(strings))
        for i, text in enumerate(strings):
            self.setData(self.index(row + i, 0), text)

        return True

    def flags(self, index):
        flags = super(ListModel, self).flags(index)
        if self.type ==  "clip":
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        else:
            if index.isValid():
                flags |= QtCore.Qt.ItemIsEditable
                flags |= QtCore.Qt.ItemIsDragEnabled
            else:
                flags = QtCore.Qt.ItemIsDropEnabled

            return flags

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):

        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [''] * count
        self.endInsertRows()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
            if index.isValid()], key=lambda index: index.row())
        encodedData = '\n'.join(self.data(index, QtCore.Qt.DisplayRole)
                for index in sortedIndexes)
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, encodedData)
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    @db_session
    def chColl(self,group,coll):
        groupObj = get(g for g in ProjectGroup if g == group)
        newColl = get(c for c in Collection if c == coll)
        groupObj.collection = newColl

    @db_session
    def chGroup(self,project,group):
        projectObj = get(p for p in Project if p == project)
        newgroup = get(g for g in ProjectGroup if g == group)
        projectObj.group = newgroup
    @db_session
    def chProj(self,card,project):
        cardObj = get(c for c in Cards if c == card)
        proj = get(p for p in Project if p == project)
        cardObj.project = proj







    def setData(self, index, value, role=QtCore.Qt.EditRole):
        with db_session:
            print(self.type)
            if not index.isValid() or role != QtCore.Qt.EditRole:
                return False

            if self.type == "collection":
                cell = get(c for c in Collection if c == self.__data[index.row()])
                print(value)
                cell.name = value
                self.__data[index.row()] = cell


            if self.type == "group":
                cell = get(g for g in ProjectGroup if g == self.__data[index.row()])
                cell.name = value
                self.__data[index.row()] = cell
            if self.type == "project":

                cell = get(p for p in Project if p == self.__data[index.row()])
                cell.name = value
                self.__data[index.row()] = cell
            if self.type == "card":

                cell = get(c for c in Cards if c == self.__data[index.row()])
                cell.name = value
                self.__data[index.row()] = cell
            commit()
            self.dataChanged.emit()
            return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction



class ProjectGroupModel(QtCore.QAbstractTableModel):
    def __init__(self, listModel, group, headers, parent = None,  *args):
        QtCore.QAbstractTableModel.__init__(self)
        self.arraydata = self.getMetadata(group)
        self.headers = headers
        self.layoutChanged.emit()
        self.group =group
        self.listModel = listModel


    @db_session
    def getMetadata(self,group):
        group = [get(g for g in ProjectGroup if g == a) for a in group]
        return [[a.id,a.name,a.comment,", ".join([c.name for c in a.defaultFollowingUser]),
                 ", ".join([u.name for u in a.clientDefault])] for a in group]


    def setHorizontalHeaderLabels(self,headers):

        if len(headers) < self.columnCount():
            raise ImportWarning
        else:
            self.headers = headers
            self.layoutChanged.emit()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.arraydata)

    def columnCount(self,parent=None, *args, **kwargs):
        return len(self.arraydata[0])

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole:

            return self.arraydata[index.row()][index.column()]


        if role == QtCore.Qt.EditRole:

                return self.arraydata[index.row()][index.column()]



    @db_session
    def setData(self, index, value, role=None):
        print(index.row())
        print(index.column())

        self.layoutAboutToBeChanged.emit()

        cell = get(g for g in ProjectGroup if g == self.group[index.row()])
        if index.column()==2:
            cell = get(g for g in ProjectGroup if g == self.group[index.row()])
            cell.comment = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==1:
            cell = get(g for g in ProjectGroup if g == self.group[index.row()])
            cell.name = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()



        self.layoutChanged.emit()



    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return "  "
        return
    def flags(self, index):
        if index.column() in [1,2]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable




class CollectionModel(QtCore.QAbstractTableModel):
    def __init__(self, listModel, collection, headers, parent = None,  *args):
        QtCore.QAbstractTableModel.__init__(self)
        self.arraydata = self.getMetadata(collection)
        self.headers = headers
        self.layoutChanged.emit()
        self.group =collection
        self.listModel = listModel


    @db_session
    def getMetadata(self,group):
        return [[a.id,a.name,a.comment] for a in group]


    def setHorizontalHeaderLabels(self,headers):

        if len(headers) < self.columnCount():
            raise ImportWarning
        else:
            self.headers = headers
            self.layoutChanged.emit()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.arraydata)

    def columnCount(self,parent=None, *args, **kwargs):
        return len(self.arraydata[0])

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole:

            return self.arraydata[index.row()][index.column()]


        if role == QtCore.Qt.EditRole:

                return self.arraydata[index.row()][index.column()]



    @db_session
    def setData(self, index, value, role=None):


        self.layoutAboutToBeChanged.emit()

        cell = get(g for g in Collection if g == self.group[index.row()])
        if index.column()==2:
            cell = get(g for g in Collection if g == self.group[index.row()])
            cell.comment = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==1:
            cell = get(g for g in Collection if g == self.group[index.row()])
            cell.name = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()



        self.layoutChanged.emit()



    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return "  "
        return
    def flags(self, index):
        if index.column() in [1,2]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable



class ProjectModel(ProjectGroupModel):

    def __init__(self, listModel, group, headers, parent = None,  *args):
        ProjectGroupModel.__init__(self, listModel, group, headers, parent = None)

    @db_session
    def getMetadata(self,group):
        return [[a.id,a.name,a.comment,a.real] for a in group]

    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        cell = get(p for p in Project if p == self.group[index.row()])
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==1:
            cell.name = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==3:
            cell.real = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        self.layoutChanged.emit()

    def flags(self, index):
        if index.column() in [1,2,3]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class CardModel(ProjectGroupModel):
    def __init__(self, listModel, group, headers, parent = None,  *args):
        ProjectGroupModel.__init__(self, listModel, group, headers, parent = None)

    @db_session
    def getMetadata(self,group):

        return [[a.id,a.name,a.comment,
                 get(c for c in Cards if c == a).disk.name,
                 get(c for c in Cards if c == a).disk.online,
                 a.jri, str(a.ingestDate),str(a.tournageDate),a.owner,
                 a.cameraModel,a.copied] for a in group]



    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        cell = get(c for c in Cards if c == self.group[index.row()])

        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==1:
            cell.name = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==5:
            cell.jri = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()

        if index.column()==10:
            cell.owner = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()

        if index.column()==11:
            cell.cameraModel = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()

    def flags(self, index):
        if index.column() in [1, 2, 5]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class ClipModel(ProjectGroupModel):
    def __init__(self, listModel, group, headers, parent = None,  *args):
        ProjectGroupModel.__init__(self, listModel, group, headers, parent = None)

    @db_session
    def getMetadata(self,group):
        return [[a.id,a.name,a.comment,a.tag,a.pays,a.ville,a.hasProxy, a.proxyPath,
                 a.videoSize,a.videoFps,a.durationSec, a.durationFrm, a.timeCode, a.videoCodec
                 ] for a in group]

    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()

        cell = get(a for a in Assets if a == self.group[index.row()])
        if index.column()==2:
            cell.comment = value
            self.arraydata[index.row()][index.column()] = value
            print(self.arraydata)
            commit()
            self.listModel.refresh()
        if index.column()==3:
            cell.tag = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==4:
            cell.pays = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        if index.column()==5:
            cell.ville = value
            self.arraydata[index.row()][index.column()] = value
            commit()
            self.listModel.refresh()
        self.layoutChanged.emit()


    def flags(self, index):
        if index.column() in [2,3,4,5]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class IngestClipModel(QtCore.QAbstractTableModel):
    def __init__(self, arrayData, headers, parent = None,  *args):
        QtCore.QAbstractTableModel.__init__(self)
        self.arraydata = arrayData
        self.headers = headers
        self.layoutChanged.emit()




    def setHorizontalHeaderLabels(self,headers):

        if len(headers) < self.columnCount():
            raise ImportWarning
        else:
            self.headers = headers
            self.layoutChanged.emit()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.arraydata)

    def columnCount(self,parent=None, *args, **kwargs):
        return len(self.arraydata[0])

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None


        if role == QtCore.Qt.DisplayRole:

            return self.arraydata[index.row()][index.column()]


        if role == QtCore.Qt.EditRole:
                return self.arraydata[index.row()][index.column()]



    @db_session
    def setData(self, index, value, role=None):
        self.layoutAboutToBeChanged.emit()
        self.arraydata[index.row()][index.column()] = value
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return "  "
        return
    def flags(self, index):
        if index.column() in [2,3,4,5]:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


'''
QHeaderView{
	font: 11pt "Helvetica";
}
QHeaderView::section{
border:1px solid rgb(199, 199, 199);
background-color: rgb(220, 236, 253);
}
'''
