# -*- coding: utf-8 -*-
__author__ = 'fcp6'
import json


import smtplib
import configparser
from email.mime.text import MIMEText



class Mailer(object):
    def __init__(self):


        self.Config =configparser.ConfigParser()
        self.Config.read('mail.conf')







    def ConfigSectionMap(self,section):
        dict1 = {}
        options = self.Config.options(section)
        for option in options:
            try:
                dict1[option] = self.Config.get(section, option)
                if dict1[option] == -1:
                    print(("skip: %s" % option))
            except:
                print(("exception on %s!" % option))
                dict1[option] = None
        return dict1


    def sendmail(self,toaddrs,strmsg,subject):
        fromaddr = self.ConfigSectionMap("GoogleMail")['username']
        msg = MIMEText(strmsg)
        msg['Subject'] = subject
        msg['From'] = fromaddr
        msg['To'] = toaddrs

        # Credentials (if needed)
        username = self.ConfigSectionMap("GoogleMail")['username']
        password = self.ConfigSectionMap("GoogleMail")['password']

        # The actual mail send
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg.as_string())
        server.quit()

    def get_text_mail(self,message):
        with open('%s.mail'%message,'r') as f:
            text = f.read()
        return text.split('///')






'''
a.sendmail("victorien.tronche@gmail.com",a.get_text_mail('hello')[1],a.get_text_mail('hello')[0])

'''