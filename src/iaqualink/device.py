from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from iaqualink.exception import AqualinkOperationNotSupportedException

if TYPE_CHECKING:
    from iaqualink.typing import DeviceData

LOGGER = logging.getLogger("iaqualink")


class AqualinkDevice:
    def __init__(
        self,
        system: Any,  # Should be AqualinkSystem but causes mypy errors.
        data: DeviceData,
    ):
        self.system = system
        self.data = data

    def __repr__(self) -> str:
        attrs = ["data"]
        attrs = [f"{i}={getattr(self, i)!r}" for i in attrs]
        return f"{self.__class__.__name__}({', '.join(attrs)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AqualinkDevice):
            return NotImplemented

        if (
            self.system.serial == other.system.serial
            and self.data == other.data
        ):
            return True
        return False

    @property
    def label(self) -> str:
        raise NotImplementedError

    @property
    def state(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def manufacturer(self) -> str:
        raise NotImplementedError

    @property
    def model(self) -> str:
        raise NotImplementedError


class AqualinkSensor(AqualinkDevice):
    pass


class AqualinkBinarySensor(AqualinkSensor):
    """These are non-actionable sensors, essentially read-only on/off."""

    @property
    def is_on(self) -> bool:
        raise NotImplementedError


class AqualinkSwitch(AqualinkBinarySensor, AqualinkDevice):
    async def turn_on(self) -> None:
        raise NotImplementedError

    async def turn_off(self) -> None:
        raise NotImplementedError


class AqualinkLight(AqualinkSwitch, AqualinkDevice):
    @property
    def brightness(self) -> int | None:
        return None

    @property
    def supports_brightness(self) -> bool:
        return self.brightness is not None

    async def set_brightness(self, _: int) -> None:
        if self.supports_brightness is True:
            raise NotImplementedError
        raise AqualinkOperationNotSupportedException

    @property
    def effect(self) -> str | None:
        return None

    @property
    def supports_effect(self) -> bool:
        return self.effect is not None

    async def set_effect_by_name(self, _: str) -> None:
        if self.supports_effect is True:
            raise NotImplementedError
        raise AqualinkOperationNotSupportedException

    async def set_effect_by_id(self, _: int) -> None:
        if self.supports_effect is True:
            raise NotImplementedError
        raise AqualinkOperationNotSupportedException

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """RGB color values as (red, green, blue) tuple."""
        return None

    @property
    def supports_rgb_color(self) -> bool:
        return self.rgb_color is not None

    async def set_rgb_color(self, red: int, green: int, blue: int) -> None:
        if self.supports_rgb_color is True:
            raise NotImplementedError
        raise AqualinkOperationNotSupportedException

    @property
    def white_value(self) -> int | None:
        """White value for RGBW lights."""
        return None

    @property
    def supports_white_value(self) -> bool:
        return self.white_value is not None

    async def set_white_value(self, white: int) -> None:
        if self.supports_white_value is True:
            raise NotImplementedError
        raise AqualinkOperationNotSupportedException


class AqualinkThermostat(AqualinkSwitch, AqualinkDevice):
    @property
    def unit(self) -> str:
        raise NotImplementedError

    @property
    def current_temperature(self) -> str:
        raise NotImplementedError

    @property
    def target_temperature(self) -> str:
        raise NotImplementedError

    @property
    def max_temperature(self) -> int:
        raise NotImplementedError

    @property
    def min_temperature(self) -> int:
        raise NotImplementedError

    async def set_temperature(self, _: int) -> None:
        raise NotImplementedError


class AqualinkHeatPump(AqualinkThermostat, AqualinkDevice):
    @property
    def mode(self) -> str | None:
        """Current heat pump mode (heat, cool, off)."""
        return None

    @property
    def supports_cooling(self) -> bool:
        """Whether the heat pump supports cooling/chilling mode."""
        return False

    async def set_mode(self, mode: str) -> None:
        """Set heat pump mode (heat, cool, off)."""
        raise NotImplementedError

    @property
    def heat_pump_type(self) -> str | None:
        """Type of heat pump (2-wire, 4-wire, etc.)."""
        return None
