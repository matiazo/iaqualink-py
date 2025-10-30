from __future__ import annotations

import logging
import secrets
import time
from typing import TYPE_CHECKING

from iaqualink.const import MIN_SECS_TO_REFRESH
from iaqualink.exception import (
    AqualinkDeviceNotSupported,
    AqualinkServiceException,
    AqualinkSystemOfflineException,
)
from iaqualink.system import AqualinkSystem
from iaqualink.systems.iaqua.device import IaquaDevice

if TYPE_CHECKING:
    import httpx

    from iaqualink.client import AqualinkClient
    from iaqualink.typing import Payload

IAQUA_SESSION_URL = "https://p-api.iaqualink.net/v1/mobile/session.json"
IAQUA_V2_COMMAND_URL = "https://prm.iaqualink.net/v2/webtouch/command"

IAQUA_COMMAND_GET_DEVICES = "get_devices"
IAQUA_COMMAND_GET_HOME = "get_home"
IAQUA_COMMAND_GET_ONETOUCH = "get_onetouch"

IAQUA_COMMAND_SET_AUX = "set_aux"
IAQUA_COMMAND_SET_LIGHT = "set_light"
IAQUA_COMMAND_ONOFF_ICLZONE = "onoff_iclzone"
IAQUA_COMMAND_SET_ICLZONE_COLOR = "set_iclzone_color"
IAQUA_COMMAND_DEFINE_ICLZONE_CUSTOMCOLOR = "define_iclzone_customcolor"
IAQUA_COMMAND_SET_HEATPUMP = "set_heatpump"
IAQUA_COMMAND_SET_POOL_HEATER = "set_pool_heater"
IAQUA_COMMAND_SET_POOL_PUMP = "set_pool_pump"
IAQUA_COMMAND_SET_SOLAR_HEATER = "set_solar_heater"
IAQUA_COMMAND_SET_SPA_HEATER = "set_spa_heater"
IAQUA_COMMAND_SET_SPA_PUMP = "set_spa_pump"
IAQUA_COMMAND_SET_TEMPS = "set_temps"


LOGGER = logging.getLogger("iaqualink")


class IaquaSystem(AqualinkSystem):
    NAME = "iaqua"

    def __init__(self, aqualink: AqualinkClient, data: Payload):
        super().__init__(aqualink, data)

        self.temp_unit: str = ""
        self.last_refresh: int = 0

    def __repr__(self) -> str:
        attrs = ["name", "serial", "data"]
        attrs = [f"{i}={getattr(self, i)!r}" for i in attrs]
        return f"{self.__class__.__name__}({' '.join(attrs)})"

    async def _send_session_request(
        self,
        command: str,
        params: Payload | None = None,
    ) -> httpx.Response:
        if not params:
            params = {}

        params.update(
            {
                "actionID": "command",
                "command": command,
                "serial": self.serial,
                "sessionID": self.aqualink.client_id,
            }
        )
        params_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{IAQUA_SESSION_URL}?{params_str}"
        return await self.aqualink.send_request(url)

    async def set_icl_light(self, data: Payload) -> None:
        """Control ICL lights using v1 API commands from GitHub issue #39."""
        LOGGER.debug(f"Setting ICL light with data: {data}")
        zone_id = data.get("zoneId", "1")
        
        # Determine which command to use based on data
        if "on_off_action" in data:
            # Turn on/off: command=onoff_iclzone&zone_id=1&on_off_action=off
            command = IAQUA_COMMAND_ONOFF_ICLZONE
            params = {
                "zone_id": zone_id,
                "on_off_action": data["on_off_action"]
            }
        elif "color_id" in data:
            # Set preset color: command=set_iclzone_color&zone_id=1&color_id=2&dim_level=100
            command = IAQUA_COMMAND_SET_ICLZONE_COLOR
            params = {
                "zone_id": zone_id,
                "color_id": data["color_id"],
                "dim_level": data.get("dim_level", "100")
            }
        elif "red_val" in data:
            # Set custom color: command=define_iclzone_customcolor&zone_id=1&red_val=255&green_val=110&blue_val=145&white_val=0
            command = IAQUA_COMMAND_DEFINE_ICLZONE_CUSTOMCOLOR
            params = {
                "zone_id": zone_id,
                "red_val": data["red_val"],
                "green_val": data["green_val"],
                "blue_val": data["blue_val"],
                "white_val": data.get("white_val", "0")
            }
        else:
            LOGGER.error(f"Unknown ICL command data: {data}")
            return
        
        LOGGER.debug(f"Using command {command} with params: {params}")
        r = await self._send_session_request(command, params)
        LOGGER.debug(f"ICL light response status: {r.status_code}")
        
        # Parse response to update device states
        response_data = r.json()
        if not response_data:
            LOGGER.debug("ICL light command returned empty response - command completed")
            return
        elif "home_screen" in response_data:
            LOGGER.debug("Parsing home_screen response")
            self._parse_home_response(r)
        elif "devices_screen" in response_data:
            LOGGER.debug("Parsing devices_screen response")
            self._parse_devices_response(r)
        else:
            LOGGER.debug(f"Unexpected ICL response format: {response_data}")

    async def _send_home_screen_request(self) -> httpx.Response:
        return await self._send_session_request(IAQUA_COMMAND_GET_HOME)

    async def _send_devices_screen_request(self) -> httpx.Response:
        return await self._send_session_request(IAQUA_COMMAND_GET_DEVICES)

    async def update(self) -> None:
        # Be nice to Aqualink servers since we rely on polling.
        now = int(time.time())
        delta = now - self.last_refresh
        if delta < MIN_SECS_TO_REFRESH:
            LOGGER.debug(f"Only {delta}s since last refresh.")
            return

        try:
            r1 = await self._send_home_screen_request()
            r2 = await self._send_devices_screen_request()
        except AqualinkServiceException:
            self.online = None
            raise

        try:
            self._parse_home_response(r1)
            self._parse_devices_response(r2)
        except AqualinkSystemOfflineException:
            self.online = False
            raise

        self.online = True
        self.last_refresh = int(time.time())

    def _parse_home_response(self, response: httpx.Response) -> None:
        data = response.json()

        LOGGER.debug(f"Home response: {data}")

        if data["home_screen"][0]["status"] == "Offline":
            LOGGER.warning(f"Status for system {self.serial} is Offline.")
            raise AqualinkSystemOfflineException

        self.temp_unit = data["home_screen"][3]["temp_scale"]

        # Make the data a bit flatter.
        devices = {}
        for x in data["home_screen"][4:]:
            name = next(iter(x.keys()))
            state = next(iter(x.values()))
            
            # Handle special device types that were previously ignored
            if name == "icl_custom_color_info" and isinstance(state, list):
                # Handle ICL custom color info
                for color_info in state:
                    if isinstance(color_info, dict):
                        zone_id = color_info.get("zoneId", 1)
                        device_name = f"icl_zone_{zone_id}"
                        # Merge with existing zone data if present
                        if device_name in devices:
                            devices[device_name].update(color_info)
                        else:
                            color_info["name"] = device_name
                            devices[device_name] = color_info
                continue
            elif name == "heatpump_info" and isinstance(state, dict):
                # Handle heat pump info
                state["name"] = name
                devices[name] = state
                continue
            elif name == "swc_info" and isinstance(state, dict):
                # Handle salt water chlorinator info
                # Only create device if actually present
                if state.get("isswcPresent", False):
                    state["name"] = name
                    devices[name] = state
                continue
            
            attrs = {"name": name, "state": state}
            devices.update({name: attrs})

        for k, v in devices.items():
            if k in self.devices:
                for dk, dv in v.items():
                    self.devices[k].data[dk] = dv
            else:
                try:
                    self.devices[k] = IaquaDevice.from_data(self, v)
                except AqualinkDeviceNotSupported as e:
                    LOGGER.debug("Device found was ignored: %s", e)

    def _parse_devices_response(self, response: httpx.Response) -> None:
        data = response.json()

        LOGGER.debug(f"Devices response: {data}")

        if data["devices_screen"][0]["status"] == "Offline":
            LOGGER.warning(f"Status for system {self.serial} is Offline.")
            raise AqualinkSystemOfflineException

        # Handle ICL info list if present (at root level of devices_screen)
        if "icl_info_list" in data:
            icl_list = data["icl_info_list"]
            LOGGER.debug(f"Found icl_info_list at root level: {icl_list}")
            if isinstance(icl_list, list):
                for icl_info in icl_list:
                    if isinstance(icl_info, dict):
                        zone_id = icl_info.get("zoneId", 1)
                        device_name = f"icl_zone_{zone_id}"
                        LOGGER.debug(f"Processing ICL zone {zone_id}, device_name={device_name}, exists={device_name in self.devices}")
                        # Merge with existing zone data from home response
                        if device_name in self.devices:
                            # Update existing device data
                            LOGGER.debug(f"Updating existing ICL device {device_name} with {icl_info}")
                            for dk, dv in icl_info.items():
                                self.devices[device_name].data[dk] = dv
                            LOGGER.debug(f"After update, device data: {self.devices[device_name].data}")
                        else:
                            # Create new device (shouldn't happen, but handle it)
                            LOGGER.debug(f"Creating new ICL device {device_name}")
                            icl_info["name"] = device_name
                            try:
                                self.devices[device_name] = IaquaDevice.from_data(self, icl_info)
                            except AqualinkDeviceNotSupported as e:
                                LOGGER.debug("ICL device found was ignored: %s", e)

        # Make the data a bit flatter.
        devices = {}
        LOGGER.debug(f"Starting aux device processing, current self.devices keys: {list(self.devices.keys())}")
        for x in data["devices_screen"][3:]:
            aux = next(iter(x.keys()))
            # Skip icl_info_list if it appears here (it shouldn't, but just in case)
            if aux == "icl_info_list":
                continue
            
            attrs = {"aux": aux.replace("aux_", ""), "name": aux}
            for y in next(iter(x.values())):
                attrs.update(y)
            devices.update({aux: attrs})

        for k, v in devices.items():
            if k in self.devices:
                for dk, dv in v.items():
                    self.devices[k].data[dk] = dv
            else:
                try:
                    self.devices[k] = IaquaDevice.from_data(self, v)
                except AqualinkDeviceNotSupported as e:
                    LOGGER.info("Device found was ignored: %s", e)

    async def set_switch(self, command: str) -> None:
        r = await self._send_session_request(command)
        self._parse_home_response(r)

    async def set_temps(self, temps: Payload) -> None:
        # I'm not proud of this. If you read this, please submit a PR to make it better.
        # We need to pass the temperatures for both pool and spa (if present) in the same request.
        # Set args to current target temperatures and override with the request payload.
        args = {}
        i = 1
        if "spa_set_point" in self.devices:
            args[f"temp{i}"] = self.devices["spa_set_point"].target_temperature
            i += 1
        args[f"temp{i}"] = self.devices["pool_set_point"].target_temperature
        args.update(temps)

        r = await self._send_session_request(IAQUA_COMMAND_SET_TEMPS, args)
        self._parse_home_response(r)

    async def set_aux(self, aux: str) -> None:
        aux = IAQUA_COMMAND_SET_AUX + "_" + aux.replace("aux_", "")
        r = await self._send_session_request(aux)
        self._parse_devices_response(r)

    async def set_light(self, data: Payload) -> None:
        LOGGER.debug(f"Setting light with data: {data}")
        # Use v1 API for all lights (regular and ICL)
        r = await self._send_session_request(IAQUA_COMMAND_SET_LIGHT, data)
        LOGGER.debug(f"Set light response status: {r.status_code}")
        
        # ICL lights may return empty response, home_screen, or devices_screen
        response_data = r.json()
        if not response_data:
            # Empty response - command succeeded but no data returned
            LOGGER.debug("Set light command returned empty response - command completed")
            return
        elif "home_screen" in response_data:
            LOGGER.debug("Parsing home_screen response")
            self._parse_home_response(r)
        elif "devices_screen" in response_data:
            LOGGER.debug("Parsing devices_screen response")
            self._parse_devices_response(r)
        else:
            LOGGER.debug(f"Unexpected set_light response format: {response_data}")

    async def set_heatpump(self, data: Payload) -> None:
        r = await self._send_session_request(IAQUA_COMMAND_SET_HEATPUMP, data)
        self._parse_home_response(r)
