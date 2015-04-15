# -*- coding: utf-8 -*-
__author__ = 'user1'
import logging
import os
import psutil
from .dataBase import *
import collections
import uuid
from PyQt5 import QtCore, QtGui, QtWidgets
logging.basicConfig( format='%(asctime)s %(message)s', level=logging.DEBUG)

class DiskPool(object):
    def __init__(self,mainwin,warn=False):
        """
        Cette classe permet de chercher tous les disuqes dans la bas de données ils seront online si ils sont toruvés
        sur le système.
        Elle permet de définir le disque par défaut il sera online si il est trouvé sur le système et si son disque de
        savegarde est lui aussi online
        """
        self.warn = warn
        self.MainWindow = mainwin
        with db_session:
            self.raid = Raid[0]
            self.sav_disks = select(d for d in Disk)
            self.proxy_disks = select(d for d in ProxyDrive)
            if not self.is_raid_online():
                raise NoRaidOnlineError

            self.refresh_partitions(warn=self.warn)

    def refresh_partitions(self,warn=False):
            self.mam_partitions,self.error = self.get_mam_partitions()
            self.current_index = None
            self.can_add_card = True
            self.online_sav_disks = self.get_online_sav_disks()
            self.online_proxy_disk = self.get_online_proxy_disk()

            self.current_disk = None
            self.current_proxy_disk = None
            self.define_current_disk()
            if not self.online_sav_disks:
                if warn:
                    self.error_message("Error","Aucun disque de sauvegarde n'est en ligne.",
                                       "Vous ne pourrez pas ajouter de cartes avant d'avoir corriger le problème")
                self.can_add_card = False
            logging.debug(self.online_proxy_disk)
            if not self.online_proxy_disk:
                if warn:
                    self.error_message("Error","Aucun disque de proxy n'est en ligne.",
                                       "Vous ne pourrez pas ajouter de cartes avant d'avoir corriger le problème")
                self.can_add_card = False

            if not self.current_disk:
                if warn:
                    self.error_message("Error","Il n'y a aucun disque de sauvegarde par défaut.",
                                       "Vous ne pourrez pas ajouter de cartes avant d'avoir corriger le problème")
                self.can_add_card = False

            if self.error:
                raise IdentificationNotReadable


    def is_disk_online(self,disk):
        with db_session:
            self.refresh_partitions()
            print(self.online_sav_disks)
            return disk in  self.online_sav_disks


    def error_message(self,title,error,informative):
        ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,str(title),
                                          str(error),
                                          QtWidgets.QMessageBox.Ok,
                                          self.MainWindow)
        ok.setInformativeText(str(informative))
        ok.exec_()

    def is_raid_online(self):
       chpath = "%s/.raid"%Raid[0].mountPoint
       print(chpath)
       return os.path.isfile(chpath)

    def set_default(self,adisk):
        with db_session:
            disk = get(d for d in Disk if d == adisk)
            print(disk)
            current_disk_force = get(c for c in Disk if c.current)
            if current_disk_force:
                current_disk_force.current=False
            disk.current = True
            disk.free = str(0)
            self.current_disk = disk

            print("hello")
            commit()
            self.define_current_disk()


    def add_disk(self, main):
        main_key = str(uuid.uuid4())

        try:
            with db_session:
                    disk = Disk(name=os.path.basename(main),mountPoint = main, online = True, current = False,
                                verificationKey = main_key,
                                free = str(0))
        except:
            raise CantAddDiskError
        else:
            try:
                with open("%s/.__identification_key"%main,"w") as f:
                    f.write(main_key)

            except:
                rollback()
                raise CantAddDiskError

            finally:
                self.refresh_partitions()

    def get_addable_disks(self):
        """
        this function return a list of drive that can be added to the system
        :return: list of path
        """
        disks_of_system = []
        for disk in psutil.disk_partitions():
            try:
                file = [a for a in os.listdir(disk.mountpoint) if not "lost+found" in a]
                files = [a for a in file if not a.startswith(".")] #if the disk is empty
          
                #If the disk is  already used
                disks_of_system.append({'path':disk.mountpoint,"data":disk,
                                    "used":True if disk.mountpoint in list(self.mam_partitions.values()) else False,
                                    "empty": False if files else True})
            except OSError:
                pass
        return disks_of_system





    def get_online_sav_disks(self):
        online_sav_disks = []

        # pour chaque disque main dans la base de donnée
        for adisk in self.sav_disks:
            disk = get(d for d in Disk if d == adisk)
            # pour chaque disque si le disque est dans la liste des clés en ligne
            if disk.verificationKey in list(self.mam_partitions.keys()):
                # On change le point de montage

                disk.mountPoint = self.mam_partitions[disk.verificationKey]
                # ON l'enregistre comme en ligne dans la base de donnée
                disk.online = True
                
                # On l'ajoute à la liste des disque en ligne
                online_sav_disks.append(disk)
                logging.debug("Main disk %s found !"%disk.name)
            else:
                #sinon on le l'indique comme étant hors_ligne dans la db
                disk.online=False
                # pour chaque disque de proxy dans la base de donnée
        return online_sav_disks

    def get_online_proxy_disk(self):
        online_proxy_disk = []

        for adisk in self.proxy_disks:
            disk = get(d for d in ProxyDrive if d == adisk)
            if disk.verificationKey in list(self.mam_partitions.keys()):
                # On change le point de montage
                disk.path = self.mam_partitions[disk.verificationKey]
                # ON l'enregistre comme en ligne dans la base de donnée
                disk.online = True
                # On l'ajoute à la liste des disque en ligne
                online_proxy_disk.append(disk)
                logging.debug("Proxy disque %s found !"%disk.name)
            else:
                #sinon on le l'indique comme étant hors_ligne
                disk.online=False
                # pour chaque disque de proxy dans la base de donnée

        return online_proxy_disk


    def define_current_disk(self):
        with db_session:
            i = -1
            for disk in self.online_sav_disks:
                i += 1
                if disk.current:
                    self.current_disk = disk
                    self.current_index = i
                    logging.debug("Current disk : %s."%disk.name)

            for disk in self.online_proxy_disk:
                if disk.default:
                    self.current_proxy_disk = disk
    def get_current_info(self):
        with db_session:
            return [self.current_disk.name, self.current_disk.mountPoint]

    def get_online_disks_path(self):
        with db_session:
            return [d.mountPoint for d in self.online_sav_disks]


    def get_current_proxy_info(self):
        with db_session:
            return [self.current_proxy_disk.name, self.current_proxy_disk.path]

    def get_current_proxy_space(self):
        with db_session:
            return psutil.disk_usage(self.current_proxy_disk.path)

    def get_default_disk_free(self):
        with db_session:
            disk = get(d for d in Disk if d == self.current_disk)
            used = disk.free
            total = psutil.disk_usage(disk.mountPoint).total
            return total-int(used),total, int(disk.free)

    def get_mam_partitions(self):
        #d'abord on liste toutes les paritions montées
        logging.debug("Get all partition of system")
        all_partitions = psutil.disk_partitions()
        mam_part = {}
        error = []
        for partition in all_partitions:
            mt_pt = partition.mountpoint
            # si la partition contient la clé
            if os.path.isfile("%s/.__identification_key"%mt_pt):
                try:
                    with open('%s/.__identification_key'%mt_pt, 'r') as f:
                        mam_part[f.read().split("\n")[0]] = mt_pt
                except IOError:
                    error.append(partition.mountPoint)
        logging.debug("got %s partitions"%(mam_part.__len__()))
        return mam_part,error




class NoRaidOnlineError(Exception):
    pass
class CantAddDiskError(Exception):
    pass
    pass
class IdentificationNotReadable(Exception):
    pass
class NoOnlineDiskError(Exception):
    pass
class BackupCurrentOfflineError(Exception):
    pass
class NoCurrentError(Exception):
    pass
class NoCurrentProxyError(Exception):
    pass
class NoProxyError(Exception):
    pass
