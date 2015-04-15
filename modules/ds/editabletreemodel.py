#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

from PyQt5.QtCore import (QAbstractItemModel, QModelIndex, Qt)
from PyQt5.QtGui import QIcon
from .dataBase import *


class TreeItem(object):
    def __init__(self, data, parent=None, icon = None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.loadedChild = False
        self.icon = icon


    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        if self.parentItem:
            if column == 1:
                return ""
            else:
                return self.itemData[0].name
        else:
            return self.itemData[column]


    def insertChildrenWithList(self, position, count, columns, values, icon = None):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self,icon)

            item.setData(0,values[row])
            self.childItems.insert(position, item)



    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self)
            self.childItems.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.insert(position, None)

        for child in self.childItems:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True
    def hasChildern(self):
        if self.parentItem:
            if not isinstance(self.itemData[0], Assets):
                return True if len(self.itemData[0].child)>0 else False
            else:
                return False
        else:
            return True


    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False

        self.itemData[column] = value

        return True


class TreeModel(QAbstractItemModel):
    def __init__(self, headers, parent=None):
        super(TreeModel, self).__init__(parent)

        rootData = [header for header in headers]
        self.rootItem = TreeItem(rootData)
        self.setupModelData(self.rootItem)

    def columnCount(self, parent=QModelIndex()):
        return self.rootItem.columnCount()

    def fetchMore(self, index):

        item = self.getItem(index)
        if item.loadedChild:
            return
        else:
            if isinstance(item.itemData[0], Collection):
                with db_session:
                    groups = select(p for p in ProjectGroup if p.collection == item.itemData[0]).prefetch(ProjectGroup.child)[:]
                    item.insertChildrenWithList(0,len(groups),1,groups,QIcon("./group.ico"))
                    item.loadedChild = True
            if isinstance(item.itemData[0], ProjectGroup):
                with db_session:
                    projects = select(p for p in Project if p.group == item.itemData[0]).prefetch(Project.child)[:]
                    item.insertChildrenWithList(0,len(projects),1,projects,QIcon("./project.ico"))
                    item.loadedChild = True

            if isinstance(item.itemData[0], Project):
                with db_session:
                    cards = select(p for p in Cards if p.project == item.itemData[0]).prefetch(Cards.child)[:]
                    item.insertChildrenWithList(0,len(cards),1,cards,QIcon("./card.ico"))
                    item.loadedChild = True
            if isinstance(item.itemData[0], Cards):
                with db_session:
                    cards = select(p for p in Assets if p.card == item.itemData[0])[:]
                    item.insertChildrenWithList(0,len(cards),1,cards,QIcon("./media.ico"))
                    item.loadedChild = True


    def hasChildren(self, index):
        return self.getItem(index).hasChildern()

    def canFetchMore(self, index):
        item = self.getItem(index)
        return item.hasChildern()


    def data(self, index, role):
        if not index.isValid():
            return None
        item = self.getItem(index)
        if role == Qt.DisplayRole or role == Qt.EditRole:

            return item.data(index.column())
        elif role == Qt.DecorationRole:
            if item.icon:
                return item.icon
        else:
            return

    def flags(self, index):
        if not index.isValid():
            return 0

        item = index.internalPointer()
        if isinstance(item.itemData[0], Assets):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):

        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows,
                self.rootItem.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeColumns(self, position, columns, parent=QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        item = self.getItem(index)
        result = False
        if not isinstance(item.itemData[0],Assets):
            with db_session:
                a = select(c for c in type(item.itemData[0]) if c == item.itemData[0]).prefetch(type(item.itemData[0]).child)[:]
                a[0].name = value
                commit()
                item.itemData[0] = a[0]
                result = True


        if result:
            self.dataChanged.emit(index, index)

        return result

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        result = self.rootItem.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def setupModelData(self,parent):
        parents= []
        with db_session:
            collections = select(c for c in Collection).prefetch(Collection.child)[:]
            self.rootItem.insertChildrenWithList(0,len(collections),1,sorted(collections),QIcon("./collection.ico"))




