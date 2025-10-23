from __future__ import annotations

import copy
from typing import cast
from unittest.mock import patch

import pytest
import respx
import respx.router

from iaqualink.systems.iaqua.device import (
    IAQUA_TEMP_CELSIUS_HIGH,
    IAQUA_TEMP_CELSIUS_LOW,
    IAQUA_TEMP_FAHRENHEIT_HIGH,
    IAQUA_TEMP_FAHRENHEIT_LOW,
    IaquaAuxSwitch,
    IaquaBinarySensor,
    IaquaColorLight,
    IaquaDevice,
    IaquaDimmableLight,
    IaquaHeatPump,
    IaquaICLLight,
    IaquaLightSwitch,
    IaquaSensor,
    IaquaSwitch,
    IaquaThermostat,
)
from iaqualink.systems.iaqua.system import IaquaSystem

from ...base import dotstar, resp_200
from ...base_test_device import (
    TestBaseBinarySensor,
    TestBaseDevice,
    TestBaseLight,
    TestBaseSensor,
    TestBaseSwitch,
    TestBaseThermostat,
)


class TestIaquaDevice(TestBaseDevice):
    def setUp(self) -> None:
        super().setUp()

        data = {"serial_number": "SN123456", "device_type": "iaqua"}
        self.system = IaquaSystem(self.client, data=data)

        data = {"name": "device", "state": "42"}
        self.sut = IaquaDevice(self.system, data)
        self.sut_class = IaquaDevice

    def test_equal(self) -> None:
        assert self.sut == self.sut

    def test_not_equal(self) -> None:
        obj2 = copy.deepcopy(self.sut)
        obj2.data["name"] = "device_2"
        assert self.sut != obj2

    def test_property_name(self) -> None:
        assert self.sut.name == self.sut.data["name"]

    def test_property_state(self) -> None:
        assert self.sut.state == self.sut.data["state"]

    def test_not_equal_different_type(self) -> None:
        assert (self.sut == {}) is False

    def test_property_manufacturer(self) -> None:
        assert self.sut.manufacturer == "Jandy"

    def test_property_model(self) -> None:
        assert self.sut.model == self.sut_class.__name__.replace("Iaqua", "")


class TestIaquaSensor(TestIaquaDevice, TestBaseSensor):
    def setUp(self) -> None:
        super().setUp()

        data = {"name": "orp", "state": "42"}
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaSensor


class TestIaquaBinarySensor(TestIaquaSensor, TestBaseBinarySensor):
    def setUp(self) -> None:
        super().setUp()

        data = {"name": "freeze_protection", "state": "0"}
        self.sut_class = IaquaBinarySensor
        self.sut = IaquaDevice.from_data(self.system, data)

    def test_property_is_on_false(self) -> None:
        self.sut.data["state"] = "0"
        super().test_property_is_on_false()
        assert self.sut.is_on is False

    def test_property_is_on_true(self) -> None:
        self.sut.data["state"] = "1"
        super().test_property_is_on_true()
        assert self.sut.is_on is True


class TestIaquaSwitch(TestIaquaBinarySensor, TestBaseSwitch):
    def setUp(self) -> None:
        super().setUp()

        data = {
            "name": "pool_heater",
            "state": "0",
        }
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaSwitch

    async def test_turn_on(self) -> None:
        self.sut.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_on()

    async def test_turn_on_noop(self) -> None:
        self.sut.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_on_noop()

    async def test_turn_off(self) -> None:
        self.sut.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_off()

    async def test_turn_off_noop(self) -> None:
        self.sut.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_off_noop()


class TestIaquaAuxSwitch(TestIaquaSwitch, TestBaseSwitch):
    def setUp(self) -> None:
        super().setUp()

        data = {
            "name": "aux_1",
            "state": "0",
            "aux": "1",
            "type": "0",
            "label": "CLEANER",
        }
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaAuxSwitch

    async def test_turn_on(self) -> None:
        self.sut.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_on()

    async def test_turn_on_noop(self) -> None:
        self.sut.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_on_noop()

    async def test_turn_off(self) -> None:
        self.sut.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_off()

    async def test_turn_off_noop(self) -> None:
        self.sut.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_off_noop()


class TestIaquaLightSwitch(TestIaquaAuxSwitch, TestBaseLight):
    def setUp(self) -> None:
        super().setUp()

        # system.set_aux = async_noop
        data = {
            "name": "aux_1",
            "state": "0",
            "aux": "1",
            "label": "POOL LIGHT",
            "type": "0",
        }
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaLightSwitch

    def test_property_brightness(self) -> None:
        assert self.sut.brightness is None

    def test_property_effect(self) -> None:
        assert self.sut.effect is None


class TestIaquaDimmableLight(TestIaquaAuxSwitch, TestBaseLight):
    def setUp(self) -> None:
        super().setUp()

        data = {
            "name": "aux_1",
            "state": "1",
            "aux": "1",
            "subtype": "25",
            "type": "1",
            "label": "SPA LIGHT",
        }
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaDimmableLight

    def test_property_name(self) -> None:
        super().test_property_name()
        assert self.sut.name == "aux_1"

    def test_property_label(self) -> None:
        super().test_property_label()
        assert self.sut.label == "Spa Light"

    def test_property_state(self) -> None:
        super().test_property_state()
        assert self.sut.state == "1"

    def test_property_is_on_false(self) -> None:
        self.sut.data["state"] = "0"
        self.sut.data["subtype"] = "0"
        super().test_property_is_on_false()
        assert self.sut.is_on is False

    def test_property_is_on_true(self) -> None:
        self.sut.data["state"] = "1"
        self.sut.data["subtype"] = "100"
        super().test_property_is_on_true()
        assert self.sut.is_on is True

    async def test_turn_on(self) -> None:
        self.sut.data["state"] = "0"
        self.sut.data["subtype"] = "0"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_on()

    async def test_turn_on_noop(self) -> None:
        self.sut.data["state"] = "1"
        self.sut.data["subtype"] = "25"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_on_noop()

    async def test_turn_off(self) -> None:
        self.sut.data["state"] = "1"
        self.sut.data["subtype"] = "100"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_off()

    async def test_turn_off_noop(self) -> None:
        self.sut.data["state"] = "0"
        self.sut.data["subtype"] = "0"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_off_noop()

    def test_property_supports_brightness(self) -> None:
        super().test_property_supports_brightness()
        assert self.sut.supports_brightness is True

    def test_property_supports_effect(self) -> None:
        super().test_property_supports_effect()
        assert self.sut.supports_effect is False

    async def test_set_brightness_75(self) -> None:
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_set_brightness_75()


class TestIaquaColorLight(TestIaquaAuxSwitch, TestBaseLight):
    def setUp(self) -> None:
        super().setUp()

        # system.set_light = async_noop
        data = {
            "name": "aux_1",
            "aux": "1",
            "state": "0",
            "type": "2",
            "subtype": "5",
            "label": "POOL LIGHT",
        }
        self.sut = IaquaDevice.from_data(self.system, data)
        self.sut_class = IaquaColorLight

    def test_property_name(self) -> None:
        super().test_property_name()
        assert self.sut.name == "aux_1"

    def test_property_label(self) -> None:
        super().test_property_label()
        assert self.sut.label == "Pool Light"

    def test_property_state(self) -> None:
        super().test_property_state()

    def test_property_manufacturer(self) -> None:
        assert self.sut.manufacturer == "Pentair"

    def test_property_model(self) -> None:
        assert self.sut.model == "Intellibrite Light"

    def test_property_supports_brightness(self) -> None:
        super().test_property_supports_brightness()
        assert self.sut.supports_brightness is False

    def test_property_supports_effect(self) -> None:
        super().test_property_supports_effect()
        assert self.sut.supports_effect is True

    async def test_turn_off(self) -> None:
        self.sut.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_off()
        # data = {"aux": "1", "light": "0", "subtype": "5"}

    async def test_turn_on(self) -> None:
        self.sut.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_turn_on()
        # data = {"aux": "1", "light": "1", "subtype": "5"}

    async def test_set_effect_by_id_4(self) -> None:
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_set_effect_by_id_4()
        # data = {"aux": "1", "light": "2", "subtype": "5"}

    async def test_set_effect_by_id_invalid_27(self) -> None:
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_set_effect_by_id_invalid_27()

    async def test_set_effect_by_name_off(self) -> None:
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_set_effect_by_name_off()

    async def test_set_effect_by_name_invalid_amaranth(self) -> None:
        with patch.object(self.sut.system, "_parse_devices_response"):
            await super().test_set_effect_by_name_invalid_amaranth()


class TestIaquaThermostat(TestIaquaDevice, TestBaseThermostat):
    def setUp(self) -> None:
        super().setUp()

        pool_set_point = {"name": "pool_set_point", "state": "86"}
        self.pool_set_point = cast(
            IaquaThermostat, IaquaDevice.from_data(self.system, pool_set_point)
        )

        pool_temp = {"name": "pool_temp", "state": "65"}
        self.pool_temp = IaquaDevice.from_data(self.system, pool_temp)

        pool_heater = {"name": "pool_heater", "state": "0"}
        self.pool_heater = IaquaDevice.from_data(self.system, pool_heater)

        spa_set_point = {"name": "spa_set_point", "state": "102"}
        self.spa_set_point = cast(
            IaquaThermostat, IaquaDevice.from_data(self.system, spa_set_point)
        )

        devices = [
            self.pool_set_point,
            self.pool_heater,
            self.pool_temp,
        ]
        self.system.devices = {x.name: x for x in devices}

        self.sut = self.pool_set_point
        self.sut_class = IaquaThermostat

    def test_property_label(self) -> None:
        assert self.sut.label == "Pool Set Point"

    def test_property_name(self) -> None:
        assert self.sut.name == "pool_set_point"

    def test_property_state(self) -> None:
        assert self.sut.state == "86"

    def test_property_is_on_true(self) -> None:
        self.pool_heater.data["state"] = "1"
        super().test_property_is_on_true()

    def test_property_is_on_false(self) -> None:
        self.pool_heater.data["state"] = "0"
        super().test_property_is_on_false()

    def test_property_unit(self) -> None:
        self.sut.system.temp_unit = "F"
        super().test_property_unit()

    def test_property_min_temperature_f(self) -> None:
        self.sut.system.temp_unit = "F"
        super().test_property_min_temperature_c()
        assert self.sut.min_temperature == IAQUA_TEMP_FAHRENHEIT_LOW

    def test_property_min_temperature_c(self) -> None:
        self.sut.system.temp_unit = "C"
        super().test_property_min_temperature_f()
        assert self.sut.min_temperature == IAQUA_TEMP_CELSIUS_LOW

    def test_property_max_temperature_f(self) -> None:
        self.sut.system.temp_unit = "F"
        super().test_property_max_temperature_f()
        assert self.sut.max_temperature == IAQUA_TEMP_FAHRENHEIT_HIGH

    def test_property_max_temperature_c(self) -> None:
        self.sut.system.temp_unit = "C"
        super().test_property_max_temperature_c()
        assert self.sut.max_temperature == IAQUA_TEMP_CELSIUS_HIGH

    def test_property_current_temperature(self) -> None:
        super().test_property_current_temperature()
        assert self.sut.current_temperature == "65"

    def test_property_target_temperature(self) -> None:
        super().test_property_target_temperature()
        assert self.sut.target_temperature == "86"

    async def test_turn_on(self) -> None:
        self.pool_heater.data["state"] = "0"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_on()
        assert len(self.respx_calls) == 1
        url = str(self.respx_calls[0].request.url)
        assert "set_pool_heater" in url

    async def test_turn_on_noop(self) -> None:
        self.pool_heater.data["state"] = "1"
        await super().test_turn_on_noop()

    async def test_turn_off(self) -> None:
        self.pool_heater.data["state"] = "1"
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_turn_off()
        assert len(self.respx_calls) == 1
        url = str(self.respx_calls[0].request.url)
        assert "set_pool_heater" in url

    async def test_turn_off_noop(self) -> None:
        self.pool_heater.data["state"] = "0"
        await super().test_turn_off_noop()

    async def test_set_temperature_86f(self) -> None:
        self.sut.system.devices["spa_set_point"] = self.spa_set_point
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_set_temperature_86f()
        assert len(self.respx_calls) == 1
        url = str(self.respx_calls[0].request.url)
        assert "temp1=102" in url
        assert "temp2=86" in url

    async def test_set_temperature_30c(self) -> None:
        with patch.object(self.sut.system, "_parse_home_response"):
            await super().test_set_temperature_30c()
        assert len(self.respx_calls) == 1
        url = str(self.respx_calls[0].request.url)
        assert "temp1=30" in url
        assert "temp2" not in url

    async def test_temp_name_spa_present(self) -> None:
        self.sut.system.devices["spa_set_point"] = self.spa_set_point
        assert self.spa_set_point._temperature == "temp1"
        assert self.pool_set_point._temperature == "temp2"

    async def test_temp_name_no_spa(self) -> None:
        assert self.pool_set_point._temperature == "temp1"


class TestIaquaICLLight(TestBaseLight):
    def setUp(self) -> None:
        super().setUp()

        data = {"serial_number": "SN123456", "device_type": "iaqua"}
        self.system = IaquaSystem(self.client, data=data)

        # ICL light data based on the example payload
        data = {
            "name": "icl_zone_1",
            "zoneId": 1,
            "zoneName": "Pool lights",
            "zoneStatus": "on",
            "zoneColor": "0",
            "zoneColorVal": "off",
            "dim_level": "75",
            "red_val": "128",
            "green_val": "64",
            "blue_val": "192",
            "white_val": "32",
        }
        self.sut = IaquaICLLight(self.system, data)
        self.sut_class = IaquaICLLight

    def test_equal(self) -> None:
        assert self.sut == self.sut

    def test_not_equal(self) -> None:
        obj2 = copy.deepcopy(self.sut)
        obj2.data["zoneId"] = 2
        assert self.sut != obj2

    def test_not_equal_different_type(self) -> None:
        data = {"name": "pool_pump", "state": "1"}
        obj2 = IaquaSwitch(self.system, data)
        assert self.sut != obj2

    def test_property_zone_id(self) -> None:
        assert self.sut.zone_id == 1

    def test_property_zone_name(self) -> None:
        assert self.sut.zone_name == "Pool lights"

    def test_property_name(self) -> None:
        assert self.sut.name == "icl_zone_1"

    def test_property_label(self) -> None:
        assert self.sut.label == "Icl Zone 1"

    def test_property_state(self) -> None:
        assert self.sut.data["zoneStatus"] == "on"

    def test_property_manufacturer(self) -> None:
        assert self.sut.manufacturer == "Jandy"

    def test_property_model(self) -> None:
        assert self.sut.model == "ICLLight"

    def test_property_is_on_true(self) -> None:
        assert self.sut.is_on is True

    def test_property_is_on_false(self) -> None:
        self.sut.data["zoneStatus"] = "off"
        assert self.sut.is_on is False

    def test_property_brightness(self) -> None:
        assert self.sut.brightness == 75

    def test_property_brightness_none(self) -> None:
        self.sut.data["dim_level"] = None
        assert self.sut.brightness is None

    def test_property_rgb_color(self) -> None:
        assert self.sut.rgb_color == (128, 64, 192)

    def test_property_rgb_color_invalid(self) -> None:
        self.sut.data["red_val"] = "invalid"
        assert self.sut.rgb_color is None

    def test_property_white_value(self) -> None:
        assert self.sut.white_value == 32

    def test_property_white_value_none(self) -> None:
        self.sut.data["white_val"] = None
        assert self.sut.white_value is None

    def test_property_effect(self) -> None:
        assert self.sut.effect == "0"

    def test_property_supports_brightness(self) -> None:
        assert self.sut.supports_brightness is True

    def test_property_supports_rgb_color(self) -> None:
        assert self.sut.supports_rgb_color is True

    def test_property_supports_white_value(self) -> None:
        assert self.sut.supports_white_value is True

    # Override base test methods that don't apply to ICL lights
    def test_property_supported_effects(self) -> None:
        pytest.skip("ICL lights use RGB color, not effect presets")

    @respx.mock
    async def test_set_brightness_75(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Override to add proper mocking
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_brightness(75)
        assert len(respx_mock.calls) > 0

    @respx.mock
    async def test_set_brightness_invalid_89(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Override to add proper mocking
        pytest.skip("ICL lights accept any 0-100 brightness value")

    @respx.mock
    async def test_set_effect_by_id_4(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        pytest.skip("ICL lights use RGB color, not effect IDs")

    @respx.mock
    async def test_set_effect_by_id_invalid_27(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        pytest.skip("ICL lights use RGB color, not effect IDs")

    @respx.mock
    async def test_set_effect_by_name_invalid_amaranth(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        pytest.skip("ICL lights use RGB color, not effect names")

    @respx.mock
    async def test_set_effect_by_name_off(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        pytest.skip("ICL lights use RGB color, not effect names")

    @respx.mock
    async def test_turn_on(self, respx_mock: respx.router.MockRouter) -> None:
        self.sut.data["zoneStatus"] = "off"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.turn_on()
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_icl_light" in url
        assert "zoneId=1" in url
        assert "zoneStatus=on" in url

    @respx.mock
    async def test_turn_on_noop(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Already on
        self.sut.data["zoneStatus"] = "on"
        respx_mock.route(dotstar).mock(resp_200)
        await self.sut.turn_on()
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_turn_off(self, respx_mock: respx.router.MockRouter) -> None:
        self.sut.data["zoneStatus"] = "on"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.turn_off()
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_icl_light" in url
        assert "zoneId=1" in url
        assert "zoneStatus=off" in url

    @respx.mock
    async def test_turn_off_noop(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Already off
        self.sut.data["zoneStatus"] = "off"
        respx_mock.route(dotstar).mock(resp_200)
        await self.sut.turn_off()
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_set_brightness(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_brightness(50)
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_icl_light" in url
        assert "zoneId=1" in url
        assert "dim_level=50" in url

    @respx.mock
    async def test_set_brightness_invalid(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with pytest.raises(Exception):
            await self.sut.set_brightness(150)  # Invalid > 100
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_set_rgb_color(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_rgb_color(255, 128, 64)
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_icl_light" in url
        assert "zoneId=1" in url
        assert "red_val=255" in url
        assert "green_val=128" in url
        assert "blue_val=64" in url

    @respx.mock
    async def test_set_rgb_color_invalid(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with pytest.raises(Exception):
            await self.sut.set_rgb_color(300, 128, 64)  # Invalid > 255
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_set_white_value(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_white_value(200)
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_icl_light" in url
        assert "zoneId=1" in url
        assert "white_val=200" in url

    @respx.mock
    async def test_set_white_value_invalid(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with pytest.raises(Exception):
            await self.sut.set_white_value(300)  # Invalid > 255
        assert len(respx_mock.calls) == 0


class TestIaquaHeatPump(TestBaseThermostat):
    def setUp(self) -> None:
        super().setUp()

        data = {"serial_number": "SN123456", "device_type": "iaqua"}
        self.system = IaquaSystem(self.client, data=data)
        self.system.temp_unit = "F"

        # Create mock pool temperature and setpoint devices
        pool_temp_data = {"name": "pool_temp", "state": "78"}
        self.pool_temp = IaquaSensor(self.system, pool_temp_data)

        pool_set_point_data = {"name": "pool_set_point", "state": "80"}
        self.pool_set_point = IaquaThermostat(self.system, pool_set_point_data)

        pool_chill_data = {"name": "pool_chill_set_point", "state": "95"}
        self.pool_chill = IaquaThermostat(self.system, pool_chill_data)

        self.system.devices = {
            "pool_temp": self.pool_temp,
            "pool_set_point": self.pool_set_point,
            "pool_chill_set_point": self.pool_chill,
        }

        # Heat pump data based on the example payload
        data = {
            "name": "heatpump_info",
            "isheatpumpPresent": True,
            "heatpumpstatus": "on",
            "isChillAvailable": True,
            "heatpumpmode": "heat",
            "heatpumptype": "4-wired",
        }
        self.sut = IaquaHeatPump(self.system, data)
        self.sut_class = IaquaHeatPump

    def test_equal(self) -> None:
        assert self.sut == self.sut

    def test_not_equal(self) -> None:
        obj2 = copy.deepcopy(self.sut)
        obj2.data["heatpumptype"] = "2-wired"
        assert self.sut != obj2

    def test_not_equal_different_type(self) -> None:
        data = {"name": "pool_pump", "state": "1"}
        obj2 = IaquaSwitch(self.system, data)
        assert self.sut != obj2

    def test_property_name(self) -> None:
        assert self.sut.name == "heatpump_info"

    def test_property_label(self) -> None:
        assert self.sut.label == "Heatpump Info"

    def test_property_manufacturer(self) -> None:
        assert self.sut.manufacturer == "Jandy"

    def test_property_model(self) -> None:
        assert self.sut.model == "HeatPump"

    def test_property_is_present(self) -> None:
        assert self.sut.is_present is True

    def test_property_is_present_false(self) -> None:
        self.sut.data["isheatpumpPresent"] = False
        assert self.sut.is_present is False

    def test_property_is_on_true(self) -> None:
        self.sut.data["heatpumpstatus"] = "on"
        assert self.sut.is_on is True

    def test_property_is_on_false(self) -> None:
        self.sut.data["heatpumpstatus"] = "off"
        assert self.sut.is_on is False

    def test_property_mode(self) -> None:
        assert self.sut.mode == "heat"

    def test_property_mode_cool(self) -> None:
        self.sut.data["heatpumpmode"] = "cool"
        assert self.sut.mode == "cool"

    def test_property_supports_cooling(self) -> None:
        assert self.sut.supports_cooling is True

    def test_property_supports_cooling_false(self) -> None:
        self.sut.data["isChillAvailable"] = False
        assert self.sut.supports_cooling is False

    def test_property_heat_pump_type(self) -> None:
        assert self.sut.heat_pump_type == "4-wired"

    def test_property_unit(self) -> None:
        assert self.sut.unit == "F"

    def test_property_current_temperature(self) -> None:
        assert self.sut.current_temperature == "78"

    def test_property_target_temperature_heat_mode(self) -> None:
        self.sut.data["heatpumpmode"] = "heat"
        assert self.sut.target_temperature == "80"

    def test_property_target_temperature_cool_mode(self) -> None:
        self.sut.data["heatpumpmode"] = "cool"
        assert self.sut.target_temperature == "95"

    def test_property_min_temperature_f(self) -> None:
        self.system.temp_unit = "F"
        assert self.sut.min_temperature == IAQUA_TEMP_FAHRENHEIT_LOW

    def test_property_min_temperature_c(self) -> None:
        self.system.temp_unit = "C"
        assert self.sut.min_temperature == IAQUA_TEMP_CELSIUS_LOW

    def test_property_max_temperature_f(self) -> None:
        self.system.temp_unit = "F"
        assert self.sut.max_temperature == IAQUA_TEMP_FAHRENHEIT_HIGH

    def test_property_max_temperature_c(self) -> None:
        self.system.temp_unit = "C"
        assert self.sut.max_temperature == IAQUA_TEMP_CELSIUS_HIGH

    # Override base test that doesn't apply to heat pump data structure
    def test_property_state(self) -> None:
        # Heat pump uses heatpumpstatus instead of state
        assert "heatpumpstatus" in self.sut.data

    @respx.mock
    async def test_set_temperature_86f(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Override to add proper mocking
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_temperature(86)
        assert len(respx_mock.calls) > 0

    @respx.mock
    async def test_set_temperature_30c(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Override to add proper mocking
        self.system.temp_unit = "C"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_temperature(30)
        assert len(respx_mock.calls) > 0

    @respx.mock
    async def test_turn_on(self, respx_mock: respx.router.MockRouter) -> None:
        self.sut.data["heatpumpstatus"] = "off"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.turn_on()
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_heatpump" in url
        assert "heatpumpmode=heat" in url

    @respx.mock
    async def test_turn_on_noop(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Already on
        self.sut.data["heatpumpstatus"] = "on"
        respx_mock.route(dotstar).mock(resp_200)
        await self.sut.turn_on()
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_turn_off(self, respx_mock: respx.router.MockRouter) -> None:
        self.sut.data["heatpumpstatus"] = "on"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.turn_off()
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_heatpump" in url
        assert "heatpumpmode=off" in url

    @respx.mock
    async def test_turn_off_noop(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        # Already off
        self.sut.data["heatpumpstatus"] = "off"
        respx_mock.route(dotstar).mock(resp_200)
        await self.sut.turn_off()
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_set_mode_heat(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_mode("heat")
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_heatpump" in url
        assert "heatpumpmode=heat" in url

    @respx.mock
    async def test_set_mode_cool(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_mode("cool")
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_heatpump" in url
        assert "heatpumpmode=cool" in url

    @respx.mock
    async def test_set_mode_off(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_mode("off")
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_heatpump" in url
        assert "heatpumpmode=off" in url

    @respx.mock
    async def test_set_mode_invalid(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        respx_mock.route(dotstar).mock(resp_200)
        with pytest.raises(Exception):
            await self.sut.set_mode("invalid_mode")
        assert len(respx_mock.calls) == 0

    @respx.mock
    async def test_set_temperature_heat_mode(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        self.sut.data["heatpumpmode"] = "heat"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_temperature(85)
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_temps" in url
        assert "temp2=85" in url

    @respx.mock
    async def test_set_temperature_cool_mode(
        self, respx_mock: respx.router.MockRouter
    ) -> None:
        self.sut.data["heatpumpmode"] = "cool"
        respx_mock.route(dotstar).mock(resp_200)
        with patch.object(self.sut.system, "_parse_home_response"):
            await self.sut.set_temperature(90)
        assert len(respx_mock.calls) == 1
        url = str(respx_mock.calls[0].request.url)
        assert "set_temps" in url
        assert "temp_chill=90" in url
