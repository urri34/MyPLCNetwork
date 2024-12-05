# MyPLCNetwork

Contains the python scripts I use to save to monitor the bandwith in my PLC network.

## MyPLCNwtwork.py:
### Idea behind:

I have a PLC network at home to move data specially coming from my cameras, that I dont want to be send thru wifi (beacuse I'm old enough to think that if data can go thru wired it's allways better than thru wireless connections). And I want everything to be inside my HA, as usual.

[plc-utils](https://github.com/qca/open-plc-utils) is the key to monitor our PLCs (because remember they dont even have an ip!), but dont worry, you dont even need to open that webpage. Just in case you want to play, here you can find the binaris and all the code.

### HW and phisycal dependencies:

This script can not be run anywhere, it has some phisical restrictions. As I told you, PLC have no ip, so we need to talk to them thru the mac address. And that means that the computer where we are executing MyPLCNetwork needs to be phisically connected to the PLC (in case you run MyPLCNetwork in a virtual machine, the host needs to be connected to the PLC) ... but ... my host also needs to be connected to the router! I can not survive without internet access in HA! Lets be clever ...

![MyDevolo](https://github.com/urri34/MyPLCNetwork/blob/main/Devolo.jpg)

I'm using this devolo 550+ as may PLC stantdard. Why? Ther are not the last generation, and you can find plenty of them in second hand apps at a very nice prices (from 15€ each one). Bandwith is not the best, as in last generation PLC? absolutly, but for my cameras 550+ is enough. And if some day I want to change I will change every thing to wifi mesh solution. If you have a look at the bottom of the Devolo 550+ you will see 2 ethernet ports. Does are internally switched allways, nevermind if PLC status is linked to a PLC network, linking or factory defaulted.

So if I connect one ethernet coming from the router to on of those ports, and the acces to my HA to the other one ...I will have internet access in the HA thru the router, acces to LAN elements thru the router and access to LAN elements behind other PLCs thru the PLC.

![MyPLCNetwork](https://github.com/urri34/MyPLCNetwork/blob/main/Diagram.jpg)

This is the only diagram taht will work. MyPLCNetwork.py executed connected to a PLC.

### Execution parameters:

You can configure all the necessary things thru the ini file:
