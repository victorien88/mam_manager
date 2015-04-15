# -*- coding: utf-8 -*-
__author__ = 'victorientronche'
import subprocess
import json
import logging
from pipes import quote
logging.basicConfig( format='%(asctime)s %(message)s', level=logging.DEBUG)


class ZeroAudioTrackError(Exception):
    pass

class ZeroDurationError(Exception):
    pass

class ZeroVideoCodecError(Exception):
    pass

class ZeroDimentionError(Exception):
    pass

class ZeroFpsError(Exception):
    pass

class ZeroTimecodeError(Exception):
    pass

class NoVideoFileError(Exception):
    pass

class FFProber(object):
    def __init__(self,moviefile,mode,xpath):
        self.movieFile = quote(moviefile)
        self.unquottedfile = moviefile
        self.mode = mode
        self.xpath = xpath
        scmd =  """ffprobe  -show_streams -of json -i %s"""% self.movieFile
        fcmd = """ffprobe  -show_format -of json -i %s"""%self.movieFile
        ecmd = """./exif/exiftool %s  -json"""%self.movieFile
        print(fcmd)
        print(scmd)
        process1 = subprocess.Popen(scmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)

        process2 = subprocess.Popen(fcmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
        process3 = subprocess.Popen(ecmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        print(ecmd)
        self.streams = json.loads(process1.communicate()[0])
        self.format = json.loads(process2.communicate()[0])
        try:
            self.exif = json.loads(process3.communicate()[0])

        except:
            raise NoVideoFileError



        try:
            self.streams["streams"][0]
        except:
            raise NoVideoFileError
    def get_audio_tracks_nb(self):
        """
        :return:returns number of audio track"""

        nb = 0
        for i in range(0, int(self.format['format']['nb_streams'])):
            if self.streams['streams'][i]['codec_type'] == 'audio':
                nb = nb + 1
            else:
                pass
        if nb == 0:
            raise ZeroAudioTrackError
        else:
            return nb

    def get_duration_sec(self):
        duration = self.format['format']['duration']
        if duration:
            return self.format['format']['duration']
        else:
            raise ZeroDurationError


    def get_data_stream(self):
        data_stream = None
        for i in range(0, int(self.format['format']['nb_streams'])):
                    if self.streams['streams'][i]['codec_type'] == 'data':
                        data_stream = i
        print(data_stream)
        return data_stream

    def normalize_exif_timecode(self,tcn):
        if tcn == "0 s":
            return "00:00:00:00"
        else:
            tc = tcn.split(":")
            return "%s%s:%s%s:%s%s:%s%s"%("0" if len(tc[0]) < 2 else "",
                                           tc[0],
                                           "0" if len(tc[1]) < 2 else "",
                                           tc[1],
                                           "0" if len(tc[2]) < 2 else "",
                                           tc[2],
                                            "0" if len(tc[2]) < 2 else "",
                                            tc[3])


    def get_time_code(self):
        """:returns SMTE TIMECODE"""
        if not self.mode:
            hastctag = False
            if "tags" in self.format['format']:
                if "timecode" in list(self.format['format']['tags'].keys()):
                    hastctag = True
            timecode = None
            dataid = self.get_data_stream()

            """for .mov Files"""

            if dataid:
                try:
                    logging.warning("with data track")
                    timecode = self.streams['streams'][dataid]['tags']['timecode']
                except KeyError:
                    raise ZeroTimecodeError

                """extract timecode from exifs info"""

            elif hastctag:
                    print("using tag track on format")
                    timecode =  self.format['format']['tags']['timecode']
            elif "TimeCode" in list(self.exif[0].keys()):
                print((self.exif[0]['TimeCode']))

                timecode = self.normalize_exif_timecode(self.exif[0]['TimeCode'])
            elif "StartTimecode" in list(self.exif[0].keys()):
                    print("with starttimecode exif")
                    timecode = self.normalize_exif_timecode(self.exif[0]['StartTimecode'])

            elif "timecode" in self.streams['streams'][0]:
                    print("with timecode on video track 0")
                    timecode = self.streams['streams'][0]['timecode']

            if timecode == None:
                raise ZeroTimecodeError
            else:
                return timecode
        else:
            if self.mode == "xml":
                return self.get_xml_tc()
            elif self.mode == "track_on_format":
                print("programmed track_on_format")
                timecode =  self.format['format']['tags']['timecode']
                if timecode:
                    print(timecode)
                    return timecode
                else:
                    raise ZeroTimecodeError
            elif self.mode == "no_tc":
                    raise ZeroTimecodeError
            elif self.mode == "data_track":
                print("programmed data_track")
                dataid = self.get_data_stream()
                timecode = self.streams['streams'][dataid]['tags']['timecode']
                if timecode:
                    return timecode
                else:
                    raise ZeroTimecodeError
            elif self.mode=='exif_timecode':
                timecode = self.normalize_exif_timecode(self.exif[0]['TimeCode'])
                print("programmed exif tc")
                if timecode:
                    return timecode
                else:
                    raise ZeroTimecodeError





    def get_video_codec(self):
        """
        :return: video codec """

        codec = None
        for i in range(0, int(self.format['format']['nb_streams'])):
            if self.streams['streams'][i]['codec_type'] == 'video':
                codec = self.streams['streams'][i]['codec_long_name']
            else:
                continue
        if codec:
            return codec
        else:
            raise ZeroVideoCodecError

    def get_video_size(self):
        """
        :returns dimention of video
        """
        dimention = None
        for i in range(0, int(self.format['format']['nb_streams'])):
            if self.streams['streams'][i]['codec_type'] == 'video':
                dimention = "%s X %s"%(str(self.streams['streams'][i]['width']),str(self.streams['streams'][i]['height']))
            else:
                continue
        if dimention:
            return dimention
        else:
            raise ZeroDimentionError

    def get_video_fps(self):
        """:returns dimention of video"""
        fps = None
        for i in range(0, int(self.format['format']['nb_streams'])):
            if self.streams['streams'][i]['codec_type'] == 'video':
                strFrate = self.streams['streams'][i]['avg_frame_rate']
                listFrate = strFrate.split("/")
                fps = str(float(listFrate[0])/float(listFrate[1]))
            else:
                continue
        if fps:
            return fps
        else:
            raise ZeroDimentionError

    def get_xml_tc(self):
        print("reading xml")
        from lxml import etree
        import os
        print(self.xpath)
        if self.xpath['same_path']:
            path, filename = os.path.split(self.unquottedfile)
        else:
            raise ZeroTimecodeError
        tree =  etree.parse("%s/%s%s"%(path,os.path.splitext(filename)[0],self.xpath["end_name"]))
        tc = tree.xpath(self.xpath['xpath'],namespaces={"ns":tree.getroot().nsmap[self.xpath['nskey']]})[0].get("value")
        if self.xpath["SonyInverted"]:
            return self.arrange_sony_tc(tc)
        else:
            raise ZeroTimecodeError

    def arrange_sony_tc(self,stc):
        '''
        Sony TC are exprimed in IISSMMHH way this function returns a smte tc
        :param tc:
        :return:
        '''
        return "%s%s:%s%s:%s%s:%s%s"%(stc[6],stc[7],stc[4],stc[5],stc[2],stc[3],stc[0],stc[1])



class AudioFFprober(FFProber):
    def __init__(self,moviefile,mode=None,xpath=None):
        FFProber.__init__(self,moviefile=moviefile,mode=mode,xpath=xpath)

    def get_video_fps(self):
        return 25

    def get_mdata(self):
        a = ''
        try :
            a += "Titre : {}\n".format(self.exif[0]["Title"])
        except KeyError:
            a += "Titre : N/A\n"
        try :
            a += "Artist : {}\n".format(self.exif[0]["Artist"])
        except KeyError:
            a += "Artist : N/A\n"
        try :
            a += "Album : {}\n".format(self.exif[0]["Album"])
        except KeyError:
            a += "Album : N/A\n"
        try :
            a += "Genre : {}\n".format(self.exif[0]["Genre"])
        except KeyError:
            a += "Genre : N/A\n"
        try :
            a += "Year : {}\n".format(self.exif[0]["Year"])
        except KeyError:
            a += "Year : N/A\n"
        try :
            a += "SampleRate : {}\n".format(self.exif[0]["SampleRate"])
        except KeyError:
            a += "SampleRate : N/A\n"
        try :
            a += "Track : {}\n".format(self.exif[0]["Track"])
        except KeyError:
            a += "Track : N/A\n"

        return a


    def get_audio_codec(self):
        """
        :return: audio codec """

        codec = None
        for i in range(0, int(self.format['format']['nb_streams'])):
            if self.streams['streams'][i]['codec_type'] == 'audio':
                codec = self.streams['streams'][i]['codec_long_name']
            else:
                continue
        if codec:
            return codec
        else:
            raise ZeroVideoCodecError





if __name__ == '__main__':
    #a = AudioFFprober("/home/ingest/Documents/AUDIO/01 Roméo Et Juliette feat Juliette Greco.mp3")
    a = AudioFFprober("/home/ingest/Documents/AUDIO/01. 01 - It.flac")
    print(a.get_audio_tracks_nb())
    print(a.get_mdata())
    print(a.get_audio_codec())
    print(a.get_duration_sec())

    '''
    b = {'xpath':"/ns:NonRealTimeMeta/ns:LtcChangeTable/ns:LtcChange[1]","nskey": None,'attrib':'value',"SonyInverted":True, "same_path":True,"end_name":"M01.XML" }
    a = FFProber("""/media/9toRushes/GPN 315 MA MAISON PAS COMME LES AUTRES/SAUV DD TOURNAGE/ARCHIVES GUILLAUME/Timelapse Videos/Random timelapses/XX - Tiny House Thanksgiving (1080p).mp4""","","")
    try:
        print a.get_time_code()
    except ZeroTimecodeError:
        print "01:00:00:00"
    print a.get_duration_sec()
    print a.get_video_codec()
    '''

