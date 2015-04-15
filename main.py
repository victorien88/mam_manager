# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets,  QtGui, QtCore
from PyQt5.uic import loadUi
from ui import rc
import unicodedata
import logging
from modules.mdata_model import NCollectionModel, NProjectGroupModel, NProjectModel,NCardsModel, NClipsModel
import psutil
import shutil
from modules.dataBase import *
from modules.modalDialogs import ModalDialog, IngestWizard
from modules.models import ListModel, GenericListModel, ProjectGroupModel, CollectionModel , ProjectModel, CardModel, ClipModel, GroupModel, Clientmodel, Usermodel
from modules.rsync import CopyFunction
from modules.proxyMaker import EncodeFunction
from modules.Analyzer import AnalyseFunction
from modules.backuper import BackupThread
from modules.DiskManager import DiskPool, IdentificationNotReadable,NoOnlineDiskError,BackupCurrentOfflineError,NoCurrentError,NoCurrentProxyError, NoProxyError
from modules.mailer import Mailer
import os
from modules.models import GenericListModel
from modules.editabletreemodel import TreeModel as RushModel
from rushWidget import RushWidget


# create logger
logging.basicConfig( format='%(asctime)s %(message)s', level=logging.DEBUG)

class Updater:
    def __init__(self):
        pass




def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nkfd_form if not unicodedata.combining(c)])



def get_size(start_path):
        total_size = 0
        seen = {}
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                except OSError:
                    continue

                try:
                    seen[stat.st_ino]
                except KeyError:
                    seen[stat.st_ino] = True
                else:
                    continue

                total_size += stat.st_size

        return total_size

@db_session
def remove_db_items():
    msg = QtWidgets.QMessageBox(MainWindow)
    msg.setText("Supprimer ?")
    msg.setIcon(QtWidgets.QMessageBox.Question)
    indexes = MainWindow.rush_browser.selectionModel().selection().indexes()
    items = [i.internalPointer() for i in indexes]
    db_items = [i.itemData[0] for i in items]
    names = [i.name for i in db_items]
    if isinstance(db_items[0], Collection):
        chose = "la / les collection(s)"
    elif isinstance(db_items[0], ProjectGroup):
        chose = "le / les groupe(s)"
    elif isinstance(db_items[0], Project):
        chose = "le / les projet(s)"
    elif isinstance(db_items[0], Cards):
        chose = "la / les carte(s)"
    else:
        return

    msg.setInformativeText("êtes-vous sur de vouloir supprimer %s : %s"%(chose,", ".join(names)))
    msg.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
    ret = msg.exec_()
    if ret == QtWidgets.QMessageBox.Yes:
        i = -1
        for index in indexes:
            i += 1
            item = index.internalPointer().itemData[0]
            if not len(index.internalPointer().itemData[0].child):
                 MainWindow.rush_model.removeRows(indexes[i].row(),indexes[i].row()+1,indexes[i].parent())
                 with db_session:
                     refreshed_item = get(i for i in type(item) if i == item)
                     refreshed_item.delete()

            else:
                ok = QtWidgets.QErrorMessage(MainWindow)
                ok.showMessage( "'%s' n'est pas vide. Impossible de supprimer."%names[i])
    return

def add_collection():
    name, desc, ok = dialog.showAddCollDialog("Ajouter une collection", "Ajouter une collection","Vous devez obligatoirement ajouter un nom. <br> La description bien qu'optionnelle est fortement recommandée")
    if ok:
        with db_session:
            #try:

                newgroup = Collection(name=name , comment=desc)
                index = MainWindow.rush_browser.selectionModel().currentIndex()
                model = MainWindow.rush_model

                if not model.insertRow(index.row()+1, index.parent()):
                    return



                for column in range(model.columnCount(index.parent())):
                    child = model.index(index.row()+1, column, index.parent())
                    print(child)
                    model.insertItem(child, newgroup)
            #except:
            #    db_error(sys.exc_info())
            #    rollback()
            #commit()


#@db_session
def add_group():
    name, desc, usermodel, clientmodel, ok = dialog.showAddGroupDialog("Ajouter un groupe", "Ajouter un groupe","Vous devez obligatoirement ajouter un nom. <br> La description bien qu'optionnelle est fortement recommandée")
    if ok:
        with db_session:
            #try:
            collection_parent = MainWindow.rush_browser.selectionModel().currentIndex().internalPointer().itemData[0]

            newgroup = ProjectGroup(name=name , comment=desc, collection=get(
                c for c in Collection if c==collection_parent))

            #except:
            #    db_error(sys.exc_info())
            #rollback()
            commit()
    MainWindow.rush_browser.model().layoutAboutToBeChanged.emit()
    MainWindow.rush_browser.selectionModel().currentIndex().internalPointer().refresh()
    MainWindow.rush_browser.model().layoutChanged.emit()




@db_session
def add_project():
    name, desc, real, ok = dialog.showAddProjectDialog("Ajouter un projet", "Ajouter un projet","Vous devez obligatoirement ajouter un nom. <br> La description bien qu'optionnelle est fortement recommandée")
    if ok:
        try:
            new_project = Project(name=name , comment=desc, real= real, group=ProjectGroup[MainWindow.listView.model().getItem(MainWindow.listView.selectionModel().selectedIndexes()[0]).id])
            MainWindow.selection.reInitProjects()
        except:
            db_error(sys.exc_info())
            rollback()


def add_user_sheet():
    logging.debug("Adding user page")
    MainWindow.user_stack.setCurrentIndex(0)
    MainWindow.stackedWidget_2.setCurrentIndex(1)
    MainWindow.l_user_name.setText("")
    MainWindow.l_user_pass1.setText("")
    MainWindow.l_user_pass2.setText("")
    MainWindow.l_email.setText("")
    MainWindow.c_cansend.setChecked(False)
    MainWindow.c_admin.setCurrentIndex(0)
    model = GroupModel()
    MainWindow.l_validate.setModel(model)

def add_user():
    logging.debug("adding a new user into DB")
    if MainWindow.l_user_pass1.text() == MainWindow.l_user_pass2.text():
        if len(MainWindow.l_user_pass1.text())>5:
            with db_session:
                if not exists(u for u in Users if u.name == MainWindow.l_user_name.text()):
                    try:
                        os.mkdir("/home/shared/%s"%(MainWindow.l_user_name.text()))
                    except:
                        error_message("Impossible de créer le dossier de l'utilisateur courrant","Vérifiez les droits d'écriture dans le répertoire partagé")
                        logging.debug("adding a new user failed. Can't create personal folder")
                        return
                    new_user = Users(name=MainWindow.l_user_name.text(),
                                        passw=MainWindow.l_user_pass1.text(),
                                        system=False,
                                        admin= True if MainWindow.c_admin.currentIndex == 1 else False,
                                        mail = MainWindow.l_email.text(),
                                        canValidate = MainWindow.c_cansend.isChecked(),
                                        canSeeMasters = MainWindow.c_masters.isChecked())

                    for line in MainWindow.l_validate.model().get_dict():
                        if line['state'] == 2:

                                group = get(g for g in ProjectGroup if g == line['object'])
                                new_user.defaulValidationGroup.add(group)
                        else:
                            pass
                    commit()
                    MainWindow.user_stack.setCurrentIndex(1)
                    MainWindow.stackedWidget_2.setCurrentIndex(0)
                    MainWindow.l_users.model().refresh()
                    logging.debug("User %s successfully added"%new_user.name)
                    MainWindow.user_stack.setCurrentIndex(1)
                    MainWindow.stackedWidget_2.setCurrentIndex(0)
                    MainWindow.l_users.model().refresh()
                    logging.debug("Sending mail to new user")
                    text = str(MainWindow.mailer.get_text_mail('hello')[1]).format(new_user.name,new_user.name,
                    new_user.passw,"administrateur, vous pourrez ajouter des rushes dans la base de données." if new_user.admin
                    else "utilisateur, vous pourrez consulter les rushes dans la base de données.", "Vous pourrez aussi envoyer des sujets en valdation." if new_user.canValidate else "")
                    MainWindow.mailer.sendmail(new_user.mail,text,MainWindow.mailer.get_text_mail('hello')[0])
                    logging.debug("Mail sucessfully sended")
                else :
                    error_message("Impossible d'ajouter l'utilisateur","Cet utilisateur existe déjà")
                    logging.debug("User already exits")
        else:
            error_message("Impossible d'ajouter l'utilisateur","Le mot de passe doit faire plus de 6 caractères")
            logging.debug("Error password too short")
    else:
        error_message("Impossible d'ajouter l'utilisateur","Les mots de passe ne sont pas concordants.")
        logging.debug("Error password does not match")

def change_user():
    if MainWindow.l_users.selectionModel().hasSelection():
        MainWindow.user_mapper.setCurrentIndex(MainWindow.l_users.selectionModel().selectedIndexes()[0].row())
        MainWindow.user_stack.setCurrentIndex(2)
        model = MainWindow.l_users.model().getSubModel(MainWindow.l_users.selectionModel().selectedIndexes()[0])
        MainWindow.ch_validate.setModel(model)
        MainWindow.b_remove_user.setEnabled(True)
    else:
        MainWindow.b_remove_user.setEnabled(False)





def show_user_page():
    MainWindow.stack.setCurrentIndex(1)
    umodel = Usermodel()
    MainWindow.l_users.setModel(umodel)
    sel = MainWindow.l_users.selectionModel()
    sel.selectionChanged.connect(change_user)
    MainWindow.user_mapper = QtWidgets.QDataWidgetMapper()
    MainWindow.user_mapper.setModel(umodel)
    MainWindow.user_mapper.addMapping(MainWindow.l_user_name_ch, 0)
    MainWindow.user_mapper.addMapping(MainWindow.l_user_pass_ch, 2)
    MainWindow.user_mapper.addMapping(MainWindow.chl_mail, 1)
    MainWindow.user_mapper.addMapping(MainWindow.ch_admin, 3)
    MainWindow.user_mapper.addMapping(MainWindow.ch_send, 4)
    MainWindow.user_mapper.addMapping(MainWindow.ch_master, 5)
    logging.debug('mapper done')
    MainWindow.user_mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.ManualSubmit)




def has_no_child(indexes, model):
    for item in indexes:
        if len(model.get_children(item.row())) >  0:
            return False
    return True

@db_session
def remove_group():
    msg = QtWidgets.QMessageBox(MainWindow)
    msg.setText("Supprimer ?")
    msg.setIcon(QtWidgets.QMessageBox.Question)
    msg.setInformativeText("êtes-vous sur de vouloir supprimer le groupe %s"%(MainWindow.listView.model().getItem(MainWindow.listView.selectionModel().selectedIndexes()[0]).name))
    msg.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)


    if has_no_child(MainWindow.listView.selectionModel().selectedIndexes(), MainWindow.listView.model()):
        ret = msg.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            for item in MainWindow.listView.selectionModel().selectedIndexes():
                with db_session:
                    try:
                        band = get(g for g in ProjectGroup if g ==MainWindow.listView.model().getItem(item.row()))
                        band.delete()
                        MainWindow.selection.reInitGroups()
                    except:
                        db_error(sys.exc_info())
                        rollback()

    else:
        ok = QtWidgets.QErrorMessage(MainWindow)
        ok.showMessage( "Le groupe n'est pas vide. Impossible de le supprimer  ")

@db_session
def remove_card():

    msg = QtWidgets.QMessageBox(MainWindow)
    msg.setText("Supprimer ?")
    msg.setIcon(QtWidgets.QMessageBox.Question)
    msg.setInformativeText("êtes-vous sur de vouloir supprimer %s carte(s) <br> Les cartes ainsi que leurs proxys seront DEFINITIVEMENT supprimées de la base de donnée ainsi que de la sauvegarde."%(len(MainWindow.listView_3.selectionModel().selectedIndexes())))
    msg.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)



    ret = msg.exec_()
    if ret == QtWidgets.QMessageBox.Yes:

        passWd, ok = QtWidgets.QInputDialog.getText(MainWindow.centralwidget,"mot de passe","Veuillez entrer la phrase magique pour supprimer les cartes :",QtGui.QLineEdit.Password)
        if passWd == "lessanglotslongs":
            todel=[]
            for itemModel in MainWindow.listView_3.selectionModel().selectedIndexes():
                item = get(c for c in Cards if c==MainWindow.listView_3.model().getItem(itemModel.row()))
                if item.stat < 2:
                    ok = QtWidgets.QErrorMessage(MainWindow)
                    ok.showMessage( "Vous devez attendre la fin de la copie pour supprimer cette carte : %s"%item.name)
                else:
                    allprox = True
                    for asset in item.child:
                        if not asset.hasProxy:
                            allprox = False
                    if not allprox:
                        ok = QtWidgets.QErrorMessage(MainWindow)
                        ok.showMessage( "Au moins un proxy est en création sur cette carte : %s<br> Vous devez attendre la fin de la génération avant de supprimer la carte."%item.name)
                    else:

                        todel.append(item)



            if not todel ==[]:
                for item in todel:

                            cardPath = "%s/%s/"%(item.disk.mountPoint,item.id)
                            raidCardPath = "%s/%s/"%(Raid[0].mountPoint,item.id)
                            fristclip = select(a for a in Assets if a.card == item)[:]
                            proxyPath = "%s/%s"%(fristclip[0].proxyDisk.path,item.id)
                            old_free = item.disk.free
                            item.disk.free = str(int(old_free) - int(item.poids))
                            # TO DO PURGE PROXY#
                            try:
                                logging.debug("deting disk Card Path")
                                shutil.rmtree(cardPath)

                            except OSError:
                                 logging.debug("deting disk Card PathFailed")
                            try:
                                logging.debug("deting  raid Path")
                                shutil.rmtree(raidCardPath)

                            except OSError:
                                    logging.debug("deting raid  PathFailed")
                            try:
                                logging.debug("deting proxy Card Path")
                                shutil.rmtree(proxyPath)
                            except OSError:
                                logging.debug("deting proxy card pathFailed")
                                logging.debug("deting proxy card pathFailed")
                            logging.debug("deting card form db")
                            item.delete()
                MainWindow.selection.reInitCards()




        else:
            ok = QtWidgets.QErrorMessage(MainWindow)
            ok.showMessage("Mauvaise phrase magique")




@db_session
def remove_project():
    msg = QtWidgets.QMessageBox(MainWindow)
    msg.setText("Supprimer ?")
    msg.setIcon(QtWidgets.QMessageBox.Question)
    msg.setInformativeText("êtes-vous sur de vouloir supprimer %s projet(s)"%(len(MainWindow.listView_2.selectionModel().selectedIndexes())))
    msg.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)


    if has_no_child(MainWindow.listView_2.selectionModel().selectedIndexes(), MainWindow.listView_2.model()):
        ret = msg.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            for item in MainWindow.listView_2.selectionModel().selectedIndexes():
                    try:
                        band = get(p for p in Project if p == MainWindow.listView_2.model().getItem(item.row()))
                        band.delete()
                        MainWindow.selection.reInitGroups()
                    except:
                        db_error(sys.exc_info())
                        rollback()
                        MainWindow.selection.reInitGroups()



    else:
        error_message("impossible de supprimer ce projet carte", "Le groupe n'est pas vide. Impossible de le supprimer  ")


def check_raid():
    with db_session:
        cards = select(c.poids for c in Cards if c.on_raid)[:]
        total = sum([int(a) for a in cards])
        if total > int(Raid[0].limit):
            print("I will purge")


@db_session
def ingest():
    if MainWindow.pool.can_add_card:
        print((MainWindow.pool.can_add_card))
        check_raid()
        if len(MainWindow.listView_2.selectedIndexes()) == 1:
            parent = MainWindow.listView_2.model().getItem(MainWindow.listView_2.selectedIndexes()[0])
            wiz = IngestWizard(MainWindow,parent)
            ret, cardPath, name, jri, create_proxy, descr, pays, ville, tourndate, cameramodel, owner, clips, avc, mode, \
            xpath, audio = wiz.setupUi()
            try:
                asset_disk = get(d for d in Disk if d == MainWindow.pool.current_disk)
                usage_asset_disk, total, used = MainWindow.pool.get_default_disk_free()
            except:
                db_error(sys.exc_info())
                rollback()
                MainWindow.selection.reInitProjects()
                return

            try:

                a = psutil.disk_usage(asset_disk.mountPoint)

            except:
                ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Erueur",
                                              "Impossible de localiser le disque de sauvegarde<br>",
                                              QtWidgets.QMessageBox.Yes,
                                                  MainWindow)
                ok.setInformativeText("%s"%(sys.exc_info()[0]))
                ok.exec_()
                MainWindow.selection.reInitProjects()
                change_disk()


            if ret:
                logging.debug("### GETTING CARD SIZE ###")

                card_size = get_size(cardPath)


                secured_usage_asset_disk = usage_asset_disk - (0.08*total)

                if card_size  < secured_usage_asset_disk:
                    logging.debug("### ADDING CARD TO DB ###")
                    new_card = Cards(comment = descr, name = remove_accents(str(name)), firsName=remove_accents(str(name)), project = get(p for p in Project if p == parent),
                                     disk = asset_disk,
                                     jri = jri, ingestDate = datetime.date.today(),
                                     tournageDate = datetime.date(day=int(tourndate.toString("dd")),
                                                                  month=int(tourndate.toString("MM")),
                                                                  year=int(tourndate.toString("yyyy"))),

                                     owner = owner, copied = False, cameraModel= cameramodel, originalPath = cardPath,
                                     locked = False, stat = 0, ingestedBy = MainWindow.currentUser.name,poids=str(card_size),
                                     audio=audio)
                    totus = float(Raid[0].used)
                    Raid[0].used = str(totus + float(card_size))
                    asset_disk.free = str(card_size +used)
                    try:
                        commit()
                    except CommitException:
                        logging.debug("Card already in DB")
                        error_message("Impossible d'importer cette carte", "Une carte avec le même nom existe déjà")
                    else:
                        logging.debug("### LAUNCHING ANALYZE ###")
                        print(mode)
                        print(xpath)
                        MainWindow.analyser.addClips(new_card,clips,ville, pays,MainWindow.pool.get_current_proxy_info()[1],mode, xpath, audio)
                        MainWindow.selection.reInitCards()


                else:
                    ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Erueur",
                                              "Pas Assez de place sur le disque dur de sauvegarde<br>Changez le disque par défaut avant d'ajouter une carte.",
                                              QtWidgets.QMessageBox.Yes,
                                                  MainWindow)

                    ok.exec_()
    else:
            error_message("Il y a un problème au niveau des disques","Impossible d'ajouter une carte. Vous devez "
                                                                      "corriger le problème")


def getSelection(view):
    items = [view.model().getItem(d) for d in view.selectedIndexes()]
    return items


def change_project_group():
    print('im here"')
    collection_model = MainWindow.collection_list.model()
    group_model = MainWindow.listView.model()
    project_model = MainWindow.listView_2.model()
    items = getSelection(MainWindow.listView_2)
    print(items)
    ret, group = dialog.showChGroup(collection_model,items)
    if ret:
        for item in items:
            project_model.chGroup(item,group)

    MainWindow.selection.reInitGroups()

def change_group_collec():
    coll_model = MainWindow.collection_list.model()
    items = getSelection(MainWindow.listView)
    group_model = MainWindow.listView.model()
    ret, index = dialog.showChColl(coll_model,items)
    if ret:
        for item in items:
            group_model.chColl(item,coll_model.getItem(index))

        MainWindow.selection.reInitGroups()

def change_card_project():
    coll_model = MainWindow.collection_list.model()
    group_model = MainWindow.listView.model()
    proj_model = MainWindow.listView_2.model()
    items = getSelection(MainWindow.listView_3)
    ret, project = dialog.showChProj(coll_model,group_model,items)
    if ret:
        for item in items:
            group_model.chProj(item,project)
        MainWindow.selection.reInitProjects()

def purge_20_percent():
    pass

@db_session
def get_disk_usage():

        if MainWindow.pool.can_add_card:

            proxy_usage = MainWindow.pool.get_current_proxy_space()
            free,total, old = MainWindow.pool.get_default_disk_free()
            reserved = 0.08*total

            used = total - (reserved + free)

            per_used = (used/total) *100
            per_free = (free/total)*100
            per_reserved = (reserved/total)*100

            main_chart_base = """
        <div class="templatemo-chart-box col-lg-3 col-md-3 col-sm-4 col-xs-12">
        <canvas id="e-chart"></canvas></div>

            <script src="js/jquery.min.js"></script>

            <script src="js/Chart.min.js"></script>

            <script type="text/javascript">
              // Line chart
              var randomScalingFactor = function(){ return Math.round(Math.random()*100)};


              var pieChartData = [
              {
                value: %s,
                color:"#F7464A",
                highlight: "#FF5A5E",
                label: "Utilisé"
              },

              {
                value: %s,
                color: "#228B22",
                highlight: "#008000",
                label: "Réservé"
              },
                {
                value: %s,
                color: "#FDB45C",
                highlight: "#FFC870",
                label: "Libre"
              }
              ]; // pie chart data



              window.onload = function(){
                var ctx_pie = document.getElementById("e-chart").getContext("2d");

                window.myPieChart = new Chart(ctx_pie).Pie(pieChartData,{
                  responsive: true
                });

              }
            </script>
         """



            chart_base = """
        <div class="templatemo-chart-box col-lg-3 col-md-3 col-sm-4 col-xs-12">
        <canvas id="e-chart"></canvas></div>

            <script src="js/jquery.min.js"></script>

            <script src="js/Chart.min.js"></script>

            <script type="text/javascript">
              // Line chart
              var randomScalingFactor = function(){ return Math.round(Math.random()*100)};


              var pieChartData = [
              {
                value: %s,
                color:"#F7464A",
                highlight: "#FF5A5E",
                label: "Utilisé"
              },

              {
                value: %s,
                color: "#FDB45C",
                highlight: "#FFC870",
                label: "Libre"
              }
              ]; // pie chart data



              window.onload = function(){
                var ctx_pie = document.getElementById("e-chart").getContext("2d");

                window.myPieChart = new Chart(ctx_pie).Pie(pieChartData,{
                  responsive: true
                });

              }
            </script>
         """
            asset_chart = main_chart_base %(per_used + 8 , per_reserved, per_free )
            proxy_chart = chart_base %(proxy_usage.percent,  100-proxy_usage.percent)
            MainWindow.stack.setCurrentIndex(2)
            MainWindow.webView_2.setHtml(proxy_chart,QtCore.QUrl("file://%s/"%(programFilePath)))
            MainWindow.webView.setHtml(asset_chart,QtCore.QUrl("file://%s/"%(programFilePath)))
            MainWindow.asset_disk_name_label.setText(MainWindow.pool.get_current_info()[0])
            MainWindow.proxy_disk_name_label.setText(MainWindow.pool.get_current_proxy_info()[1])
            MainWindow.asset_disk_online_label.setText("<i> Autres disques online"+ " :" + ", ".join(
                [d for d in MainWindow.pool.get_online_disks_path() if not d == MainWindow.pool.get_current_info()[1]])+"</i>")
            MainWindow.proxy_disk_free_label.setText("%s To disponibles"%(round(proxy_usage.free/1000000000000,2)))
            MainWindow.asset_disk_free_label.setText("%s To disponibles"%(round(free/1000000000000,2)))
            #", ".join(pool.get_online_disks_path())
        else:
            if not MainWindow.pool.get_current_info:
                error_message("Impossible de localiser le disque de proxy. L'application va s'arrêter.","Remontez le disque avant de relancer l'application.")
                app.quit()
                return
            else:
                change_disk(force=True)
            MainWindow.user_stack.setCurrentIndex(2)

def updateRemoveUserButton():
    if len(MainWindow.l_users.selectedIndexes())>0:
        MainWindow.b_remove_user.setEnabled(True)
    else:
        MainWindow.b_remove_user.setEnabled(False)

def delete_user():
    ret = QtWidgets.QMessageBox.question(MainWindow,"Effacer un utilisateur","Êtes-vous sur de vouloir effacer un utilisateur ?",QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
    if ret == QtWidgets.QMessageBox.Yes:
        with db_session:
            logging.debug("Deleting user %s"%MainWindow.l_users.model().getItemFromIndex(MainWindow.l_users.selectedIndexes()[0].row()))
            user_to_delete = get(u for u in Users if u== MainWindow.l_users.model().getItemFromIndex(MainWindow.l_users.selectedIndexes()[0].row()))


            try:
                shutil.rmtree("/home/shared/%s"%user_to_delete.name)
            except :
                pass

            user_to_delete.delete()
            MainWindow.l_users.model().refresh()
            MainWindow.l_users.selectionModel().clearSelection()
            MainWindow.user_stack.setCurrentIndex(1)

def delete_client():
    ret = QtWidgets.QMessageBox.question(MainWindow,"Effacer un client","Êtes-vous sur de vouloir effacer un client ?",QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
    if ret == QtWidgets.QMessageBox.Yes:
        with db_session:
            logging.debug("Deleting client %s"%MainWindow.l_client.model().getItemFromIndex(MainWindow.l_client.selectedIndexes()[0].row()))
            user_to_delete = get(c for c in Client if c== MainWindow.l_client.model().getItemFromIndex(MainWindow.l_client.selectedIndexes()[0].row()))


            user_to_delete.delete()
            MainWindow.l_client.model().refresh()
            MainWindow.l_client.selectionModel().clearSelection()
            MainWindow.user_stack_2.setCurrentIndex(1)


@db_session
def updateUserData():
    MainWindow.user_mapper.submit()
    MainWindow.ch_validate.model().instertInDb()
    MainWindow.user_stack.setCurrentIndex(1)



def check_login(username,passw):
    try:
        if get(u for u in Users if u.name == username).passw == passw:
            logging.debug("Password for user %s ok"%username)
            return True
        else:
            logging.debug("Password for user %s bad"%username)
            return False
    except:
        return False



@db_session
def set_rights():
    if not MainWindow.currentUser.admin:
        MainWindow.b_users.setEnabled(False)
        MainWindow.b_drives.setEnabled(False)
    else:
        MainWindow.b_users.setEnabled(True)
        MainWindow.b_drives.setEnabled(True)

        purgeError()
        MainWindow.proxyMaker.fixProxies()
        #TO DO FIX FIX PROXY



@db_session
def connect():
    users = select(u for u in Users if not u.system)[:]
    ch_user = MainWindow.l_user.text()
    ch_pass = MainWindow.l_pass.text()

    MainWindow.l_users.setModel(GenericListModel(sorted(users)))
    b = MainWindow.l_users.selectionModel()
    MainWindow.l_users.selectionModel().selectionChanged.connect(updateRemoveUserButton)
    b = MainWindow.l_users.selectionModel()
    if check_login(ch_user,ch_pass):
            MainWindow.stackedWidget.setCurrentIndex(1)
            MainWindow.deconnect.setVisible(True)
            MainWindow.currentUser = get(u for u in Users if u.name == ch_user)
            logging.debug("Current user connected : %s"%ch_user)
            get_disk_usage()
            MainWindow.stack.setCurrentIndex(0)
            set_rights()

    else:

            a =QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Invalid password", "Nom d'utilisateur ou mot de passe invalide",QtWidgets.QMessageBox.Ok,MainWindow)
            a.exec_()



@db_session
def change_disk(force=False):
    if not force:
        ok = dialog.showAddAssetDisk(MainWindow.pool)
        MainWindow.pool = DiskPool(MainWindow)
        get_disk_usage()
    else:
        ok = dialog.showAddAssetDisk(MainWindow.pool)
        MainWindow.pool = DiskPool(MainWindow)
        if not MainWindow.pool.can_add_card:
            error_message("Aucun disque n'est disponible pour l'ajout des cartes","Pour des raisons de sécurité l'application va s'arrêter")
            app.quit()

def send_mail_clients():
    ok,object,mail = dialog.show_send_mail("Envoyer un mail à tous les clients","<b>Envoyer un mail à tous les clients</b>")
    if ok:
        with db_session:
            clients = select(c for c in Client)[:]
            mails = [c.mail for c in clients]
            logging.debug("sending mail to %s" %mails)
        progress = QtWidgets.QProgressDialog("Envoi du mail...", "Anuler", 0, len(mails), MainWindow)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        logging.debug("sending %s mails"%len(mails))
        for i in range(len(mails)):
            progress.setValue(i)

            logging.debug("sending mail %s: %s"%(i,mails[i]))
            if progress.wasCanceled():
                break
            MainWindow.mailer.sendmail(mails[i],mail.encode('utf-8','ignore'),object.encode('utf-8','ignore'))
            #print "mail to %s : sub %s text: %s"%(mails[i],mail.encode('utf-8','ignore'),object.encode('utf-8','ignore'))
        progress.setValue(len(mails))

def send_mail_users():
    ok,object,mail = dialog.show_send_mail("Envoyer un mail à tous les utilisateurs","<b>Envoyer un mail à tous les utilisateurs</b>")
    if ok:
        with db_session:
            mails = select(u.mail for u in Users if u.mail)[:]

        progress = QtWidgets.QProgressDialog("Envoi du mail...", "Anuler", 0, len(mails), MainWindow)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        for i in range(len(mails)):
            progress.setValue(i)

            if progress.wasCanceled():
                break
            logging.debug("Sending mail to %s"%mails[i])
            MainWindow.mailer.sendmail(mails[i],mail.encode('utf-8','ignore'),object.encode('utf-8','ignore'))

        progress.setValue(len(mails))

def send_mail_devel():
    ok,object,mail = dialog.show_send_mail("Envoyer un mail au développeur","<b>Envoyer un mail au développeur</b>")
    if ok:
        MainWindow.mailer.sendmail("victorien.tronche@gmail.com",mail.encode('utf-8','ignore'),object.encode('utf-8','ignore'))

def canok():
    if MainWindow.chl_mail.text() :
        MainWindow.buttonBox_2.button(QtWidgets.QDialogButtonBox).setEnabled(True)
    else:
        MainWindow.buttonBox_2.button(QtWidgets.QDialogButtonBox).setEnabled(False)
    if MainWindow.l_user_name.text() and MainWindow.l_user_pass1.text() and MainWindow.l_user_pass2.text() and MainWindow.l_email.text():
        MainWindow.buttonBox.button(QtWidgets.QDialogButtonBox).setEnabled(True)
    else:
        MainWindow.buttonBox.button(QtWidgets.QDialogButtonBox).setEnabled(False)
    if   MainWindow.l_client_name.text() and MainWindow.l_client_fullName.text() and MainWindow.l_client__pass1.text() and MainWindow.l_client_pass2.text() and MainWindow.l_client_company.text() and MainWindow.l_client_mail.text():
        MainWindow.buttonBox_3.button(QtWidgets.QDialogButtonBox).setEnabled(True)
    else:
        MainWindow.buttonBox_3.button(QtWidgets.QDialogButtonBox).setEnabled(False)

def user_rejected():
    MainWindow.user_stack.setCurrentIndex(1)
    MainWindow.l_user_name.setText('')
    MainWindow.l_user_pass1.setText('')
    MainWindow.l_user_pass2.setText('')
    MainWindow.c_admin.setCurrentIndex(0)
    MainWindow.stackedWidget_2.setCurrentIndex(0)
    MainWindow.l_users.selectionModel().clearSelection()


def is_first_start():
    with db_session:
        a = select(u for u in Users)[:]
        if len(a) == 0:
            return True
        else:
            return False

def stackChanged(number):

    pass


def decon():
    MainWindow.l_user.setText('')
    MainWindow.l_pass.setText('')
    MainWindow.stackedWidget.setCurrentIndex(0)
    MainWindow.deconnect.setVisible(False)


@db_session(retry=3)
def proxy_change():
    ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Erueur",
                                      "Vous allez changer le disque de proxy. Merci de ne pas déconnecter l'ancien disque sinon vous proxys seront offilne",
                                      QtWidgets.QMessageBox.Ok,
                                      MainWindow)
    ok.exec_()
    disk = QtWidgets.QFileDialog.getExistingDirectory(MainWindow,"Choisir le nouveau disque")
    if disk:
        b = select(d for d in ProxyDrive if d.default == True)[:]
        for c in b:
            c.default = False
        a = ProxyDrive(path=disk, default=True)


def db_error(error):
    ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,"Erreur",
                                      "Une erreur de base de donnée est apparue.<br>",
                                      QtWidgets.QMessageBox.Ok,
                                      MainWindow)
    ok.setInformativeText("%s : %s, at : %s"%(error))
    ok.exec_()

def error_message(error,informative):
    ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,"Erreur",
                                      str(error),
                                      QtWidgets.QMessageBox.Ok,
                                      MainWindow)
    ok.setInformativeText(str(informative))
    ok.exec_()

def reinit_proxys():
    with db_session:
        a = select(a for a in Assets)[:]
        for b in a:
            b.hasProxy = False
            b.progression = 0

def change_passwd_client():
    ret, value = dialog.show_ch_passwd()
    if ret:
        MainWindow.l_user_pass1_ch_2.setText(value)

def change_passwd_user():
    ret, value = dialog.show_ch_passwd()
    if ret:
        MainWindow.l_user_pass_ch.setText(value)

def select_model(indexes,parent_model):
    if isinstance(indexes[0].internalPointer().itemData[0], Collection):
        try:
            MainWindow.add_b.clicked.disconnect()
            MainWindow.remove_b.clicked.disconnect()
        except:
            pass
        MainWindow.add_b.clicked.connect(add_group)
        MainWindow.remove_b.clicked.connect(remove_db_items)
        MainWindow.move_b.clicked.connect(change_group_collec)
        return False,NCollectionModel(indexes,parent_model)
    elif isinstance(indexes[0].internalPointer().itemData[0], ProjectGroup):
        return False,NProjectGroupModel(indexes,parent_model)
    elif isinstance(indexes[0].internalPointer().itemData[0], Project):
        return False,NProjectModel(indexes,parent_model)
    elif isinstance(indexes[0].internalPointer().itemData[0], Cards):
        return True, NCardsModel(indexes,parent_model)
    elif isinstance(indexes[0].internalPointer().itemData[0], Assets):
        return False, NClipsModel(indexes,parent_model)
    else:
        raise TransactionError

def update_data(a,b):
    en_dis_side_buttons()
    if MainWindow.rush_browser.selectionModel().hasSelection():
        indexes = MainWindow.rush_browser.selectionModel().selection().indexes()
        delegate, model = select_model(indexes,MainWindow.rush_browser.model())


        MainWindow.mdata_view.setModel(model)
        if delegate:
            from modules.delegate import SpinBoxDelegate
            MainWindow.mdata_view.setItemDelegateForColumn(5,SpinBoxDelegate())

        MainWindow.rush_model.refresh.connect(model.refresh_data)
        MainWindow.mdata_view.resizeColumnsToContents()
    else:
        MainWindow.mdata_view.setModel(GenericListModel([]))
        MainWindow.add_b.clicked.disconnect()
        MainWindow.add_b.clicked.connect(add_collection)

def en_dis_side_buttons():
    if MainWindow.rush_browser.selectionModel().hasSelection():
        indexes = MainWindow.rush_browser.selectionModel().selection().indexes()
        if not isinstance(indexes[0].internalPointer().itemData[0], Assets):
            MainWindow.add_b.setEnabled(True)
            MainWindow.remove_b.setEnabled(True)
            MainWindow.move_b.setEnabled(True)
        else:
            MainWindow.add_b.setEnabled(False)
            MainWindow.remove_b.setEnabled(False)
            MainWindow.move_b.setEnabled(False)
    else:
        MainWindow.add_b.setEnabled(True)
        MainWindow.remove_b.setEnabled(False)
        MainWindow.move_b.setEnabled(False)

def show_client_page():
    MainWindow.stack.setCurrentIndex(4)
    MainWindow.user_stack.setCurrentIndex(1)
    MainWindow.user_stack_2.setCurrentIndex(1)

    model = Clientmodel()
    MainWindow.l_client.setModel(model)
    sel = MainWindow.l_client.selectionModel()
    sel.selectionChanged.connect(change_client)
    MainWindow.mapper = QtWidgets.QDataWidgetMapper()
    MainWindow.mapper.setModel(model)
    MainWindow.mapper.addMapping(MainWindow.l_user_name_ch_2, 0)
    MainWindow.mapper.addMapping(MainWindow.lineEdit_3, 1)
    MainWindow.mapper.addMapping(MainWindow.l_user_pass1_ch_2, 2)
    MainWindow.mapper.addMapping(MainWindow.lineEdit_4, 3)
    MainWindow.mapper.addMapping(MainWindow.lineEdit, 4)
    MainWindow.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.ManualSubmit)
    #MainWindow.mapper.addMapping(MainWindow.l_groups, 5, QtGui.QAbstractItemView.QStringListModel)
    MainWindow.mapper.toFirst()
def change_client():
    if MainWindow.l_client.selectionModel().hasSelection():
        MainWindow.user_stack_2.setCurrentIndex(2)
        MainWindow.mapper.setCurrentIndex(MainWindow.l_client.selectionModel().selectedIndexes()[0].row())
        model = MainWindow.l_client.model().getSubModel(MainWindow.l_client.selectionModel().selectedIndexes()[0])
        MainWindow.l_groups.setModel(model)
        MainWindow.b_remove_user_3.setEnabled(True)

    else:
        MainWindow.user_stack_2.setCurrentIndex(2)
        MainWindow.b_remove_user_3.setEnabled(False)

def modify_client_rejected():
    MainWindow.user_stack_2.setCurrentIndex(1)

def modify_client():
    MainWindow.user_stack_2.setCurrentIndex(1)
    MainWindow.l_groups.model().instertInDb()

    MainWindow.mapper.submit()

def purge_proxys():
    print("purging...")
    import shutil
    with db_session:
        for x in range(0,max(c.id for c in Cards)):
            print(("found cadr : %s"%x))
            if not Cards[x]:
                print(("purge cadr : %s"%x))
                for drive in select( p for p in ProxyDrive)[:]:
                    proxy = "%s/%s/"%(drive.path,x)
                    try:
                        shutil.rmtree(proxy)

                    except:
                        pass
    ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,"Erreur",
                                      "Tous les proxys inutiles ont été supprimés",
                                      QtWidgets.QMessageBox.Ok,
                                      MainWindow)
    ok.exec_()

@db_session
def purgeError():
    card_to_purge = select(c for c in Cards if c.stat == 0 or c.stat == 1)[:]
    if card_to_purge:
        import shutil
        print('asdfsdsfsdf')
        er_dialog = loadUi("ui/error_at_launch.ui",QtWidgets.QDialog(MainWindow))

        text = "<h1> La précédente session ne s'est pas terminée correctement</h1><i>Pour des raisons de " \
               "sécurité les cartes suivantes vont être retirées de la bases de données.</i><li>"
        for card in card_to_purge :
            text += "<ul>%s</ul>"% card.name

        text += "</ul>"
        er_dialog.textEdit.setHtml(text)
        er_dialog.buttonBox.accepted.connect(er_dialog.accept)
        er_dialog.exec_()
        progress = QtWidgets.QProgressDialog("Suppression des cartes..", "", 0, len(card_to_purge), MainWindow)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        print(("###%s card to purge"%(len(card_to_purge))))
        i = 0
        for card in card_to_purge:


            cardPath = "%s/%s/"%(card.disk.mountPoint,card.id)
            try:
                ass = select(a for a in Assets if a.card == card)[:]
                proxyPath = "%s/%s"%(ass[0].proxyDisk.path, card.id)
            except:
                proxyPath = None
            raidCardPath = "%s/%s/"%(Raid[0].mountPoint,card.id)

            try:
                shutil.rmtree(cardPath)
            except:
                pass
            try:
                shutil.rmtree(raidCardPath)
            except:
                pass
            try:
                if proxyPath:
                    shutil.rmtree(proxyPath)
            except:
                pass

            old_free = card.disk.free
            card.disk.free = str(int(old_free) - int(card.poids))



            print(("####REMOVE Card %s From DB"%card.id))
            card.delete()
            print("####update WIDGET")
            i = i +1
            progress.setValue(i)
            logging.debug("updating disk udes space")
            allDisk = select(d for d in Disk)[:]
            for disk in allDisk:
                cards = select(c for c in Cards if c.disk == disk)[:]

                total = 0
                for card in cards:
                    total = total + int(card.poids)
                    disk.free = str(total)



def quit():
    print("I QUIT")
    MainWindow.bckupThread.stop()
    os.remove("/var/lock/mamman4")
    QtCore.QThreadPool.globalInstance().waitForDone(1000)




def add_client_sheet():
    logging.debug("adding client sheet")
    MainWindow.l_client_name.setText("")
    MainWindow.l_client_fullName.setText("")
    MainWindow.l_client__pass1.setText("")
    MainWindow.l_client_pass2.setText("")
    MainWindow.l_client_company.setText("")
    MainWindow.l_client_mail.setText("")
    MainWindow.user_stack_2.setCurrentIndex(0)
    MainWindow.stackedWidget_4.setCurrentIndex(1)
    model = GroupModel()
    MainWindow.l_client_groups.setModel(model)



def add_client():
    print("adding into db")
    if MainWindow.l_client__pass1.text() == MainWindow.l_client_pass2.text():
        with db_session:
            if not exists(c for c in Client if c.name == MainWindow.l_client_name.text()):

                new_client = Client(name=MainWindow.l_client_name.text(),
                                    completeName = MainWindow.l_client_fullName.text(),
                                    company = MainWindow.l_client_company.text(),
                                    passWord = MainWindow.l_client__pass1.text(),
                                    mail = MainWindow.l_client_mail.text())

                for line in MainWindow.l_client_groups.model().get_dict():
                    if line['state'] == 2:

                            group = get(g for g in ProjectGroup if g == line['object'])
                            new_client.defaultGroup.add(group)
                    else:
                        pass
                commit()
                MainWindow.user_stack_2.setCurrentIndex(1)
                MainWindow.stackedWidget_4.setCurrentIndex(0)
                MainWindow.l_client.model().refresh()
            else :
                error_message("Impossible d'ajouter l'utilisateur","Cet utilisateur existe déjà")
    else:
        error_message("Impossible d'ajouter l'utilisateur","Les mots de passe ne sont pas concordants.")

def client_rejected():
    MainWindow.user_stack_2.setCurrentIndex(1)
    MainWindow.stackedWidget_4.setCurrentIndex(0)



def fix_timecode(id):
    from .modules.ffprober import FFProber
    print(("fixing timecode %s"%id))
    with db_session:
        clips = select(c for c in Assets if c.card.id == id)
        for c in clips:
            path = "%s/%s/%s%s"%(Raid[0].mountPoint,c.card.id,c.card.firsName,c.clipPath)
            print(path)
            prob = FFProber(path,'xml',{'xpath':"/ns:NonRealTimeMeta/ns:LtcChangeTable/ns:LtcChange[1]","nskey": None,'attrib':'value',"SonyInverted":True, "same_path":True,"end_name":"M01.XML" })
            c.timeCode = prob.get_time_code()



def error_in_backup(msg,id):
    error_message("Erreur de copie",msg)
    MainWindow.bckupThread.add_copy(id)


def change_default_group():
    print((MainWindow.listView.selectionModel().selectedIndexes()))
    #try :
    dialog.show_right_dialog(MainWindow.listView.model().getItem(MainWindow.listView.selectionModel().selectedIndexes()[0]))
    #except:
    #    error_message(u"Impossible de modifier les droits",sys.exc_info())

def refresh_disks():
    try:
        MainWindow.pool = DiskPool(MainWindow,warn=True)
    except IdentificationNotReadable:
        error_message("Impossible de lire la clé d'un disque...","Contactez votre administrateur")
    except NoOnlineDiskError:
        error_message("Aucun disque n'est en ligne","Vous devrez corriger le problème avant d'ajouter une carte")
    except BackupCurrentOfflineError:
        error_message("Le disque de sauvegarde du disque par défaut n'a pas été trouvé","Vous devrez corriger le problème avant d'ajouter une carte")
    except NoCurrentError:
        error_message("Le disque  par défaut n'a pas été trouvé","Vous devrez corriger le problème avant d'ajouter une carte")
    except NoCurrentProxyError:
        error_message("Impossible de localiser le disque de proxy","Vous devrez corriger le problème avant d'ajouter une carte")
    except NoProxyError:
        error_message("Aucun disque de proxy n'est disponible","Vous devrez corriger le problème avant d'ajouter une carte")



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("fusion"))
    darkPalette = QtGui.QPalette()
    darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(53,53,53));
    darkPalette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(25,25,25))
    darkPalette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53,53,53))
    darkPalette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(53,53,53))
    darkPalette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red);
    darkPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))

    darkPalette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))

    darkPalette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

    app.setPalette(darkPalette)

    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    MainWindow = loadUi('ui/tree.ui')
    MainWindow.show()



    if QtCore.QFile.exists("/var/lock/mamman4"):
        ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Erueur",
                              "Un autre utilisateur utilise la MamManager sur ce poste. Pour des raisons de sécurité, MamManager ne peut être exécuté que par un seul utilisateur à la fois.",
                              QtWidgets.QMessageBox.Yes,
                              MainWindow)
        ok.exec_()
        exit()
    else:
        os.system("touch /var/lock/mamman4")
    dialog = ModalDialog(MainWindow)




    try:
        db.generate_mapping(check_tables=True, create_tables=True)
        MainWindow.dbIcon.setIcon(QtGui.QIcon("images/ic_sync_green_18dp.png"))


    except:
        MainWindow.b_connect.setEnabled(False)
        MainWindow.l_user.setEnabled(False)
        MainWindow.l_pass.setEnabled(False)
        db_error(sys.exc_info())

    #reinit_proxys()
    ###############
    ##CONNECTIONS##
    ###############

    MainWindow.updter = Updater()
    MainWindow.buttonBox_3.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
    #inset_value()
    MainWindow.buttonBox_2.accepted.connect(updateUserData)

    MainWindow.b_connect.clicked.connect(connect)
    MainWindow.b_rushes.clicked.connect(lambda: MainWindow.stack.setCurrentIndex(0))
    MainWindow.b_users.clicked.connect(show_user_page)
    MainWindow.b_progress.clicked.connect(lambda: MainWindow.stack.setCurrentIndex(3))
    MainWindow.b_clients.clicked.connect(show_client_page)
    MainWindow.b_add_client.clicked.connect(add_client_sheet)
    MainWindow.b_drives.clicked.connect(get_disk_usage)
    MainWindow.b_add_user.clicked.connect(add_user_sheet)
    MainWindow.buttonBox.rejected.connect(user_rejected)
    MainWindow.buttonBox_3.rejected.connect(client_rejected)
    MainWindow.buttonBox_3.accepted.connect(add_client)
    MainWindow.buttonBox_4.rejected.connect(modify_client_rejected)
    MainWindow.buttonBox_4.accepted.connect(modify_client)
    MainWindow.buttonBox_2.rejected.connect(user_rejected)
    MainWindow.buttonBox_2.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
    MainWindow.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
    MainWindow.deconnect.setVisible(False)
    MainWindow.deconnect.linkActivated.connect(decon)
    MainWindow.l_user.textChanged[str].connect(lambda : MainWindow.b_connect.setEnabled(True)
    if MainWindow.l_user.text() and MainWindow.l_pass.text() else MainWindow.b_connect.setEnabled(False))
    MainWindow.l_pass.textChanged[str].connect(lambda : MainWindow.b_connect.setEnabled(True)
    if MainWindow.l_user.text() and MainWindow.l_pass.text() else MainWindow.b_connect.setEnabled(False))
    MainWindow.l_user_name.textChanged.connect(canok)
    MainWindow.l_user_pass1.textChanged.connect(canok)
    MainWindow.l_user_pass2.textChanged.connect(canok)
    MainWindow.l_email.textChanged.connect(canok)
    MainWindow.l_user_name_ch.textChanged.connect(canok)
    MainWindow.chl_mail.textChanged.connect(canok)

    MainWindow.l_user_pass_ch.textChanged.connect(canok)

    MainWindow.actionPurger_les_miniatures.triggered.connect(purge_proxys)
    MainWindow.stack.currentChanged[int].connect(stackChanged)
    MainWindow.asset_disk_change.clicked.connect(change_disk)
    MainWindow.asset_disk_update.clicked.connect(get_disk_usage)
    MainWindow.proxy_disk_change.clicked.connect(proxy_change)
    MainWindow.toolButton_2.clicked.connect(change_passwd_client)
    MainWindow.change_pass.clicked.connect(change_passwd_user)
    import os
    non_symbolic=os.path.realpath(sys.argv[0])
    programFilePath=os.path.dirname(os.path.join(sys.path[0], os.path.basename(non_symbolic)))
    MainWindow.buttonBox.accepted.connect(add_user)
    MainWindow.b_remove_user.clicked.connect(delete_user)
    refresh_disks()

    MainWindow.proxyMaker = EncodeFunction(MainWindow)
    MainWindow.copier = CopyFunction(MainWindow.proxyMaker,MainWindow)

    MainWindow.analyser = AnalyseFunction(MainWindow.copier,MainWindow,"")


    if is_first_start():
        ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,"Erueur",
                                      "Ceci est votre premier démarrage, nous allons initialiser la base de données :<br>",
                                      QtWidgets.QMessageBox.Yes,
                                      MainWindow)
        ok.exec_()

        userName, ok = QtWidgets.QInputDialog.getText(MainWindow.centralwidget,"Nom du compte","Choisissez un nom pour le premier utilisateur")
        if ok and userName:
            passWd, ok = QtWidgets.QInputDialog.getText(MainWindow.centralwidget,"mot de passe","Choisissez un mot de passe",QtGui.QLineEdit.Password)
            if ok and passWd:
                passWd2, ok = QtWidgets.QInputDialog.getText(MainWindow.centralwidget,"mot de passe","Confirmez le mot de passe",QtGui.QLineEdit.Password)
                if ok and passWd2:
                    if passWd2 == passWd:
                        with db_session:
                            admin = Users(name=userName, passw = passWd , admin = True, system = False, motu = True)
                            admin = Users(name="DELETED_USER", passw = "NO_NEED" , admin = True, system = True)
                            try:
                                os.mkdir("/home/mamshare/%s")%userName
                            except:
                                pass

                            '''
                            db.execute("""CREATE SCHEMA perso;
                            CREATE EXTENSION unaccent;
                            CREATE TEXT SEARCH CONFIGURATION perso.fr ( COPY = french );
                            ALTER TEXT SEARCH CONFIGURATION perso.fr
                            ALTER MAPPING FOR hword, hword_part, word
                                    WITH unaccent, french_stem;
                            ALTER TABLE assets ADD COLUMN vector tsvector;
                            CREATE TRIGGER ass_update BEFORE INSERT OR UPDATE
                               ON assets FOR EACH ROW
                               EXECUTE PROCEDURE tsvector_update_trigger(vector, 'perso.fr', tag, comment, pays, ville);
                            CREATE INDEX idx_vecteur ON assets USING gin (vector);
                            CREATE INDEX idx_index ON assets USING hash (id);
 ALTER TABLE cards ADD COLUMN vector tsvector;
                            CREATE TRIGGER card_update BEFORE INSERT OR UPDATE
                               ON cards FOR EACH ROW
                               EXECUTE PROCEDURE tsvector_update_trigger(vector, 'perso.fr', name, comment);
                            CREATE INDEX idx_card_vecteur ON cards USING gin (vector);
                            CREATE INDEX idx_card_index ON cards USING hash (id);
 ALTER TABLE project ADD COLUMN vector tsvector;
                            CREATE TRIGGER project_update BEFORE INSERT OR UPDATE
                               ON project FOR EACH ROW
                               EXECUTE PROCEDURE tsvector_update_trigger(vector, 'perso.fr', name, comment);
                            CREATE INDEX idx_P_vecteur ON project USING gin (vector);
                            CREATE INDEX idx_P_index ON project USING hash (id);
 ALTER TABLE projectgroup ADD COLUMN vector tsvector;
                            CREATE TRIGGER projectGr_update BEFORE INSERT OR UPDATE
                               ON projectgroup FOR EACH ROW
                               EXECUTE PROCEDURE tsvector_update_trigger(vector, 'perso.fr', name, comment);
                            CREATE INDEX idx_PG_vecteur ON projectgroup USING gin (vector);
                            CREATE INDEX idx_PG_index ON projectgroup USING hash (id);
                           CREATE INDEX trgm_tags
  ON tags
  USING gist
  (name COLLATE pg_catalog."default" gist_trgm_ops);





create type holder as (id int, name TEXT, sml float4);
create function getsimilartag(TEXT) returns holder as

$$
SELECT *, similarity(name, $1) AS sml  FROM tags  WHERE name% $1  ORDER BY sml DESC;
$$
 language 'sql';


  """)'''

                        change_disk()
                        proxy_change()

                    else:
                        ok = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,"Erueur",
                              "Mot de passe non concordants",
                              QtWidgets.QMessageBox.Yes,
                              MainWindow)
                        ok.exec_()
                        exit()
                else:
                    exit()
            else:
                exit()
        else:
            exit()
    delta =0

    MainWindow.l_client_name.textChanged.connect(canok)
    MainWindow.l_client_fullName.textChanged.connect(canok)
    MainWindow.l_client__pass1.textChanged.connect(canok)
    MainWindow.l_client_pass2.textChanged.connect(canok)
    MainWindow.l_client_company.textChanged.connect(canok)
    MainWindow.l_client_mail.textChanged.connect(canok)
    MainWindow.sendmailToClients.triggered.connect(send_mail_clients)
    MainWindow.sendmailToUsers.triggered.connect(send_mail_users)
    MainWindow.sendmailToDevel.triggered.connect(send_mail_devel)
    #MainWindow.rush_browser = RushWidget()
    MainWindow.rush_model = RushModel(["rushes"])
    MainWindow.rush_browser.setModel(MainWindow.rush_model)
    pannel = loadUi("ui/mdata.ui")

    MainWindow.rush_browser.setPreviewWidget(pannel)
    MainWindow.rush_browser.selectionModel().selectionChanged[QtCore.QItemSelection,QtCore.QItemSelection]\
        .connect(update_data)

    MainWindow.mailer = Mailer()
    MainWindow.b_remove_user_3.clicked.connect(delete_client)
    with db_session:
        logging.debug("Updating disk used space")
        allDisk = select(d for d in Disk)[:]
        for disk in allDisk:
            cards = select(c for c in Cards if c.disk == disk)[:]
            total = 0
            for card in cards:
                total = total + int(card.poids)
                disk.free = str(total)


    QtCore.QThreadPool.globalInstance().setMaxThreadCount(8)
    MainWindow.bckupThread=BackupThread()
    MainWindow.bckupThread.setAutoDelete(True)
    MainWindow.add_b.clicked.connect(add_collection)
    MainWindow.bckupThread.updateStatut[int].connect(lambda val: MainWindow.lto_progress.setValue(val))
    MainWindow.bckupThread.updatePh[str].connect(lambda text: MainWindow.label_49.setText(text))
    MainWindow.bckupThread.error[str,int].connect(error_in_backup)
    QtCore.QThreadPool.globalInstance().start(MainWindow.bckupThread,1)
    with db_session:
        notsaved = select(c for c in Cards if c.stat == 2)[:]
        for n in notsaved:
            logging.debug("Adding not saved card %s"%n.name)
            MainWindow.bckupThread.add_copy(n.id)



    logging.debug("Application sucessfully launched")




    app.aboutToQuit.connect(quit)

    sys.exit(app.exec_())

