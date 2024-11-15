#!python.exe
# -*- coding: utf-8 -*-
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, getLogger, Formatter, FileHandler, StreamHandler
import subprocess
import configparser
from sys import _getframe
from os import path
from pathlib import Path
from diagrams import Diagram, Edge
from diagrams.aws.network import DirectConnect
from diagrams.aws.compute import EC2

LogFile=path.join(path.dirname(path.realpath(__file__)), path.splitext(path.basename(__file__))[0]+'.log')
LogLevel=DEBUG #.DEBUG .INFO .WARNING .ERROR .CRITICAL

def LoadVarsFromIni():
    DefName=_getframe( ).f_code.co_name
    global IpPath, Int6kPath, DNSs
    Config = configparser.ConfigParser()
    IniFile=path.splitext(path.basename(__file__))[0]+'.ini'
    Config.read(IniFile)

    if Config.has_section('Constants'):
        if Config.has_option('Constants', 'ip'):
            IpPath=Config.get('Constants', 'ip')
            logger.debug(DefName+'(): IpPath='+str(IpPath))
        else:
            logger.critical(DefName+'(): No IpPath set in '+IniFile)
            exit(1)
        if Config.has_option('Constants', 'int6k'):
            Int6kPath=Config.get('Constants', 'int6k')
            logger.debug(DefName+'(): Int6kPath='+str(Int6kPath))
        else:
            logger.critical(DefName+'(): No Int6kPath set in '+IniFile)
            exit(1)

        DNSs=[]
        DNSNumber=1
        while True:
            Mac=''
            Name=''
            if Config.has_option('DNS'+str(DNSNumber), 'mac'):
                Mac=Config.get('DNS'+str(DNSNumber), 'mac')
                logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].mac='+str(Mac))
                if Config.has_option('DNS'+str(DNSNumber), 'name'):
                    Name=Config.get('DNS'+str(DNSNumber), 'name')
                    logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].name='+str(Name))
                    DNS={}
                    DNS['mac']=Mac
                    DNS['name']=Name
                    DNSs.append(DNS)
                else:
                    logger.debug(DefName+'(): [DNS'+str(DNSNumber)+'].name not set')
                DNSNumber=DNSNumber+1
            else:
                break
    else:
        logger.critical(DefName+'(): No '+path.splitext(path.basename(__file__))[0]+'.ini')
        exit(1)

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

    logger.info(DefName+'(): Looking for interfaces ...')
    Interfaces=[]
    InterfaceName=''
    InterfaceMac=''
    for Line in StdOut.splitlines():
        #logger.debug(DefName+'(): Line='+str(Line))
        if 'mtu' in Line:
            if InterfaceName != '':
                Interfaces.append([InterfaceName, InterfaceMac])
                InterfaceName=''
                InterfaceMac=''
            InterfaceName=Line.split(' ')[1].replace(':','')
            logger.debug(DefName+'(): interface detected '+InterfaceName)
        if 'link/ether' in Line:
            InterfaceMac=' '.join(Line.split()).split(' ')[1]
            logger.debug(DefName+'(): mac detected '+InterfaceMac+' for '+InterfaceName)
            
    if InterfaceName != '':
        Interfaces.append([InterfaceName, InterfaceMac])
    logger.debug(DefName+'(): Interfaces='+str(Interfaces))
    return Interfaces

def WhereAmIconnectedTo(SelectedInterface):
    DefName=_getframe( ).f_code.co_name
    
    CommandArguments=[Int6kPath, "-r", '-i', SelectedInterface[0]]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=subprocess.run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()
    StdError=CommandExecution.stderr.strip()

    logger.info(DefName+'(): Looking network ...')
    Network=str(StdError).split(' ')[1]
    logger.debug(DefName+'(): Network='+str(Network))

    logger.info(DefName+'(): Looking CCO ...')
    CCO=str(StdOut).split(' ')[1] 
    logger.debug(DefName+'(): CCO='+str(CCO))
    
    return Network, CCO

def FindTheStations(SelectedInterface):
    DefName=_getframe( ).f_code.co_name
    
    CommandArguments=[Int6kPath, "-m", '-i', SelectedInterface[0]]
    logger.debug(DefName+'(): CommandArguments='+str(CommandArguments))
    CommandExecution=subprocess.run(CommandArguments, capture_output=True, text=True)
    StdOut=CommandExecution.stdout.strip()

    Stations=[]
    logger.info(DefName+'(): Looking for stations ...')
    for Line in StdOut.splitlines():
        if 'station->MAC' in Line:
            MAC=' '.join(Line.split()).split(' ')[2]
            logger.debug(DefName+'(): MAC='+str(MAC))
        if 'station->AvgPHYDR_TX' in Line:
            TX=' '.join(Line.split()).split(' ')[2]+' '.join(Line.split()).split(' ')[3]
            if TX[0]=='0':
                TX=TX[1:]
            logger.debug(DefName+'(): TX='+str(TX))
        if 'station->AvgPHYDR_RX' in Line:
            RX=' '.join(Line.split()).split(' ')[2]+' '.join(Line.split()).split(' ')[3]
            if RX[0]=='0':
                RX=RX[1:]
            logger.debug(DefName+'(): RX='+str(RX))
            Stations.append([MAC, TX, RX])
    return Stations

def MACDNS(MAC):
    DefName=_getframe( ).f_code.co_name
    for DNS in DNSs:
        if DNS['mac']==MAC:
            return DNS['name']
    return MAC

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

def BuildConnectionsMatrix(MyCCOMAC, Stations):
    Connections=[]
    for Station in Stations:
        MAC=Station[0]
        TX=Station[1]
        RX=Station[2]
        Connections.append([MyCCOMAC, MAC, TX, RX])
    return Connections

def DrawConnections(MyCCOMAC, Connections):
    with Diagram("PLC-Flow-CCO", show=False):
        CentralNode = DirectConnect(MyCCOMAC)
        for Connection in Connections:
            CentralNode >> Edge(label=Connection[2]+'/'+Connection[3]) >> EC2(Connection[1])

def main():
    DefName=_getframe( ).f_code.co_name
    global logger
    logger = SetMyLogger()
    logger.debug(DefName+'(): Logging active for me: '+str(Path(__file__).stem))

    LoadVarsFromIni()
    NetWorkInterfaces = AvailableNetworkInterfaces()
    SelectedInterface = NetWorkInterfaces[1]
    MyNetwork, MyCCOMAC = WhereAmIconnectedTo(SelectedInterface)
    Stations=FindTheStations(SelectedInterface)
    Connections=BuildConnectionsMatrixWithDNS(MyCCOMAC, Stations)
    DrawConnectionsWithDNS(MyCCOMAC, Connections)
    Connections=BuildConnectionsMatrix(MyCCOMAC, Stations)
    DrawConnections(MyCCOMAC, Connections)

if __name__ == '__main__':
    main()
