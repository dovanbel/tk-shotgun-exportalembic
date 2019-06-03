# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
App that launches a Publish from inside of Shotgun.

"""

from tank.platform import Application
from tank import TankError
import tank
import sys
import os
import sgtk
import tempfile
import random

def rrGetRR_Root():
        if os.environ.has_key('RR_ROOT'):
            return os.environ['RR_ROOT']
        HCPath="%"
        if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
            HCPath="%RRLocationWin%"
        elif (sys.platform.lower() == "darwin"):
            HCPath="%RRLocationMac%"
        else:
            HCPath="%RRLocationLx%"
        if HCPath[0]!="%":
            return HCPath
        return"";

def rrWriteNodeStr(fileID,name,text):
        text=text.replace("&","&amp;")
        text=text.replace("<","&lt;")
        text=text.replace(">","&gt;")
        text=text.replace("\"","&quot;")
        text=text.replace("'","&apos;")
        text=text.replace(unichr(228),"&#228;")
        text=text.replace(unichr(246),"&#246;")
        text=text.replace(unichr(252),"&#252;")
        text=text.replace(unichr(223),"&#223;")
        try:
            fileID.write("    <"+name+">  "+text+"   </"+name+">\n")
        except:
            pass
        
def rrWriteNodeInt(fileID,name,number):
        fileID.write("    <"+name+">  "+str(number)+"   </"+name+">\n")
        
def rrWriteNodeBool(fileID,name,value):
        if value:
            fileID.write("    <"+name+">   1   </"+name+">\n")
        else:
            fileID.write("    <"+name+">   0   </"+name+">\n")


def rrWriteJobToFile(fileID, rootPath, scenePath, seq, shot, version):
        fileID.write("<Job>\n")
        if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
            rrWriteNodeStr(fileID,"SceneOS", "win")
        elif (sys.platform.lower() == "darwin"):
            rrWriteNodeStr(fileID,"SceneOS", "mac")
        else:
            rrWriteNodeStr(fileID,"SceneOS", "lx")
        rrWriteNodeStr(fileID,"Software", "Maya")
        rrWriteNodeInt(fileID,"Version", 2013)
        rrWriteNodeStr(fileID,"SceneName", scenePath)
        rrWriteNodeStr(fileID,"SceneDatabaseDir", rootPath)
        rrWriteNodeStr(fileID,"Renderer", "mayaPy")
        rrWriteNodeStr(fileID,"CustomScript", "//VSERVER01/RoyalRender6/render_apps/scripts/mayapy_export_abc.py")
        rrWriteNodeStr(fileID,"CustomData", "*")
        rrWriteNodeStr(fileID,"ImageFilename", os.path.dirname(scenePath))
        
        

        fileID.write("</Job>\n") 
        fileID.write("<SubmitterParameter>DefaultClientGroup=0~farm_windows LittleJob=1~1 CustomSceneName=1~"+seq+" CustomSHotName=1~"+shot+" CustomVersionName=1~"+version+" </SubmitterParameter>\n")  

def rrSetNewTempFileName(UIMode):
        random.seed()
        if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
            if os.environ.has_key('TEMP'):
                nam=os.environ['TEMP']
            else:
                nam=os.environ['TMP']
            nam+="\\"
        else:
            nam="/tmp/"
        nam+="rrSubmitMaya_"
        if (UIMode):
            nam+=str(random.randrange(1000,10000,1))
        nam+=".xml"
        print nam
        return nam



class LaunchPublish(Application):
    
    def init_app(self):
        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")
        
        p = {
            "title": "Publish all the Alembic from this file",
            "entity_types" : ["PublishedFile"],
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": True
        }
        
        self.engine.register_command("publish_abc", self.publish_abc, p)


    def publish_abc(self, entity_type, entity_ids):

        rootPath = os.path.dirname(self.tank.roots["primary"])

        for uid in entity_ids:

            d = self.shotgun.find_one(entity_type, [["id", "is", uid]], ["name", "path", "published_file_type", "entity", "image", "task"])

            if d.get("entity").get("type") == "Shot":

                path_on_disk = d.get("path").get("local_path")

                ctx = self.tank.context_from_path(path_on_disk)

                #template_work = self.get_template("template_shot_work")
                fileTemplate = self.tank.template_from_path(path_on_disk) 
                fields = fileTemplate.get_fields(path_on_disk)
               
                # use templates to convert to publish path:


                simpleName = fields["Shot"]
                pfields = ["sg_sequence"]
                seq = self.shotgun.find_one("Shot", filters=[["project", "is", ctx.project], ["code", "is", fields["Shot"]]], fields=pfields)
                if seq:
                    simpleName = seq["sg_sequence"]["name"]

                TempFileName=rrSetNewTempFileName(False)
                fileID=0
                fileID = file(TempFileName, "w")
                fileID.write("<RR_Job_File syntax_version=\"6.0\">\n")
                fileID.write("<DeleteXML>1</DeleteXML>\n")                



                rrWriteJobToFile(fileID, rootPath, path_on_disk, str(simpleName), str(fields["Shot"]), str(fields["version"]))
                fileID.write("</RR_Job_File>\n")
                
                
                fileID.close()

                #self.parent.log_debug("Executing command: %s" % finalCommand)
                RR_ROOT=rrGetRR_Root()
                if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):  
                    os.system("\""+RR_ROOT+"\\bin\\win\\rrSubmitterconsole.exe\" "+TempFileName)
                elif (sys.platform.lower() == "darwin"):
                    
                    os.system("\""+RR_ROOT+"/bin/mac/rrSubmitter.app/Contents/MacOS/rrSubmitter\" -darkui "+TempFileName)
                else:
                    
                    os.system("\""+RR_ROOT+"/lx__rrSubmitter.sh\" -darkui "+TempFileName)                
        self.engine.log_info("done")

