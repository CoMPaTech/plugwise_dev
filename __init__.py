"""Plugwise Climate component for HomeAssistant."""

import logging

import voluptuous as vol
import haanna

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries, core

from homeassistant.components.climate import (
    ClimateDevice,
)

from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_AUTO,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)

from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)

from .const import (
    CONF_LEGACY,
    CONF_SMILE,
    DEFAULT_NAME,
    DEFAULT_USERNAME,
    DEFAULT_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_ICON,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DOMAIN,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_LEGACY,
    DEFAULT_ICON,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    CURRENT_HVAC_DHW,
)


from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)


# HVAC modes
ATTR_HVAC_MODES_1 = [HVAC_MODE_HEAT, HVAC_MODE_AUTO]
ATTR_HVAC_MODES_2 = [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO]

SUPPORT_FLAGS = (
            SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
            )

SMILE_CONFIG = vol.Schema(
        {
            vol.Optional(
                CONF_NAME, default=DEFAULT_NAME
            ): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(
                CONF_LEGACY, default=False
            ): cv.boolean,
            vol.Optional(
                CONF_PORT, default=DEFAULT_PORT
            ): cv.port,
            vol.Optional(
                CONF_USERNAME, default=DEFAULT_USERNAME
            ): cv.string,
        }
)

# Read platform configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
        {
                vol.Optional(CONF_SMILE): vol.All(
                    cv.ensure_list,
                    [
                        vol.All(
                            cv.ensure_list, [SMILE_CONFIG],
                        ),
                    ],
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


#async def async_setup_platform(
#    hass, config, async_add_entities, discovery_info=None
#):
def setup(hass, config):
    """Add the Plugwise (Anna) Thermostate."""

    conf = config.get(DOMAIN)

    if conf is None:
        raise PlatformNotReady
        #conf = {}

    _LOGGER.info('Plugwise %s',conf)
    hass.data[DOMAIN] = {}

    if CONF_SMILE in conf:
        smiles = conf[CONF_SMILE]

        _LOGGER.info('Smiles %s',smiles)
        hass.data[DOMAIN][CONF_SMILE] = {}

        for smile in smiles:
            _LOGGER.info('Smile %s',smile)
            smile_config=smile[0]

            api = haanna.Haanna(
                smile_config[CONF_USERNAME],
                smile_config[CONF_PASSWORD],
                smile_config[CONF_HOST],
                smile_config[CONF_PORT],
                smile_config[CONF_LEGACY],
            )
            try:
                api.ping_anna_thermostat()
            except OSError:
                _LOGGER.debug(
                    "Ping failed, retrying later", exc_info=True
                )
                raise PlatformNotReady
        
            hass.data[DOMAIN][CONF_SMILE][smile_config[CONF_NAME]] = { 'api': api }
    

    hass.helpers.discovery.load_platform('climate', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    _LOGGER.info('Config %s',hass.data[DOMAIN])
    return True


class PlugwiseThermostatSensor(Entity):
    """Representation of a Plugwise thermostat."""

    def __init__(self, api, name, sensor, sensor_type):
        """Set up the Plugwise API."""
        self._api = api
        self._name = name
        self._sensor = sensor
        self._sensor_type = sensor_type
        self._domain_objects = None
        self._state = None

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return DEFAULT_ICON

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Update the data from the thermostat."""
        _LOGGER.debug("Update called")
        self._domain_objects = (
            self._api.get_domain_objects()
        )
        _LOGGER.info("Sensor {}".format(self._sensor))
        if self._sensor == 'illuminance':
          self._state = self._api.get_illuminance(
            self._domain_objects
          )
        if self._sensor == 'boiler_temperature':
          self._state = self._api.get_boiler_temperature(
            self._domain_objects
          )
        if self._sensor == 'water_pressure':
          self._state = self._api.get_water_pressure(
            self._domain_objects
          )
        if self._sensor == 'outdoor_temperature':
          self._state = self._api.get_outdoor_temperature(
            self._domain_objects
          )


class PlugwiseThermostatDevice(ClimateDevice):
    """Representation of an Plugwise thermostat."""

    def __init__(self, api, name, min_temp, max_temp):
        """Set up the Plugwise API."""
        self._api = api
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._name = name
        self._domain_objects = None
        self._outdoor_temperature = None
        self._selected_schema = None
        self._preset_mode = None
        self._presets = None
        self._presets_list = None
        self._heating_status = None
        self._cooling_status = None
        self._dhw_status = None
        self._schema_names = None
        self._schema_status = None
        self._current_temperature = None
        self._thermostat_temperature = None
        self._schedule_temperature = None
        self._hvac_mode = None
        self._hvac_modes_1 = ATTR_HVAC_MODES_1
        self._hvac_modes_2 = ATTR_HVAC_MODES_2

    @property
    def hvac_action(self):
        """Return the current action."""
        if self._heating_status:
            return CURRENT_HVAC_HEAT
        elif self._cooling_status:
            return CURRENT_HVAC_COOL
        elif self._dhw_status:
            return CURRENT_HVAC_DHW
        else:
            return CURRENT_HVAC_IDLE

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return DEFAULT_ICON

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {}
        if self._outdoor_temperature is not None:
            attributes[
                "outdoor_temperature"
            ] = self._outdoor_temperature
        attributes["available_schemas"] = self._schema_names
        attributes[
            "selected_schema"
        ] = self._selected_schema

    @property
    def preset_modes(self):
        """
        Return the available preset modes list and make the presets with
        their temperatures available.
        """
        return self._presets_list

    @property
    def hvac_modes(self):
        """Return the available hvac modes list."""
        if self._heating_status is not None:
            if self._cooling_status is not None:
                return self._hvac_modes_2
            else:
                return self._hvac_modes_1

    @property
    def hvac_mode(self):
        """Return current active hvac state."""
        if self._schema_status:
            return HVAC_MODE_AUTO
        elif self._heating_status is not None:
            if self._cooling_status is not None:
                return HVAC_MODE_HEAT_COOL
            else:
                return HVAC_MODE_HEAT

    @property
    def thermostat_temperature(self):
        """
        Return the thermostat set temperature. This setting directly follows
        the changes in temperature from the interface or schedule. After a 
        small delay, the target_temperature value will change as well, 
        this is some kind of filter-function.
        """
        return self._thermostat_temperature

    @property
    def target_temperature(self):
        """
        Returns the active target temperature.
        From the XML the thermostat-value is used because it updates
        'immediately' compared to the target_temperature-value.
        This way the information on the card is "immediately" updated
        after changing the preset, temperature, etc.
        """
        return self._thermostat_temperature

    @property
    def preset_mode(self):
        """
        Return the active selected schedule-name, or the (temporary) active 
        preset or Temporary in case of a manual change in the set-temperature.
        """
        if self._presets is not None:
            presets = self._presets
            preset_temperature = presets.get(
                self._preset_mode, "none"
            )
            if self.hvac_mode == HVAC_MODE_AUTO:
                if (
                    self._thermostat_temperature
                    == self._schedule_temperature
                ):
                    return "{}".format(
                        self._selected_schema
                    )
                elif (
                    self._thermostat_temperature
                    == preset_temperature
                ):
                    return self._preset_mode
                else:
                    return "Temporary"
            elif (
                self._thermostat_temperature
                != preset_temperature
            ):
                return "Temporary"
            else:
                return self._preset_mode

    @property
    def current_temperature(self):
        """Return the current room temperature."""
        return self._current_temperature

    @property
    def min_temp(self):
        """Return the minimal temperature possible to set."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature possible to set."""
        return self._max_temp

    @property
    def temperature_unit(self):
        """Return the unit of measured temperature."""
        return TEMP_CELSIUS

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        _LOGGER.debug("Adjusting temperature")
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if (
            temperature is not None
            and self._min_temp
            < temperature
            < self._max_temp
        ):
            _LOGGER.debug("Changing temporary temperature")
            self._api.set_temperature(
                self._domain_objects, temperature
            )
        else:
            _LOGGER.error("Invalid temperature requested")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the hvac mode."""
        _LOGGER.debug(
            "Adjusting hvac_mode (i.e. schedule/schema)"
        )
        schema_mode = "false"
        if hvac_mode == HVAC_MODE_AUTO:
            schema_mode = "true"
        self._api.set_schema_state(
            self._domain_objects,
            self._selected_schema,
            schema_mode,
        )

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        _LOGGER.debug("Changing preset mode")
        self._api.set_preset(
            self._domain_objects, preset_mode
        )

    async def async_update(self):
        """Update the data from the thermostat."""
        _LOGGER.debug("Update called")
        self._domain_objects = (
            self._api.get_domain_objects()
        )
        self._outdoor_temperature = self._api.get_outdoor_temperature(
            self._domain_objects
        )
        self._selected_schema = self._api.get_active_schema_name(
            self._domain_objects
        )
        self._preset_mode = self._api.get_current_preset(
            self._domain_objects
        )
        self._presets = self._api.get_presets(
            self._domain_objects
        )
        self._presets_list = list(
            self._api.get_presets(self._domain_objects)
        )
        self._heating_status = self._api.get_heating_status(
            self._domain_objects
        )
        self._cooling_status = self._api.get_cooling_status(
            self._domain_objects
        )
        self._dhw_status = self._api.get_domestic_hot_water_status(
            self._domain_objects
        )
        self._schema_names = self._api.get_schema_names(
            self._domain_objects
        )
        self._schema_status = self._api.get_schema_state(
            self._domain_objects
        )
        self._current_temperature = self._api.get_current_temperature(
            self._domain_objects
        )
        self._thermostat_temperature = self._api.get_thermostat_temperature(
            self._domain_objects
        )
        self._schedule_temperature = self._api.get_schedule_temperature(
            self._domain_objects
        )
