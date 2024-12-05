#!python.exe
# -*- coding: utf-8 -*-
from configparser import ConfigParser
from diagrams import Diagram, Edge, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB
from json import dumps
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from os import path
from pathlib import Path
from re import sub
from subprocess import run
from sys import _getframe
from time import sleep
import paho.mqtt.client as mqtt

LogFile=path.join(path.dirname(path.realpath(__file__)), path.splitext(path.basename(__file__))[0]+'.log')
LogLevel=DEBUG #.DEBUG .INFO .WARNING .ERROR .CRITICAL
CLEAN_SESSION=True
MainSleep=60
QOS=0

def AvailableNetworkInterfaces():
    DefName=_getframe( ).f_code.co_name
    CommandArguments=[IpPath, "a"]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()
    if StdError != '':
        logger.debug(DefName+'(): StdError=\n'+str(StdError))
        exit(1)
    logger.debug(DefName+'(): Looking for interfaces ...')
    Interfaces=[]
    InterfaceName=''

    for Line in StdOut.splitlines():
        #logger.debug(DefName+'(): Line='+str(Line))
        if 'mtu' in Line:
            if InterfaceName != '':
                Interfaces.append(InterfaceName)
                InterfaceName=''
            InterfaceName=Line.split(' ')[1].replace(':','')
            #logger.debug(DefName+'(): interface detected '+InterfaceName)
            
    if InterfaceName != '':
        Interfaces.append(InterfaceName)
    logger.debug(DefName+'(): Interfaces='+str(Interfaces))
    return Interfaces

def DrawConnections(Elements):
    DefName=_getframe( ).f_code.co_name
    with Diagram("PLC-Flow-DNS-CCO", show=False):
        #CCO CentralNode drawed as ELB
        CentralNode=''
        for Element in Elements:
            if Element['type']=='CCO':
                CentralNode = ELB(Element['sensor_name'])
                logger.debug(DefName+'(): Setting '+Element['sensor_name']+' as central node.')
        if CentralNode=='':
            logger.critical(DefName+'(): No central node.')
            exit(1)

        StoppedNodeCount=0
        with Cluster("Sttoped"):
            for Element in Elements:
                if Element['type']!='CCO':
                    if Element['status']=='off':
                        globals()['StoppedNode'+str(StoppedNodeCount)]=EC2(Element['sensor_name'])
                        logger.debug(DefName+'(): Setting StoppedNode'+str(StoppedNodeCount)+' with '+Element['sensor_name']+' as normal node inside Sttoped nodes.')
                        StoppedNodeCount+=1

        if StoppedNodeCount != 0:
            StoppedNodeCount-=1
            while StoppedNodeCount >= 0:
                CentralNode >> globals()['StoppedNode'+str(StoppedNodeCount)]
                logger.debug(DefName+'(): Drawing line beteween CentralNode and StoppedNode'+str(StoppedNodeCount))
                StoppedNodeCount-=1

        for Element in Elements:
            if Element['type']!='CCO':
                if Element['status']=='on':
                    CentralNode >> Edge(label=str(Element['tx'])+'/'+str(Element['rx'])) >> EC2(Element['sensor_name'])

def GetElementsFromConfig(Elements):
    DefName=_getframe( ).f_code.co_name
    for DNS in DNSs:
        DNSActive=False
        for Element in Elements:
            if DNS['mac'] == Element['mac']:
                DNSActive=True
        if not DNSActive:
            Element={}
            Element['mac']=DNS['mac']
            Element['sensor_name']=NameFromMac(Element['mac'])
            Element['role']='Unknown'
            Element['sw_version']='Unknown'
            Element['hw_version']='Unknown'
            Element['tx']=0
            Element['rx']=0
            Element['status']='off'
            logger.debug(DefName+'(): Element from DNS='+str(Element))
            Elements.append(Element)
    return Elements

def GetElementsFromPLCStats(InforFromPLCStat):
    DefName=_getframe( ).f_code.co_name
    Elements=[]
    for Line in InforFromPLCStat.splitlines():
        if 'P/L NET TEI ------ MAC ------ ------ BDA ------  TX  RX CHIPSET FIRMWARE' not in Line:
            Components=' '.join(Line.split()).split(' ')
            #logger.debug(DefName+'(): Components='+str(Components))
            Element={}
            Element['mac']=Components[3]
            Element['sensor_name']=NameFromMac(Element['mac'])    
            Element['role']=Components[1]
            try:
                Element['sw_version']=Components[8]
            except:
                Element['sw_version']='Unknown'
            try:
                Element['hw_version']=Components[7]
            except:
                Element['hw_version']='Unknown'
            if Components[5] == 'n/a':
                Element['tx']=0
            else:
                Element['tx']=int(Components[5])
            if Components[6] == 'n/a':
                Element['rx']=0
            else:
                Element['rx']=int(Components[6])
            if Element['sw_version']=='Unknown' and Element['hw_version']=='Unknown':
                Element['status']='off'   
            else:
                Element['status']='on'   
            logger.debug(DefName+'(): Element from OS='+str(Element))
            Elements.append(Element)
    return Elements

def GetInfoFromPLCStat():
    DefName=_getframe( ).f_code.co_name
    CommandArguments=[PlcStatPath, "-t", '-i', Interface]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()
    if StdError != '':
        logger.debug(DefName+'(): StdError=\n'+str(StdError))
        exit(1)
    return StdOut

def GetPayLoadData(Element):
    PayLoadData={
        "rx":int(Element['rx']),
        "tx":int(Element['rx']),
        "role":Element['role']
    }
    return PayLoadData

def GetPayLoadDeviceAndTx(Element):
    DefName=_getframe( ).f_code.co_name
    PayLoadDeviceAndTx={
        "name": "Tx",
        "device_class":"data_rate",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "unit_of_measurement":"MB/s",
        "value_template":"{{ value_json.tx }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_tx",
        "icon": "mdi:transmission-tower-import",
        "device":{
            "identifiers": [ "PLC_"+str(Element['mac']).replace(':','') ],
            "name": Element['sensor_name'],
            "serial_number": str(Element['mac']).replace(':',''),
            "hw_version": Element['hw_version'],
            "sw_version": Element['sw_version'],
            "configuration_url": "https://github.com/urri34/MyPLCNetwork",
            "manufacturer": "plcstat",
            "model": "MyPLCNetwork"
        }
    }
    return PayLoadDeviceAndTx

def GetPayLoadRole(Element):
    PayLoadRole={
        "name": "Role",
        "device_class":"enum",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "value_template":"{{ value_json.role }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_role",
        "options": ["CCO", "STA", "Unknown"],
        "device":{
            "identifiers":[ "PLC_"+str(Element['mac']).replace(':','') ]
        }
    }
    return PayLoadRole

def GetPayLoadRx(Element):
    DefName=_getframe( ).f_code.co_name
    PayLoadRx={
        "name": "Rx",
        "device_class":"data_rate",
        "state_topic":"homeassistant/sensor/"+Element['sensor_name']+"/state",
        "unit_of_measurement":"MB/s",
        "value_template":"{{ value_json.rx }}",
        "unique_id": "PLC_"+str(Element['mac']).replace(':','')+"_rx",
        "icon": "mdi:transmission-tower-export",
        "device":{
            "identifiers":[ "PLC_"+str(Element['mac']).replace(':','') ]
        }
    }
    return PayLoadRx

def LoadVarsFromIni():
    DefName=_getframe( ).f_code.co_name
    global Interface, IpPath, PlcStatPath, DNSs, Broker, Port, UserName, Password
    Config = ConfigParser()

    IniFile=path.splitext(path.basename(__file__))[0]+'.ini'
    if not path.isfile(IniFile):
        logger.critical(DefName+'(): No '+IniFile)
        exit(1)
    try:
        Config.read(IniFile)
    except:
        logger.critical(DefName+'(): Not a valid ini file '+IniFile)
        exit(1)
    #IP
    if Config.has_option('Constants', 'ip'):
        IpPath=Config.get('Constants', 'ip')
    else:
        logger.critical(DefName+'(): No IpPath set in '+IniFile)
        exit(1)
    if not path.isfile(IpPath):
        logger.critical(DefName+'(): Configured IpPath is not valid')
        exit(1)
    else:
        logger.debug(DefName+'(): IpPath='+str(IpPath))
    #Interface
    if Config.has_option('Constants', 'interface'):
        Interface=Config.get('Constants', 'interface')
    else:
        logger.critical(DefName+'(): No Interface set in '+IniFile)
        exit(1)
    Interfaces=AvailableNetworkInterfaces()
    if Interface not in Interfaces:
        logger.critical(DefName+'(): Configured interface '+str(Interface)+' is not valid '+str(Interfaces))
        exit(1)
    else:
        logger.debug(DefName+'(): Interface='+str(Interface))
    #PlcStat
    if Config.has_option('Constants', 'plcstat'):
        PlcStatPath=Config.get('Constants', 'plcstat')
    else:
        logger.critical(DefName+'(): No plcstat set in '+IniFile)
        exit(1)
    if not path.isfile(PlcStatPath):
        logger.critical(DefName+'(): Configured plcstat is not valid')
        exit(1)
    else:
        logger.debug(DefName+'(): PlcStatPath='+str(PlcStatPath))
    #Broker
    if Config.has_option('Constants', 'broker'):
        Broker=Config.get('Constants', 'broker')
        logger.debug(DefName+'(): Broker='+str(Broker))
    else:
        logger.critical(DefName+'(): No broker set in '+IniFile)
        exit(1)
    #Port
    if Config.has_option('Constants', 'port'):
        Port=Config.get('Constants', 'port')
    else:
        logger.critical(DefName+'(): No port set in '+IniFile)
        exit(1)
    try:
        Port=int(Port)
        logger.debug(DefName+'(): Port='+str(Port))
    except:
        logger.critical(DefName+'(): Configured port is not valid')
        exit(1)        
    #UserName
    if Config.has_option('Constants', 'username'):
        UserName=Config.get('Constants', 'username')
        logger.debug(DefName+'(): UserName='+str(UserName))
    else:
        logger.critical(DefName+'(): No username set in '+IniFile)
        exit(1)
    #Password
    if Config.has_option('Constants', 'password'):
        Password=Config.get('Constants', 'password')
        logger.debug(DefName+'(): Password='+str(Password))
    else:
        logger.critical(DefName+'(): No password set in '+IniFile)
        exit(1)
    DNSs=[]
    DNSNumber=1
    while True:
        Mac=''
        Name=''
        Model=''
        Location=''
        if Config.has_option('DNS'+str(DNSNumber), 'mac'):
            Mac=Config.get('DNS'+str(DNSNumber), 'mac').upper()
            #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].mac='+str(Mac))
            if Config.has_option('DNS'+str(DNSNumber), 'name'):
                Name=Config.get('DNS'+str(DNSNumber), 'name')
            else:
                Name='Unknown'
                #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].name not set')
            #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].name='+str(Name))
            if Config.has_option('DNS'+str(DNSNumber), 'model'):
                Model=Config.get('DNS'+str(DNSNumber), 'model')
            else:
                Model='Unknown'
                #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].model not set')
            #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].model='+str(Model))

            if Config.has_option('DNS'+str(DNSNumber), 'location'):
                Location=Config.get('DNS'+str(DNSNumber), 'location')
            else:
                Location=''
                #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].location not set')
            #logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].location='+str(Location))
            DNS={}
            DNS['mac']=Mac
            DNS['name']=Name
            DNS['model']=Model
            DNS['location']=Location
            logger.debug(DefName+'(): DNS='+str(DNS))
            DNSs.append(DNS)
            DNSNumber=DNSNumber+1
        else:
            break

def NameFromMac(MAC):
    for DNS in DNSs:
        if DNS['mac']==MAC:
            return sub(r'[^a-zA-Z0-9\-_]', '', DNS['name'])
    return MAC

def SendPayLoadToMQTTTopic(PayLoad, Topic, client):
    DefName=_getframe( ).f_code.co_name
    logger.debug(DefName+'(): PayLoad='+dumps(PayLoad, indent=1))
    logger.debug(DefName+'(): Topic='+str(Topic))
    logger.debug(DefName+'(): Return:'+str(client.publish(Topic,
                                    dumps(PayLoad),
                                    QOS)))

def SetMyLogger():
    from logging import getLogger, Formatter, StreamHandler
    from logging.handlers import RotatingFileHandler

    logger = getLogger()
    logger.setLevel(LogLevel)
    LogFormat = ('[%(asctime)s] %(levelname)-4s %(message)s')
    formatter = Formatter(LogFormat)

    file_handler = RotatingFileHandler(LogFile, mode="a", encoding="utf-8", maxBytes=1*1024*1024, backupCount=2)
    file_handler.setLevel(LogLevel)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stdout_handler = StreamHandler()
    stdout_handler.setLevel(LogLevel)
    stdout_handler.setFormatter(formatter)       
    logger.addHandler(stdout_handler)

    return logger

def main():
    DefName=_getframe( ).f_code.co_name
    global logger
    logger = SetMyLogger()
    logger.debug(DefName+'(): Logging active for me: '+str(Path(__file__).stem))

    logger.info(DefName+'(): Loading vars from ini file ...')
    LoadVarsFromIni()
    
    logger.info(DefName+'(): Connecting to MQTT ...')
    #client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "python-mqtt", clean_session=CLEAN_SESSION)
    client = mqtt.Client("python-mqtt", clean_session=CLEAN_SESSION)
    client.username_pw_set(UserName, Password)
    client.connect(Broker, Port)
    client.loop_start()
    
    while True:
        InforFromPLCStat=GetInfoFromPLCStat()
        logger.info(DefName+'(): Loading elements from plcstat ...')
        Elements=GetElementsFromPLCStats(InforFromPLCStat)

        logger.info(DefName+'(): Loading elements from config ...')
        Elements=GetElementsFromConfig(Elements)

        #logger.info(DefName+'(): Drawing connections ...')
        #DrawConnections(Elements)

        for Element in Elements:
            if False:
                PayLoadDeviceAndTx=GetPayLoadDeviceAndTx(Element)
                Topic="homeassistant/sensor/"+Element['sensor_name']+"/tx/config"
                SendPayLoadToMQTTTopic(PayLoadDeviceAndTx, Topic, client)
                del(PayLoadDeviceAndTx)

                PayLoadRx=GetPayLoadRx(Element)
                Topic="homeassistant/sensor/"+Element['sensor_name']+"/rx/config"
                SendPayLoadToMQTTTopic(PayLoadRx, Topic, client)
                del(PayLoadRx)

                PayLoadRole=GetPayLoadRole(Element)
                Topic="homeassistant/sensor/"+Element['sensor_name']+"/role/config"
                SendPayLoadToMQTTTopic(PayLoadRole, Topic, client)
                del(PayLoadRole)
            else:
                PayLoadData=GetPayLoadData(Element)
                Topic="homeassistant/sensor/"+Element['sensor_name']+"/state"
                SendPayLoadToMQTTTopic(PayLoadData, Topic, client)
                del(PayLoadData)

        sleep(MainSleep)
        
if __name__ == '__main__':
    main()
