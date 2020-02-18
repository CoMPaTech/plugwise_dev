"""Plugwise Sensor component for HomeAssistant."""

import logging

import voluptuous as vol
import haanna

import homeassistant.helpers.config_validation as cv

from . import (
    DOMAIN,
    CONF_SMILE,
    PlugwiseThermostatSensor,
)

from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    TEMP_CELSIUS,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_PRESSURE,
)
from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "temperature": [TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    "illumination": ["lm", None, DEVICE_CLASS_ILLUMINANCE],
    "pressure": ["hPa", None, DEVICE_CLASS_PRESSURE],
}

SENSOR_AVAILABLE = {
    "illuminance": "illumination",
    "boiler_pressure": "pressure",
    "boiler_temperature": "temperature",
    "outdoor_temperature": "temperature",
}

# Configuration directives
CONF_LEGACY = "legacy_anna"

# Default directives
DEFAULT_NAME = "Plugwise Development Thermostat"
DEFAULT_USERNAME = "smile"
DEFAULT_TIMEOUT = 10
DEFAULT_PORT = 80
DEFAULT_ICON = "mdi:thermometer"
DEFAULT_MIN_TEMP = 4
DEFAULT_MAX_TEMP = 30

def setup_platform(
    hass, config, add_entities, discovery_info=None
):
    """Add the Plugwise (Anna) Thermostate."""

    if discovery_info is None:
        return

    devices = []
    for device,thermostat in hass.data[DOMAIN][CONF_SMILE].items():
        _LOGGER.info('Device %s',device)
        _LOGGER.info('Thermostat %s',thermostat)

        api = thermostat['api']
        domain_objects = (
            api.get_domain_objects()
        )

        for sensor,sensor_type in SENSOR_AVAILABLE.items():
            _LOGGER.info('Sensor %s',sensor)
            _LOGGER.info('Sensortype %s',sensor_type)
            addSensor=False
            if sensor == 'illuminance':
                _LOGGER.info('Checking for illuminance')
                if api.get_illuminance( domain_objects ):
                    addSensor=True
                    _LOGGER.info('Adding illuminance')
            if sensor == 'boiler_temperature':
                _LOGGER.info('Checking for boiler_temperature')
                if api.get_boiler_temperature( domain_objects ):
                    addSensor=True
                    _LOGGER.info('Adding boiler_temperature')
            if sensor == 'water_pressure':
                _LOGGER.info('Checking for water_pressure')
                if api.get_water_pressure( domain_objects):
                    addSensor=True
                    _LOGGER.info('Adding water_pressure')
            if sensor == 'outdoor_temperature':
                _LOGGER.info('Checking for outdoor_temperature')
                if api.get_outdoor_temperature( domain_objects):
                    addSensor=True
                    _LOGGER.info('Adding outdoor_temperature')
            if addSensor:
                devices.append(PlugwiseThermostatSensor(api,'{}_{}'.format(device,sensor),sensor,sensor_type))
    add_entities(devices)


