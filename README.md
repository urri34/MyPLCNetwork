# MyPLCNetwork

Contains the python scripts I use to save to monitor the bandwith in my PLC network.

## MyPLCNwtwork.py:
### Idea behind:

I have a PLC network at home to move data specially coming from my cameras, that I dont want to be send thru wifi (beacuse I'm old enough to think that if data can go thru wired it's allways better than thru wireless connections). And I want everything to be inside my HA, as usual.

[plc-utils]([https://github.com/hass-agent/HASS.Agent](https://github.com/qca/open-plc-utils)) is the key to monitor our PLCs (because remember they dont even have an ip!), but dont worry, you dont even need to open that webpage.

### HW and phisycal dependencies:

This script can not be run anywhere, it has some phisical restrictions. 

### Execution parameters:

You can configure all the necessary things thru the ini file:
