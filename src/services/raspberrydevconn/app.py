import io
import logging
import cherrypy
import paho.mqtt.client as mqtt

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *
from common.WIOThread import WIOThread

class RaspberryDevConnAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._th = WIOThread(target=self._airhumidity, name="Air Humidity Thread")
        self._th1 = WIOThread(target=self._airtemperature, name="Air Temperature Thread")
        self._th2 = WIOThread(target=self._terrainhumidity, name="Terrain Humidity Thread")
        upperRESTSrvcApp.subsribe_evt_stop(self._th.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th1.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th2.stop)
        f = open("../deviceconfig/confs.json")
        data = json.load(f)
        self.wait_temp_hum = data["sensors"]["temp"]["sampleperiod"] / 1000
        self.logger.debug(self.wait_temp_hum)
        self.wait_air_hum = data["sensors"]["airhum"]["sampleperiod"] / 1000
        self.logger.debug(self.wait_temp_hum)
        self.wait_soil_hum = data["sensors"]["soilhum"]["sampleperiod"] / 1000
        self.logger.debug(self.wait_temp_hum)
        self._th.run()
        self._th1.run()
        self._th2.run()
        with open(SettingsManager.relfile2abs("../deviceconfig/confs.json")) as fp:
                keys = self._rec_dict(json.load(fp))
                for k in keys:
                    self._catreq.subscribeMQTT("DeviceConfig", f"/conf{k}")
                    if (f"/conf{k}" == "/conf/sensors/temp/sampleperiod"):
                        self._catreq.callbackOnTopic("DeviceConfig", f"/conf{k}", self.onMessageReceiveTemp)
                    elif (f"/conf{k}" == "/conf/sensors/airhum/sampleperiod"):
                        self._catreq.callbackOnTopic("DeviceConfig", f"/conf{k}", self.onMessageReceiveAirhum)
                    elif (f"/conf{k}" == "/conf/sensors/soilhum/sampleperiod"):
                        self._catreq.callbackOnTopic("DeviceConfig", f"/conf{k}", self.onMessageReceiveSoilhum)
        
    def _airhumidity(self):
        while not self._th.is_stop_requested:
            self._th.wait(self.wait_air_hum)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/airhumidity", "airhumiditypayload")
    
    def _airtemperature(self):
        while not self._th.is_stop_requested:
            self._th1.wait(self.wait_temp_hum)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/airtemperature", "airtemperaturepayload")
        
    def _terrainhumidity(self):
        while not self._th.is_stop_requested:
            self._th.wait(self.wait_soil_hum)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/terrainhumidity", "terrainhumiditypayload")

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("Raspberry Device Connector Endpoint")
        elif path[0] == "airhumidity":
            return self.asjson("airhumidityvalue")
        elif path[0] == "airtemperature":
            return self.asjson("airtemperature")
        elif path[0] == "terrainhumidity":
            return self.asjson("terrainhumidity")
        return self.asjson("error")
    
    def onMessageReceiveTemp(self, paho_mqtt , userdata, msg:mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string)
        self.wait_temp_hum = json_string["v"] / 1000
        self.logger.debug(self.wait_temp_hum)
        self._th1.stop()
        self._th1.run()
    
    def onMessageReceiveAirhum(self, paho_mqtt , userdata, msg:mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string) / 1000
        self.wait_air_hum = json_string["v"] / 1000
        self.logger.debug(self.wait_air_hum)
        self._th.stop()
        self._th.run()

    
    def onMessageReceiveSoilhum(self, paho_mqtt , userdata, msg:mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string)
        self.wait_soil_hum = json_string["v"] / 1000
        self.logger.debug(self.wait_soil_hum)
        self._th2.stop()
        self._th2.run()
    
    def _rec_dict(self, d: dict, path: str = "") -> list[str]:
        ret = []
        for k, v in d.items():

            p = f"{path}/{k}"
            if isinstance(v, dict):
                ret = [*ret, *self._rec_dict(v, p)]
            else:
                ret.append(p)
            
        return ret

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "RaspberryDevConn", ServiceType.DEVICE, ServiceSubType.RASPBERRY)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/airhumidity", [EndpointParam("state")], endpointTypeSub=EndpointTypeSub.RESOURCE)
            self.addRESTEndpoint("/airtemperature", [EndpointParam("state")], endpointTypeSub=EndpointTypeSub.RESOURCE)
            self.addRESTEndpoint("/terrainhumidity", [EndpointParam("state")], endpointTypeSub=EndpointTypeSub.RESOURCE)
            self.addMQTTEndpoint("/airhumidity", "data of the air humidity from the DHT11")
            self.addMQTTEndpoint("/airtemperature", "data of the air temperature from the DHT11")
            self.addMQTTEndpoint("/terrainhumidity", "dafa of the terrain humidity from the arduino board")

            self.mount(RaspberryDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
