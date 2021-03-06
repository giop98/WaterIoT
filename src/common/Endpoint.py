import copy
from enum import Enum

from common.WIOTEnum import WIOTEnum

class EndpointType(WIOTEnum):
    MQTT = 1
    REST = 2

class EndpointTypeSub(WIOTEnum):
    GENERAL  = 1
    RESOURCE = 2

class EndpointParam:

    def __init__(self, name: str, required: bool = True) -> None:
        self.name = name
        self.required = required

    def toDict(self):
        return copy.deepcopy(self.__dict__)

    @staticmethod
    def fromDict(d: dict):
        return EndpointParam(**d)

class Endpoint:

    def __init__(self, uri: str, endpointType: EndpointType, subType: EndpointTypeSub = EndpointTypeSub.GENERAL, params: list[EndpointParam] = [], mqttDescription: str = None) -> None:
        self.uri = uri
        self.endpointType = endpointType
        self.subType = subType
        self.params = params
        self.mqtt_description = mqttDescription

    def toDict(self, remType: bool):

        d = copy.deepcopy(self.__dict__)
        d["endpointType"] = self.endpointType.name
        d["subType"] = self.subType.name
        d["params"] = [e.toDict() for e in d["params"]]

        if remType:
            d.pop("endpointType")

        if self.endpointType == EndpointType.MQTT:
            d["description"] = d["mqtt_description"]
            d.pop("params")
            d.pop("subType")

        d.pop("mqtt_description")

        return d

    @staticmethod
    def fromDict(d: dict, etype: EndpointType):

        uri = d["uri"]
        subtype = EndpointTypeSub.value_of(d["subType"]) if "subType" in d.keys() else EndpointTypeSub.GENERAL
        params = [EndpointParam.fromDict(e) for e in d["params"]] if etype == EndpointType.REST else []
        description = d["description"] if etype == EndpointType.MQTT else None

        return Endpoint(uri, etype, subtype, params, description)