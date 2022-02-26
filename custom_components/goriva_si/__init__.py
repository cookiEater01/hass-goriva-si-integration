"""The Cene naftnih derivatov integration."""
from __future__ import annotations

from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.helpers.discovery import async_load_platform
import voluptuous as vol
from datetime import timedelta
import homeassistant.helpers.config_validation as cv
import logging
from .goriva_si_api import get_data
from .const import (
    DOMAIN,
    NAME,
    CONF_RADIUS,
    CONF_LOCATION,
    FUEL_TYPES,
    CONF_FUEL_TYPES,
    CONF_ONLY_STATIONS,
)

from homeassistant.const import CONF_SCAN_INTERVAL

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.LIGHT]

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(minutes=120)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_LOCATION): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
                vol.Required(CONF_RADIUS, default=5000): vol.All(
                    cv.positive_int, vol.Range(min=1)
                ),
                vol.Optional(CONF_FUEL_TYPES, default=FUEL_TYPES): vol.All(
                    cv.ensure_list, [vol.In(FUEL_TYPES)]
                ),
                vol.Optional(CONF_ONLY_STATIONS, default=[]): vol.All(
                    cv.ensure_list, [cv.positive_int]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Cene naftnih derivatov from a config entry."""

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    _LOGGER.debug("Setting up integration")

    goriva_si = GorivaSiData(hass, conf)

    setup_ok = await hass.async_add_executor_job(goriva_si.setup)

    if not setup_ok:
        _LOGGER.error("Could not setup integration")
        return False

    hass.data[DOMAIN] = goriva_si

    hass.async_create_task(
        async_load_platform(
            hass,
            SENSOR_DOMAIN,
            DOMAIN,
            discovered=goriva_si.stations,
            hass_config=conf,
        )
    )

    return True


class GorivaSiData:
    """Get the latest data from goriva.si API"""

    def __init__(self, hass, conf):
        """Initialize the data object."""
        self.location = conf[CONF_LOCATION]
        self.radius = conf[CONF_RADIUS]
        self.update_interval = conf[CONF_SCAN_INTERVAL]
        self.fuel_types = conf[CONF_FUEL_TYPES]
        self.only_stations = conf[CONF_ONLY_STATIONS]
        self.stations = {}
        self._hass = hass

    def add_station(self, station: dict):
        """Add fuel station to the list."""

        _LOGGER.debug("add station")

        station_id = station["pk"]

        if station_id in self.stations:
            _LOGGER.warning(
                "Sensor for station with pk %s was already created", station_id
            )
            return
        self.stations[station_id] = station
        _LOGGER.debug("add_station called for station: %s", station)

    def setup(self):
        """Read the initial data from the server, to initialize the list of stations."""

        _LOGGER.debug("setup")

        url = (
            "https://goriva.si/api/v1/search/?position="
            + str(self.location).replace(" ", "+")
            + "&radius="
            + str(self.radius)
        )

        data = get_data(url)

        if not (found_stations := data["results"]):
            _LOGGER.warning("Could not find any station in range")
        else:
            for station in found_stations:
                if self.only_stations and station["pk"] in self.only_stations:
                    _LOGGER.debug("adding station that is on the list")
                    self.add_station(station)
                elif not self.only_stations:
                    _LOGGER.debug("adding station")
                    self.add_station(station)

        return True

    async def fetch_data(self):
        """Get the latest data from goriva.si API."""

        _LOGGER.info("Updating petrol station prices from goriva.si")

        prices = {}

        url = (
            "https://goriva.si/api/v1/search/?position="
            + str(self.location).replace(" ", "+")
            + "&radius="
            + str(self.radius)
        )

        data = await self._hass.async_add_executor_job(get_data, url)

        for station in data["results"]:
            fp = station["prices"]
            prices.update(fp)

        return prices
