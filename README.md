# MyPLCNetwork

Contains the python scripts I use to save to monitor the bandwith in my PLC network.

## MyPLCNwtwork.py:
### Idea behind:

I have a PLC network at home to move data specially coming from my cameras, that I dont want to be send thru wifi (beacuse I'm old enough to think that if data can go thru wired it's allways better than thru wireless connections). And I want everything to be inside my HA, as usual.

[plc-utils](https://github.com/qca/open-plc-utils) is the key to monitor our PLCs (because remember they dont even have an ip!), but dont worry, you dont even need to open that webpage. Just in case you want to play, here you can find the binaris and all the code.

### HW and phisycal dependencies:

This script can not be run anywhere, it has some phisical restrictions. As I told you, PLC have no ip, so we need to talk to them thru the mac address. And that means that the computer where we are executing MyPLCNetwork needs to be phisically connected to the PLC (in case you run MyPLCNetwork in a virtual machine, the host needs to be connected to the PLC) ... but ... my host also needs to be connected to the router! I can not survive without internet access in HA! Lets use

![MyPLCNetwork](https://github.com/urri34/MyPLCNetwork/blob/main/Diagram.png)

### Execution parameters:

You can configure all the necessary things thru the ini file:
