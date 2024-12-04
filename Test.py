import json
from paho.mqtt import client as mqtt_client
from time import sleep

Broker = '100.124.79.67'
Port = 1883
ClientId = f'python-mqtt'
UserName = 'mosquito'
Password = 'mosquito'

Element={ 'mac': '30:D3:2D:5E:3E:85',
    'sensor_name': 'PLCSaleta',
    'type': 'CCO',
    'friendly_name': 'PLC_Saleta',
    'sw_version': 'MAC-QCA7420-1.1.1.1193-03-20140207-CS',
    'hw_version': 'QCA7420',
    'suggested_area': 'sala_d_estar',
    'model': 'Devolo550p',
    'tx': 0,
    'rx': 0,
    'status': 'on'}

payload={
  "ldevice": {
    "identifiers": str(Element['sensor_name']),
    "name": str(Element['friendly_name']),
    "model": str(Element['model']),
    "sw_version": str(Element['sw_version']),
    "serial_number": str(Element['mac']).replace(':',''),
    "hw_version": str(Element['hw_version'])
  },
  "origin": {
    "name":"plcstat",
    "sw_version": "0.0.6",
    "support_url": "https://github.com/urri34/MyPLCNetwork"
  },
  "components": {
    str(Element['sensor_name'])+'_tx': {
      "platform": "sensor",
      "device_class":"data_rate",
      "unit_of_measurement":"MB/s,",
      "value_template":str(Element['tx']),
      "unique_id":str(Element['sensor_name'])+'_tx_id'
    },
    str(Element['sensor_name'])+'_rx': {
      "platform": "sensor",
      "device_class":"data_rate",
      "unit_of_measurement":"MB/s,",
      "value_template":"{{ value_json.humidity}}",
      "unique_id":str(Element['sensor_name'])+'_rx_id'
    }
  },
  "state_topic":"homeassistant/sensor/"+str(Element['sensor_name'])+"/config",
  "qos": 2,
}

Topic='homeassistant/sensor/'+str(Element['sensor_name'])+'/config'

def ConnectMqtt() -> mqtt_client:
  def OnConnect(client, userdata, flags, rc):
    print('Succesfully connected to Mqtt broker')

  def OnDisconnect(client, userdata, rc):
    print('Disconnecting from Mqtt broker')

  client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, ClientId)
  client.username_pw_set(UserName, Password)
  client.on_connect = OnConnect
  client.connect(Broker, Port, keepalive=120)
  client.on_disconnect = OnDisconnect
  return client

def Publish(client, MessageDict):
  print('Dictionary='+str(MessageDict))
  Message = json.dumps(MessageDict)
  result = client.publish(Topic, Message)
  status = result[0]
  if status == 0:
    print('Send '+str(Message)+' to topic {'+str(Topic)+'}')
    return 0
  else:
    print('Failed to send message to topic {'+str(Topic)+'}')
    return 1

def PrepareConnection():
  client = ConnectMqtt()
  client.loop_start()
  sleep(1)
  return client

def CloseConnection(client):
  client.loop_stop()
  client.disconnect()

client = PrepareConnection()

if client.is_connected():
  Publish(client, payload)
else:
  print('client not connected')
CloseConnection(client)
