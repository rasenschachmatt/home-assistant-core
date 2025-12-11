"""Allows to configure a switch using RPi GPIO."""

from __future__ import annotations

from typing import Any

from gpiozero import LED
import voluptuous as vol

from homeassistant.components.switch import (
    PLATFORM_SCHEMA as SWITCH_PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.const import CONF_HOST, DEVICE_DEFAULT_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import (
    CONF_INVERT_LOGIC,
    DEFAULT_INVERT_LOGIC,
    DOMAIN,
    setup_output,
    write_output,
)

CONF_PORTS = "ports"

_SENSORS_SCHEMA = vol.Schema({cv.positive_int: cv.string})

PLATFORM_SCHEMA = SWITCH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORTS): _SENSORS_SCHEMA,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Remote Raspberry PI GPIO devices."""
    host = config[CONF_HOST]
    invert_logic = config[CONF_INVERT_LOGIC]
    ports = config[CONF_PORTS]

    devices = []
    for port, name in ports.items():
        try:
            led = setup_output(host, port, invert_logic)
        except (ValueError, IndexError, KeyError, OSError):
            return
        new_switch = RemoteRPiGPIOSwitch(name, led, host, port)
        devices.append(new_switch)

    add_entities(devices)


class RemoteRPiGPIOSwitch(SwitchEntity):
    """Representation of a Remote Raspberry Pi GPIO."""

    _attr_assumed_state = True
    _attr_should_poll = False

    def __init__(self, name: str | None, led: LED, host: str, port: int) -> None:
        """Initialize the pin."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_is_on = False
        self._switch = led
        self._host = host
        self._port = port

    @property
    def unique_id(self) -> str:
        """Return a unique ID based on host and port."""
        host_string = self._host.replace(".", "_").replace(":", "_")
        return f"{DOMAIN}_{host_string}_{self._port}"

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        write_output(self._switch, 1)
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        write_output(self._switch, 0)
        self._attr_is_on = False
        self.schedule_update_ha_state()
