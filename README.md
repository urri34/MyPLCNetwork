# MyPLCNetwork

Contains the python scripts I use to save to monitor the bandwidth in my PLC network. This is tha base of my addon plc_network.

It reads info from the PLC network and sends it to MQTT broker which auto generates devices in HA. That easy!

## MyPLCNetwork.py:
### Idea behind:

I have a PLC network at home to move data specially coming from my cameras to my recording server, that I don’t want to be send thru Wi-Fi (because I'm old enough to know that if data can go thru wired it's always better than thru wireless connections). And I want everything to be inside my HA, as usual.

[plc-utils](https://github.com/qca/open-plc-utils) is the key to monitor our PLCs (because remember they don’t even have an ip!), but don’t worry, you don’t even need to open that webpage. Just in case you want to play, here you can find the binaries and all the code. If you have a Debian or derived you can find all you need in plc-utils package in your favorite repository.

### HW and physical dependencies:

**This script cannot be run anywhere, it has some <ins>physical</ins> restrictions**. As I told you, PLC have no ip, so we need to talk to them thru the mac address. And that means that the computer where we are executing MyPLCNetwork.py needs to be physically connected to the PLC (in case you run MyPLCNetwork in a virtual machine, the host needs to be connected to the PLC). You can put a little raspberry connected to a PLC and run MyPLCNetwork.py there as it will send the data through MQTT.

I use it in order to know the bandwidth between cameras and the recording server (which is the machine that hosts the HA VM). So take it in consideration, this will measure bandwidth between PLCs and the place where you execute MyPLCNetwork.py

In my case (worst case) I also want this someday to become a HA Addon, so I want MyPLCNetwork to run in my HA machine ... but ... my HA also needs to be connected to the router! And to the LAN! I cannot survive without internet access in HA! Let’s be clever ...

<p align="center">
  <img src="https://github.com/urri34/MyPLCNetwork/blob/main/Devolo.jpg" />
</p>

I'm using this devolo 550+ as my PLC standard. Why? Ther are not the last generation, and you can find plenty of them in secondhand apps at very nice prices (from 15€ each one). Bandwith is not the best, as in the last generation PLC? absolutely, but for my cameras 550+ is enough. And if someday I want to change, I will change everything to Wi-Fi mesh solution where the nodes have also ethernet ports and the Wi-Fi is extremely stable. If you have a look at the bottom of the Devolo 550+ you will see 2 ethernet ports. Does are internally switched always, never mind if PLC status is linked to a PLC network, linking or factory defaulted.

So, if I connect one ethernet coming from the router to one of those ports, and the access to my HA to the other one ... I will have internet access in the HA thru the router, access to LAN elements (Wi-Fi or wired) thru the router and access to LAN elements behind other PLCs thru the PLC.

<p align="center">
  <img src="https://github.com/urri34/MyPLCNetwork/blob/main/Diagram.jpg" />
</p>

This is the only diagram that will work. MyPLCNetwork.py executed connected to a PLC.

### Execution parameters:

You can configure all the necessary things through the ini file:

```
[Constants]
interface=enp0s3
ip=/usr/bin/ip
plcstat=/usr/bin/plcstat
broker=192.168.1.1
port=1883
username=mosquitouser
password=mosquitopass

[DNS1]
mac=00:00:00:00:00:01
name=PLC_Test1

[DNS2]
mac=00:00:00:00:00:02
name=PLC_Test2

(...)
```

Let’s have a look at the parameter:

- interface: You need to know thru what interface is the OS seeing the PLC. enp0s3, eth0 or eth1 use to be the most common ones but ... 'ip a' this command can help you to find it.
- ip: path of the ip binary file. /usr/bin/ip is the place for Debian but ... 'whereis ip' this command can help you to find it.
- plcstat: Path of the plcstat binary file. /usr/bin/plcstat is the place for Debian but ... 'whereis plcstat' this command can help you to find it.
- broker: Ip address or FQDN of the MQTT server
- port: Port of the MQTT server (1883 is the standard)
- username: Username to login the MQTT server
- password: Password to login the MQTT server

As many times as you need, just taking in consideration that the numbers need to be correlative like DNS1, DNS2, DNS3 ...

- mac: Mac address for a PLC. You can find it in a sticker behind the hardware.
- name: Nice name for that PLC, mac address are ugly. I like to use PLC_location as a name which is nice :grin:

### HA Side:

If everything is ok PLC devices will appear in you HA. How many PLCs? You think the answer is as much PLC I have powered on and connected to my PLC network? No. One device for each PLC connected and alive, but also one device for each PLC listed in the ini file (and not alive in the network). For each PLC, 3 sensors will appear:

- tx: Real time transmission bandwidth between the PLC behind the device **and the PLC where is physically connected the MyPLCNetwork.py**
- rx: Real time reception bandwidth between the PLC behind the device **and the PLC where is physically connected the MyPLCNetwork.py**
- role: This can take 3 values: Unknown, CCO and STA. Unknown is given to an stopped PLC. CCO means that PLC is the boss of the PLC Network. If a CCO PLC is stopped, it's role moves to another one. I will use this in later versions in order to draw the network, but today for 99,99% of the population it has absolutely no influence.
