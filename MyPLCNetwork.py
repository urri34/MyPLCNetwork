#!python.exe
# -*- coding: utf-8 -*-
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, getLogger, Formatter, FileHandler, StreamHandler
import subprocess
import configparser
from sys import _getframe
from os import path
from pathlib import Path
from re import sub
#from diagrams import Diagram, Edge
#from diagrams.aws.network import DirectConnect
#from diagrams.aws.compute import EC2

LogFile=path.join(path.dirname(path.realpath(__file__)), path.splitext(path.basename(__file__))[0]+'.log')
LogLevel=DEBUG #.DEBUG .INFO .WARNING .ERROR .CRITICAL

def AvailableNetworkInterfaces():
    DefName=_getframe( ).f_code.co_name
    CommandArguments=[IpPath, "a"]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=subprocess.run(CommandArguments, capture_output=True, text=True)
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

def LoadVarsFromIni():
    DefName=_getframe( ).f_code.co_name
    global Interface, IpPath, PlcStatPath, DNSs
    Config = configparser.ConfigParser()
    IniFile=path.splitext(path.basename(__file__))[0]+'.ini'
    if not path.isfile(IniFile):
        logger.critical(DefName+'(): No '+IniFile)
        exit(1)
    try:
        Config.read(IniFile)
    except:
        logger.critical(DefName+'(): Nota valid ini file '+IniFile)
        exit(1) 
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
    DNSs=[]
    DNSNumber=1
    while True:
        Mac=''
        Name=''
        Model=''
        Location=''
        if Config.has_option('DNS'+str(DNSNumber), 'mac'):
            Mac=Config.get('DNS'+str(DNSNumber), 'mac')
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
    logger.info(DefName+'(): Vars from ini loaded.')

def SetMyLogger():
    logger = getLogger()
    logger.setLevel(LogLevel)
    formatter = Formatter("[{asctime}] {levelname} {message}", style="{")

    file_handler = FileHandler(LogFile, mode="a", encoding="utf-8")
    file_handler.setLevel(LogLevel)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stderr_log_handler = StreamHandler()
    stderr_log_handler.setLevel(LogLevel)
    stderr_log_handler.setFormatter(formatter)       
    logger.addHandler(stderr_log_handler)
    return logger

def NameFromMac(MAC):
    for DNS in DNSs:
        if str(DNS['mac']).upper()==MAC:
            return DNS['name']
    return MAC

def AreaFromMac(MAC):
    for DNS in DNSs:
        if str(DNS['mac']).upper()==MAC:
            return DNS['location']
    return ''

def ModelFromMac(MAC):
    for DNS in DNSs:
        if str(DNS['mac']).upper()==MAC:
            return DNS['model']
    return 'Unkown'

def BuildConnectionsMatrixWithDNS(MyCCOMAC, Stations):
    Connections=[]
    for Station in Stations:
        MAC=Station[0]
        TX=Station[1]
        RX=Station[2]
        Connections.append([MACDNS(MyCCOMAC), MACDNS(MAC), TX, RX])
    return Connections

def DrawConnectionsWithDNS(MyCCOMAC, Connections):
    with Diagram("PLC-Flow-DNS-CCO", show=False):
        CentralNode = DirectConnect(MACDNS(MyCCOMAC))
        for Connection in Connections:
            CentralNode >> Edge(label=Connection[2]+'/'+Connection[3]) >> EC2(Connection[1])

def main():
    DefName=_getframe( ).f_code.co_name
    global logger
    logger = SetMyLogger()
    logger.debug(DefName+'(): Logging active for me: '+str(Path(__file__).stem))

    LoadVarsFromIni()
    CommandArguments=[PlcStatPath, "-t", '-i', Interface]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=subprocess.run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()
    if StdError != '':
        logger.debug(DefName+'(): StdError=\n'+str(StdError))
        exit(1)
    
    #P/L NET TEI ------ MAC ------ ------ BDA ------  TX  RX CHIPSET FIRMWARE
    #LOC CCO 004 30:D3:2D:5E:3E:85 08:00:27:92:46:68 n/a n/a QCA7420 MAC-QCA7420-1.1.1.1193-03-20140207-CS
    #REM STA 002 30:D3:2D:5E:3C:24 F6:A2:00:00:4F:02 218 263 QCA7420 MAC-QCA7420-1.1.1.1193-03-20140207-CS
    #REM STA 005 B8:BE:F4:7F:F0:5D B8:27:EB:AE:6C:3C 149 148 QCA7420 MAC-QCA7420-1.3.0.2134-00-20151212-CS

    logger.debug(DefName+'(): Loading elements from os ...')
    Elements=[]
    for Line in StdOut.splitlines():
        if 'P/L NET TEI ------ MAC ------ ------ BDA ------  TX  RX CHIPSET FIRMWARE' not in Line:
            Components=' '.join(Line.split()).split(' ')
            #logger.debug(DefName+'(): Components='+str(Components))
            Element={}
            Element['mac']=Components[3]
            Element['sensor_name']=sub(r'[^a-zA-Z0-9\s]', '', NameFromMac(Element['mac']))         
            Element['type']=Components[1]
            Element['friendly_name']=NameFromMac(Element['mac'])
            try:
                Element['sw_version']=Components[8]
            except:
                Element['sw_version']='Unknown'
            try:
                Element['hw_version']=Components[7]
            except:
                Element['hw_version']='Unknown'
            Element['suggested_area']=AreaFromMac(Element['mac'])
            Element['model']=ModelFromMac(Element['mac'])
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

    logger.debug(DefName+'(): Loading elements from config ...')
    for DNS in DNSs:
        DNSActive=False
        for Element in Elements:
            if str(DNS['mac']).upper() == Element['mac']:
                DNSActive=True
        if not DNSActive:
            Element={}
            Element['mac']=DNS['mac'].upper()
            Element['sensor_name']=sub(r'[^a-zA-Z0-9\s]', '', NameFromMac(Element['mac']))
            Element['type']='Unknown'
            Element['friendly_name']=NameFromMac(Element['mac'])
            Element['sw_version']='Unknown'
            Element['hw_version']='Unknown'
            Element['suggested_area']=AreaFromMac(Element['mac'])
            Element['model']=ModelFromMac(Element['mac'])
            Element['tx']=0
            Element['rx']=0
            Element['status']='off'
            logger.debug(DefName+'(): Element from DNS='+str(Element))
            Elements.append(Element)

    """
        payload={"unique_id": Element['sensor_name'],
            "name": Element['friendly_name'],
            "state_topic": "home/PLC/"+Element['sensor_name'],
            "command_topic": "home/bedroom/bedroom_socket_switch/set",
            "availability_topic":"home/bedroom/bedroom_socket_switch/available",
            "payload_on": "ON",
            "payload_off": "OFF",
            "state_on": "ON",
            "state_off": "OFF",
            "optimistic": False,
            "qos": 0,
            "retain": True
        }
        payload=json.dumps(payload) #convert to JSON


    # Create the JSON payload for MQTT Discovery configuration
    json_payload=$(jq -n --arg sensor_name "$sensor_name" --arg status "$status" --arg type "$type" --arg friendly_name "$friendly_name" \
       '{"name": "Devolo '$friendly_name'",
         "state_topic": "homeassistant/sensor/'$sensor_name'/state",
         "unique_id": "'$sensor_name'",
         "device": {"identifiers": ["'$mac'"],
                    "name": "'$friendly_name'",
                    "model": "dLAN 550 duo+",
                    "manufacturer": "Devolo"
                   },
         "json_attributes_topic": "homeassistant/sensor/'$sensor_name'/attributes",
         "json_attributes_template": "{{ value_json.data.value | tojson }}"
       }')

    # Publish the MQTT Discovery configuration to the appropriate topic
    mosquitto_pub -h localhost -u $mqtt_username -P $mqtt_password -t homeassistant/sensor/$sensor_name/config -m "$json_payload"

    # Publish the sensor state to the MQTT state topic
    mosquitto_pub -h localhost -u $mqtt_username -P $mqtt_password -t homeassistant/sensor/$sensor_name/state -m "$status"

    # Publish the sensor attributes to the MQTT attribute topic
    json_attribute="{ \"mac\": \"$mac\", \"type\": \"$type\""

    # Check if tx is a numeric value
    if [[ $tx =~ ^[0-9]+$ ]]; then
        json_attribute="$json_attribute, \"tx\": $tx"
    fi

    # Check if rx is a numeric value
    if [[ $rx =~ ^[0-9]+$ ]]; then
        json_attribute="$json_attribute, \"rx\": $rx"
    fi

    json_attribute="$json_attribute }"
    mosquitto_pub -h localhost -u $mqtt_username -P $mqtt_password -t homeassistant/sensor/$sensor_name/attributes -m "$json_attribute"
    """

if __name__ == '__main__':
    main()
