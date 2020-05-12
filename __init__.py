"""The SENEC.Home integration."""
import requests
import json

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_MONITORED_CONDITIONS, CONF_SCAN_INTERVAL, CONF_HOST
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import DATA_UPDATED, DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

DEFAULT_INTERVAL = timedelta(seconds=10)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                ),
                vol.Optional(
                    CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)
                ): vol.All(cv.ensure_list, [vol.In(list(SENSOR_TYPES))]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the SENEC.Home component."""
    conf = config[DOMAIN]
    data = hass.data[DOMAIN] = SenecData(hass, conf.get(CONF_HOST))

    async_track_time_interval(hass, data.update, conf[CONF_SCAN_INTERVAL])

    hass.async_create_task(
        async_load_platform(
            hass, SENSOR_DOMAIN, DOMAIN, conf[CONF_MONITORED_CONDITIONS], config
        )
    )

    return True


class SenecData:
    """Get the latest data from SENEC.Home."""

    def __init__(self, hass, host_ip):
        """Initialize the data object."""
        self.data = None
        self._hass = hass
        self._server = host_ip

    def update(self, now=None):
        """Get the latest data from SENEC.Home."""

        _LOGGER.debug("Fetch data from SENEC.Home")

        headers = {
            "Content-Type": "application/json",
        }
        data = '{"STATISTIC":{},"ENERGY":{},"BMS":{}}'
        response = requests.post(
            "http://" + self._server + "/lala.cgi", headers=headers, data=data
        )
        senec = json.loads(response.text)

        self.data = senec
        dispatcher_send(self._hass, DATA_UPDATED)
