import logging

from common.RESTServiceApp import RESTServiceApp
from common.Service import *
from common.Endpoint import *
from common.PingCatalog import PingCatalog
from common.RESTBase import RESTBase
from common.SettingsManager import SettingsManager

# class Callback:
#     get_callback = None
#     post_callback = None
#     put_callback = None
#     del_callback = None

class WIOTRestApp(RESTServiceApp):

    def __init__(self, log_stdout_level: int = logging.INFO, log_filename: str = None) -> None:
        super().__init__(log_stdout_level, log_filename)

    def create(self, settings: SettingsManager, serviceName: str, srvT: ServiceType, srvSubT: ServiceSubType = None, devid: int = None):
        self._settings = settings
        port = self._settings.rest_server.port
        host = self._settings.rest_server.host
        catalogHost = self._settings.catalog.host
        catalogPort = self._settings.catalog.port
        catalogPing = self._settings.catalog.ping_ms

        self._service = Service(serviceName, srvT, host, port, srvSubT, devid)
        self._pinger = PingCatalog(self._service, catalogHost, catalogPort, catalogPing, self._logger)

        self.subsribe_evt_stop(self._pinger.stop)

    def mount(self, root: RESTBase, conf: dict, path: str = "/"):
        return super().mount(path, root, conf)

    def loop(self):
        self._pinger.run()
        super().loop(self._service.port, self._service.host)

    def addRESTEndpoint(self, uri: str, params: tuple[EndpointParam] = (), endpointTypeSub: EndpointTypeSub = EndpointTypeSub.GENERAL):

        # class WIOTRestApp_DummyClass:
        #     exposed = True

        #     def GET(self):
        #         callback.get_callback()

        if uri[0] != '/':
            raise ValueError("Uri must begin with a '/'")

        self._service.addEndpoint(Endpoint(uri, EndpointType.REST, endpointTypeSub, params))

    def addMQTTEndpoint(self, uri: str, description: str):
        """
        uri must be absolute like /temperature/room
        the endpoint will be registered as /{service_name}/temperature/room
        """

        if uri[0] != '/':
            raise ValueError("Uri must begin with a '/'")
 
        ap = f"/{self.service.deviceid}" if self.service.deviceid is not None else ""
        self._service.addEndpoint(Endpoint(f"/{self._service.name}{ap}{uri}", EndpointType.MQTT, mqttDescription=description))

    @property
    def service(self):
        return self._service

    @property
    def pinger(self):
        return self._pinger
