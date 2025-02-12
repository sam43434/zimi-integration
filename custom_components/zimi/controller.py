"""Zimi Controller wrapper class device."""
import logging
import pprint
import socket

from zcc import (
    ControlPoint,
    ControlPointDescription,
    ControlPointDiscoveryService,
    ControlPointError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS, TIMEOUT, VERBOSITY, WATCHDOG


class ZimiController:
    """Manages a single Zimi Controller hub."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize."""
        self.controller: ControlPoint = None
        self.hass = hass
        self.config = config

        self.logger = logging.getLogger(__name__)
        if config.data.get("debug", False):
            self.logger.setLevel(logging.DEBUG)

        self.logger.debug("__init() %s", pprint.pformat(self.config))

        # store (this) bridge object in hass data
        hass.data.setdefault(DOMAIN, {})[self.config.entry_id] = self

    @property
    def debug(self) -> bool:
        """Return the debug flag for this hub."""
        return self.config.data.get(DEBUG, False)

    @property
    def host(self) -> str:
        """Return the host of this hub."""
        return self.config.data[CONF_HOST]

    @property
    def port(self) -> int:
        """Return the host of this hub."""
        return self.config.data[CONF_PORT]

    @property
    def timeout(self) -> int:
        """Return the timeout of this hub."""
        if self.config.data[TIMEOUT] == 0:
            self.config.data[TIMEOUT] = 3
        return self.config.data[TIMEOUT]

    async def connect(self) -> bool:
        """Initialize Connection with the Zimi Controller."""
        try:
            self.logger.info(
                "ControlPoint inititation starting to %s:%d with verbosity=%s, timeout=%d and watchdog=%d",
                self.host,
                self.port,
                self.verbosity,
                self.timeout,
                self.watchdog,
            )
            if self.host == "":
                description = await ControlPointDiscoveryService().discover()
                # self.config.data[CONF_HOST] = description.host
                # self.config.data[CONF_PORT] = description.port
            else:
                description = ControlPointDescription(host=self.host, port=self.port)

            self.controller = ControlPoint(
                description=description, verbosity=self.verbosity, timeout=self.timeout
            )
            await self.controller.connect()
            self.logger.info("ControlPoint inititation completed")
            self.logger.info("\n%s", self.controller.describe())

            if self.watchdog > 0:
                self.controller.start_watchdog(self.watchdog)
                self.logger.info("Started %d minute watchdog", self.watchdog)
        except ControlPointError as error:
            self.logger.info("ControlPoint initiation failed")
            raise ConfigEntryNotReady(error) from error

        if self.controller:
            self.hass.config_entries.async_forward_entry_setups(self.config, PLATFORMS)

        return True

    @property
    def verbosity(self) -> int:
        """Return the verbosity of this hub."""
        try:
            if self.config.data[VERBOSITY] == None:
                self.config.data[VERBOSITY] = 1
            return self.config.data[VERBOSITY]
        except KeyError:
            return 1

    @property
    def watchdog(self) -> int:
        """Return the watchdog timer of this hub."""
        try:
            if self.config.data[WATCHDOG] == None:
                self.config.data[WATCHDOG] = 1800
            return self.config.data[WATCHDOG]
        except KeyError:
            return 0
