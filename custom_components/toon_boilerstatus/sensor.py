"""
Support for reading Opentherm boiler status data using Toon thermostat's ketelmodule.
Only works for rooted Toon.

configuration.yaml

sensor:
    - platform: toon_boilerstatus
    host: IP_ADDRESS
    port: 80
    scan_interval: 10
    resources:
        - boilersetpoint
        - boilerintemp
        - boilerouttemp
        - boilerpressure
        - boilermodulationlevel
        - roomtemp
        - roomtempsetpoint
"""
import asyncio
import logging
from datetime import timedelta, datetime
from typing import Final

import aiohttp
import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_RESOURCES,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

BASE_URL = 'http://{host}:{port}'
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
DEFAULT_NAME = "Toon "

SENSOR_LIST = {
    "boilersetpoint"        : "currentSetPoint",
    "boilerintemp"          : "thermstat_boilerRetTemp",
    "boilerouttemp"         : "thermstat_boilerTemp",
    "boilerpressure"        : "thermstat_ChPressure",
    "boilermodulationlevel" : "currentModulationLevel",
    "roomtemp"              : "currentTemp",
    "roomtempsetpoint"      : "currentSetpoint",
}

SENSOR_TYPES: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key="boilersetpoint",
        name="Boiler SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerintemp",
        name="Boiler InTemp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerouttemp",
        name="Boiler OutTemp",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerpressure",
        name="Boiler Pressure",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilermodulationlevel",
        name="Boiler Modulation",
        icon="mdi:fire",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="roomtemp",
        name="Room Temp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="roomtempsetpoint",
        name="Room Temp SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=80): cv.positive_int,
        vol.Required(CONF_RESOURCES, default=list(SENSOR_LIST)): vol.All(
            cv.ensure_list, [vol.In(list(SENSOR_LIST))]
        ),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Toon boilerstatus sensors."""

    session = async_get_clientsession(hass)
    data = ToonBoilerStatusData(session, config.get(CONF_HOST), config.get(CONF_PORT))
    prefix = config.get(CONF_NAME)
    await data.async_update()

    entities = []
    for description in SENSOR_TYPES:
        if description.key in config[CONF_RESOURCES]:
            _LOGGER.debug("Adding Toon Boiler Status sensor: %s", description.name)
            sensor = ToonBoilerStatusSensor(prefix, description, data)
            entities.append(sensor)
    async_add_entities(entities, True)


# pylint: disable=abstract-method
class ToonBoilerStatusData:
    """Handle Toon object and limit updates."""

    def __init__(self, session, host, port):
        """Initialize the data object."""

        self._session = session
        self._url = ''
        self._url_happ = BASE_URL.format(host = host, port = port) + "/happ_thermstat?action=getThermostatInfo"
        self._url_rrd = BASE_URL.format(host = host, port = port) + \
        "/hcb_rrd?action=getRrdData&loggerName={loggerName}&rra=30days&readableTime=0&nullForNaN=1&from={timeStamp}"
        self.data = None
        
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Download and update data from Toon."""

        try:
            async with async_timeout.timeout(5):
                self._url = self._url_happ
                response = await self._session.get(
                    self._url, headers={"Accept-Encoding": "identity"}
                )
            self.data = await response.json(content_type="text/javascript")
            _LOGGER.debug("Data received from Toon (happ): %s", self.data)
            timeStamp = int(datetime.now().replace(second=0,microsecond=0).timestamp()) - 60
            for sensorName in SENSOR_LIST:
                loggerName = SENSOR_LIST[sensorName]
                if "thermstat" in loggerName:
                    async with async_timeout.timeout(5):
                        self._url = self._url_rrd.format(loggerName = loggerName, timeStamp = timeStamp)
                        response = await self._session.get(
                            self._url, headers={"Accept-Encoding": "identity"}
                        )
                    data = await response.json(content_type="text/javascript")
                    _LOGGER.debug("Data received from Toon (rrd): %s", data)
                    sampleTimeStr = sorted(data.keys())[-1]
                    self.data[loggerName] = data[sampleTimeStr]
                    self.data['sampleTime'] = int(sampleTimeStr)
        except aiohttp.ClientError:
            _LOGGER.error("Cannot connect to Toon using url '%s'", self._url)
        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout error occurred while connecting to Toon using url '%s'",
                self._url
            )
        except (TypeError, KeyError) as err:
            _LOGGER.error("Cannot parse data received from Toon: %s", err)


class ToonBoilerStatusSensor(SensorEntity):
    """Representation of a Toon Boilerstatus sensor."""

    def __init__(self, prefix, description: SensorEntityDescription, data):
        """Initialize the sensor."""
        self.entity_description = description
        self._data = data
        self._prefix = prefix
        self._type = self.entity_description.key
        self._attr_icon = self.entity_description.icon
        self._attr_name = self._prefix + self.entity_description.name
        self._attr_state_class = self.entity_description.state_class
        self._attr_native_unit_of_measurement = (
            self.entity_description.native_unit_of_measurement
        )
        self._attr_device_class = self.entity_description.device_class
        self._attr_unique_id = f"{self._prefix}_{self._type}"

        self._state = None
        self._last_updated = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr

    async def async_update(self):
        """Get the latest data and use it to update our sensor state."""

        await self._data.async_update()
        boiler = self._data.data

        if boiler:
            if "sampleTime" in boiler and boiler["sampleTime"] is not None:
                self._last_updated = boiler["sampleTime"]
            for type in SENSOR_LIST:
                if self._type == type:
                    if SENSOR_LIST[type] in boiler and boiler[SENSOR_LIST[type]] is not None:
                        if (self._type == "roomtemp" or self._type == "roomtempsetpoint"):
                            self._state = float(boiler[SENSOR_LIST[type]])/100
                        else: 
                            self._state = float(boiler[SENSOR_LIST[type]])
            _LOGGER.debug("Device: %s State: %s", self._type, self._state)
