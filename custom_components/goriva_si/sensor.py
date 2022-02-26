"""The Cene naftnih derivatov integration."""
from __future__ import annotations
from .const import DOMAIN, NAME
import logging
import re
import random

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CURRENCY_EURO,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

ICON = "mdi:gas-station"

_LOGGER = logging.getLogger(__name__)

ATTR_FRANCHISE = "franchise"
ATTR_FUEL_TYPE = "fuel_type"
ATTR_ZIP_CODE = "zip"
ATTR_PRICE = "price"
ATTR_STATION_NAME = "station_name"
ATTR_ADDRESS = "address"
ATTRIBUTION = "Data provided by https://goriva.si"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Cene naftnih derivatov sensors."""

    if discovery_info is None:
        return

    goriva = hass.data[DOMAIN]

    async def async_update_data():
        """Fetch data from goriva.si API"""

        try:
            _LOGGER.debug("Requesting update")
            response = await goriva.fetch_data()
            return response
        except LookupError as err:
            raise UpdateFailed("Failed to fetch data") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=NAME,
        update_method=async_update_data,
        update_interval=goriva.update_interval,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    _LOGGER.info("Coordinator First: %s", coordinator.data)

    stations = discovery_info.values()
    entities = []

    for station in stations:
        for fuel in goriva.fuel_types:
            if fuel not in station["prices"]:
                _LOGGER.warning(
                    "Station %s does not offer %s fuel", station["pk"], fuel
                )
                continue

            name = (
                station["name"]
                .replace(" ", "_")
                .lower()
                .replace("č", "c")
                .replace("ž", "z")
                .replace("š", "s")
                .replace(".", "")
                .replace("-", "")
            )

            sensor = FuelStationByFuelSensor(
                coordinator, station, fuel, f"{name}_{fuel}"
            )
            entities.append(sensor)

    _LOGGER.info("Added sensors %s", entities)

    async_add_entities(entities)


class FuelStationByFuelSensor(CoordinatorEntity, SensorEntity):
    """Contains prices for fuel in a given station."""

    def __init__(self, coordinator, station, fuel_type, name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station = station
        self._station_id = f"{station['pk']}_{fuel_type}"
        self._station_pk = station["pk"]
        self._name = name
        self._latitude = station["lat"]
        self._longitude = station["lng"]
        self._franchise = station["franchise"]
        self._address = station["address"]
        self._zip_code = station["zip_code"]
        self._fuel_type = fuel_type
        self._price = station["prices"][fuel_type]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        return CURRENCY_EURO

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self._station_id}_{self._fuel_type}"

    @property
    def native_value(self):
        """Return the state of the device."""
        # key Fuel_type is not available when the fuel station is closed, use "get" instead of "[]" to avoid exceptions
        # return self.coordinator.data[self._station_id].get(self._price)
        return self.coordinator.data[self._station_pk][self._fuel_type]

    @property
    def extra_state_attributes(self):
        """Return the attributes of the device."""
        # data = self.coordinator.data[self._station_id]

        attrs = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_FRANCHISE: self._station["franchise"],
            ATTR_STATION_NAME: self._station["name"],
            ATTR_PRICE: self._price,
            ATTR_FUEL_TYPE: self._fuel_type,
            ATTR_ZIP_CODE: self._zip_code,
            ATTR_ADDRESS: self._address,
        }

        return attrs
