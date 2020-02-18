"""Plugwise Climate component for HomeAssistant."""

import logging

import voluptuous as vol
import haanna

from . import (
    DOMAIN,
    CONF_SMILE,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    PlugwiseThermostatDevice,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateDevice,
)
from homeassistant.exceptions import PlatformNotReady


_LOGGER = logging.getLogger(__name__)

# Read platform configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(
            CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP
        ): cv.positive_int,
        vol.Optional(
            CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP
        ): cv.positive_int,
    }
)


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
        devices.append(
            PlugwiseThermostatDevice(
                thermostat['api'],
                '{}_{}'.format(device,CONF_SMILE),
                4,30,
                #config[CONF_MIN_TEMP],
                #config[CONF_MAX_TEMP],
            )
        )
    add_entities(devices)


