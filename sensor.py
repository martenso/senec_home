"""Support for SENEC.Home sensor."""
import logging
import struct

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_UPDATED, DOMAIN, SENSOR_TYPES, SENEC_STATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info):
    """Set up the SENEC.Home sensor."""
    data = hass.data[DOMAIN]
    async_add_entities([SenecSensor(data, sensor) for sensor in discovery_info])


class SenecSensor(RestoreEntity):
    """Implementation of a SENEC.Home sensor."""

    def __init__(self, senec_data, sensor_type):
        """Initialize the sensor."""
        self._name = SENSOR_TYPES[sensor_type][1]
        self.senec = senec_data
        self.type = sensor_type
        self._state = None
        self._data = None
        self._unit_of_measurement = SENSOR_TYPES[self.type][2]
        self._icon = SENSOR_TYPES[self.type][3]

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format("Senec", self._name)

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._unit_of_measurement is None:
            return
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return icon."""
        return self._icon

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return False

#    @property
#    def device_state_attributes(self):
#        """Return the state attributes."""
#        if self.type != "stat_state":
#            return {}
#        attr = {
#            "Version": self._data["BMS"]["MODULE_COUNT"],
#        }
#        return attr

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, DATA_UPDATED, self._schedule_immediate_update
            )
        )

    def update(self):
        """Get the latest data and update the states."""
        self._data = self.senec.data
        if self._data is None:
            return

        json_key = SENSOR_TYPES[self.type][0].split(".")

        if self._data[json_key[0]][json_key[1]][:2] == "u8":
            result = int(self._data[json_key[0]][json_key[1]][3:], 16)
        else:
            result = struct.unpack(
                "!f", bytes.fromhex(self._data[json_key[0]][json_key[1]][3:])
            )

        if self.type == "stat_state":
            self._state = SENEC_STATE[int(result)].capitalize()
        elif self.type == "solar_power":
            self._state = str(round(abs(result[0]), 2))
        elif self.type == "grid_import":
            if result[0] > 0:
                self._state = str(round(result[0], 2))
            else:
                self._state = 0
        elif self.type == "grid_export":
            if result[0] < 0:
                self._state = str(round(abs(result[0]), 2))
            else:
                self._state = 0
        elif self.type == "battery_charge":
            if result[0] > 0:
                self._state = str(round(abs(result[0]), 2))
            else:
                self._state = 0
        elif self.type == "battery_discharge":
            if result[0] < 0:
                self._state = str(round(abs(result[0]), 2))
            else:
                self._state = 0
        elif self.type == "battery_level":
            self._state = str(round(abs(int(result[0])), 0))
            self._icon = "mdi:battery-" + str(round(abs(int(result[0])), -1))
        else:
            self._state = str(round(result[0], 2))

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)
