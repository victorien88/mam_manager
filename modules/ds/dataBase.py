__author__ = 'fcp6'


import datetime
from pony.orm import *
db = Database()
db.bind('postgres', host='localhost',port=5432, user='postgres', password='root', database='mam')
#db.bind('postgres', host='localhost',port=5433, user='postgres', password='root', database='mam')


class ProxyDrive(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT',auto=True)
    path = Required(unicode)
    online = Required(bool)
    name = Required(unicode)
    default = Required(bool)
    verificationKey = Required(unicode)
    child = Set("Assets")
    validation = Set('Validation', reverse='proxyDisk')

class Validation(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Optional(unicode,unique=True)
    uuid = Optional(unicode)
    allowedClients = Set('Client', reverse="validation")
    clientHasValided = Set('Client', reverse="valided")
    clientHasRejected = Set('Client', reverse="rejected")
    group = Required('ProjectGroup')
    sended = Required(bool,default=False)
    comment = Required(unicode)
    supervisors = Set('Users')
    client_comment = Optional(unicode)
    proxy_name = Required(unicode)
    proxyDisk = Set(ProxyDrive, reverse='validation')

class Client(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT',auto=True)
    name = Required(unicode,unique=True)
    completeName = Optional(unicode)
    company = Optional(unicode)
    passWord = Required(unicode)
    mail = Optional(unicode)
    defaultGroup = Set("ProjectGroup")
    validation = Set(Validation, reverse="allowedClients")
    valided = Set(Validation, reverse="clientHasValided")
    rejected = Set(Validation, reverse="clientHasRejected")

class Collection(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT',auto=True)
    name = Required(unicode,unique=True)
    comment = Optional(unicode)
    child = Set("ProjectGroup")


class BackupDisk(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode,unique=True)
    mountPoint = Required(unicode)
    verificationKey = Required(unicode)
    online = Required(bool)

class ProjectGroup(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode,unique=True)
    comment = Optional(unicode)
    collection = Required(Collection)
    child = Set("Project")
    clientDefault = Set(Client)
    defaultFollowingUser = Set("Users")
    valid = Set(Validation)





class Preferences(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT',auto=True)
    key = Optional(unicode)
    value = Optional(unicode)

class Users(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT',auto=True)
    name = Required(unicode,unique=True)
    passw = Required(unicode)
    admin = Required(bool)
    mail = Optional(unicode)
    canSeeMasters = Required(bool, default=True)
    canValidate = Required(bool,default=False)
    defaulValidationGroup = Set(ProjectGroup)
    system = Required(bool)
    motu = Required(bool, default=False)
    folowedValid = Set(Validation,reverse='supervisors')




class Disk(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode,unique=True)
    child = Set('Cards')
    mountPoint = Required(unicode)
    online = Required(bool)
    current = Required(bool)
    verificationKey = Required(unicode)
    free = Required(unicode)


class Raid(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Optional(unicode)
    mountPoint = Optional(unicode)
    used = Optional(unicode)
    deletedFiles = Optional(int,sql_type='BIGINT')
    limit = Optional(unicode)


class Project(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode,unique=True)
    comment = Optional(unicode)
    real = Optional(unicode)
    group = Required(ProjectGroup)
    child = Set("Cards")

class Cards(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    audio = Required(bool, default=False)
    comment = Optional(unicode)
    poids = Optional(unicode)
    name = Required(unicode,unique=True)
    project = Required(Project)
    disk = Required(Disk)
    jri = Optional(unicode)
    ingestDate = Required(datetime.date)
    tournageDate = Required(datetime.date)
    owner = Required(unicode)
    copied = Required(bool)
    copyProgress = Optional(int,sql_type='BIGINT')
    cameraModel=Optional(unicode)
    originalPath = Required(unicode)
    locked = Required(bool)
    stat = Required(int, sql_type='BIGINT') # 0 = Job not started 1 = jub started 2 = job finished 3 = backuped
    ingestedBy = Required(unicode)
    child = Set("Assets")
    firsName = Required(unicode)
    on_raid = Required(bool, default=True)




class Assets(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode)
    comment = Optional(unicode)
    tag = Optional(unicode)
    stat = Required(int,sql_type='BIGINT') #0 normal #1 In queue #2 started  #3 success #4 error
    progression = Optional(int,sql_type='BIGINT')
    hasProxy = Required(bool)
    proxyPath = Optional(unicode)
    card = Required(Cards)
    videoSize = Optional(unicode)
    videoFps = Optional(unicode)
    derush = Optional(unicode)
    durationSec = Required(unicode)
    durationFrm = Required(int)
    timeCode = Required(unicode)
    videoCodec = Required(unicode)
    proxyDisk = Optional(ProxyDrive)
    clipPath = Required(unicode)
    pays = Optional(unicode)
    ville = Optional(unicode)
    ville = Optional(unicode)
    nb_audio_stream = Optional(int,sql_type='BIGINT')


class Tags(db.Entity):
    id = PrimaryKey(int,sql_type='BIGINT', auto=True)
    name = Required(unicode)


''''
class DataBase:
    def __init__(self):

        self.db.generate_mapping(create_tables=True)

    db_session
    def get_projects_groups(self):
        qu = select(c for c in ProjectGroup).order_by(ProjectGroup.name)[:]
        return qu
'''''
