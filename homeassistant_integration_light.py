"""Support for Aqualink pool lights."""

from __future__ import annotations

import asyncio
from typing import Any

from iaqualink.device import AqualinkLight

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AqualinkConfigEntry, refresh_system
from .entity import AqualinkEntity
from .utils import await_or_reraise

# Allow Home Assistant to queue updates while dragging color picker
# This prevents sending commands for every pixel of the drag
PARALLEL_UPDATES = 1

# Debounce delay for color changes (in seconds)
# Wait this long after last color change before sending to device
DEBOUNCE_DELAY = 0.3


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AqualinkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up discovered lights."""
    async_add_entities(
        (HassAqualinkLight(dev) for dev in config_entry.runtime_data.lights),
        True,
    )


class HassAqualinkLight(AqualinkEntity[AqualinkLight], LightEntity):
    """Representation of a light."""

    def __init__(self, dev: AqualinkLight) -> None:
        """Initialize AquaLink light."""
        super().__init__(dev)
        self._attr_name = dev.label
        
        # Debouncing for color changes
        self._pending_update: dict[str, Any] | None = None
        self._debounce_task: asyncio.Task | None = None
        self._update_lock = asyncio.Lock()
        
        # Set up supported features
        supported_features = LightEntityFeature(0)
        if dev.supports_effect:
            self._attr_effect_list = list(dev.supported_effects)
            supported_features |= LightEntityFeature.EFFECT
        self._attr_supported_features = supported_features
        
        # Determine color mode based on device capabilities
        # Priority: RGBW > RGB > BRIGHTNESS > ONOFF
        color_mode = ColorMode.ONOFF
        if dev.supports_rgb_color and dev.supports_white_value:
            color_mode = ColorMode.RGBW
        elif dev.supports_rgb_color:
            color_mode = ColorMode.RGB
        elif dev.supports_brightness:
            color_mode = ColorMode.BRIGHTNESS
        
        self._attr_color_mode = color_mode
        self._attr_supported_color_modes = {color_mode}

    @property
    def is_on(self) -> bool:
        """Return whether the light is on or off."""
        return self.dev.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light (0-255)."""
        if (brightness_pct := self.dev.brightness) is not None:
            return round(brightness_pct * 255 / 100)
        return None

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self.dev.effect

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value."""
        return self.dev.rgb_color

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the rgbw color value."""
        if self.dev.supports_white_value and self.dev.rgb_color:
            rgb = self.dev.rgb_color
            white = self.dev.white_value or 0
            return (*rgb, white)
        return None

    async def _debounced_update(self) -> None:
        """Execute the debounced update after delay."""
        await asyncio.sleep(DEBOUNCE_DELAY)
        
        async with self._update_lock:
            if self._pending_update is None:
                return
            
            kwargs = self._pending_update
            self._pending_update = None
            
            # Execute the actual update
            await self._execute_turn_on(kwargs)

    async def _execute_turn_on(self, kwargs: dict[str, Any]) -> None:
        """Execute the actual turn on command."""
        # Handle RGB color (for RGB mode lights)
        if rgb_color := kwargs.get(ATTR_RGB_COLOR):
            # For RGB mode, explicitly set white to 0
            await await_or_reraise(self.dev.set_rgb_color(*rgb_color, white=0))
            return
        
        # Handle RGBW color (for RGBW mode lights)
        if rgbw_color := kwargs.get(ATTR_RGBW_COLOR):
            # Set RGB and white together in a single call to avoid race conditions
            if rgbw_color[3] > 0 or all(c == 0 for c in rgbw_color[:3]):
                # Set white value if: explicitly requested OR no RGB color (pure white)
                await await_or_reraise(self.dev.set_rgb_color(*rgbw_color[:3], white=rgbw_color[3]))
            else:
                # When selecting colors from picker, turn off white LEDs
                await await_or_reraise(self.dev.set_rgb_color(*rgbw_color[:3], white=0))
            return
        
        # Handle effects
        if effect_name := kwargs.get(ATTR_EFFECT):
            await await_or_reraise(self.dev.set_effect_by_name(effect_name))
            return
        
        # Handle brightness (for BRIGHTNESS mode lights or as fallback)
        if brightness := kwargs.get(ATTR_BRIGHTNESS):
            # Aqualink supports percentages in 25% increments.
            pct = int(round(brightness * 4.0 / 255)) * 25
            await await_or_reraise(self.dev.set_brightness(pct))
            return
        
        # Default: just turn on
        await await_or_reraise(self.dev.turn_on())

    @refresh_system
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light.

        This handles RGB/RGBW color, brightness, and light effects.
        Uses debouncing for color changes to prevent flooding the API.
        """
        # Check if this is a color change that should be debounced
        is_color_change = ATTR_RGB_COLOR in kwargs or ATTR_RGBW_COLOR in kwargs
        
        if is_color_change:
            # Store the pending update
            async with self._update_lock:
                self._pending_update = kwargs
                
                # Cancel existing debounce task if any
                if self._debounce_task and not self._debounce_task.done():
                    self._debounce_task.cancel()
                
                # Start new debounce task
                self._debounce_task = asyncio.create_task(self._debounced_update())
            
            # Optimistically update the state in HA UI
            if rgb_color := kwargs.get(ATTR_RGB_COLOR):
                self._attr_rgb_color = rgb_color
            elif rgbw_color := kwargs.get(ATTR_RGBW_COLOR):
                self._attr_rgbw_color = rgbw_color
            
            self.async_write_ha_state()
        else:
            # Non-color changes (effects, brightness, on/off) are sent immediately
            await self._execute_turn_on(kwargs)

    @refresh_system
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await await_or_reraise(self.dev.turn_off())
