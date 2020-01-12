"""The tests for the Ring binary sensor platform."""
from asyncio import run_coroutine_threadsafe
import unittest
from unittest.mock import patch

import requests_mock

from homeassistant.components import ring as base_ring
from homeassistant.components.ring import binary_sensor as ring

from tests.common import get_test_home_assistant, load_fixture, mock_storage
from tests.components.ring.test_init import ATTRIBUTION, VALID_CONFIG


class TestRingBinarySensorSetup(unittest.TestCase):
    """Test the Ring Binary Sensor platform."""

    DEVICES = []

    def add_entities(self, devices, action):
        """Mock add devices."""
        for device in devices:
            self.DEVICES.append(device)

    def setUp(self):
        """Initialize values for this testcase class."""
        self.hass = get_test_home_assistant()
        self.config = {
            "username": "foo",
            "password": "bar",
            "monitored_conditions": ["ding", "motion"],
        }

    def tearDown(self):
        """Stop everything that was started."""
        self.hass.stop()

    @requests_mock.Mocker()
    def test_binary_sensor(self, mock):
        """Test the Ring sensor class and methods."""
        mock.post(
            "https://oauth.ring.com/oauth/token", text=load_fixture("ring_oauth.json")
        )
        mock.post(
            "https://api.ring.com/clients_api/session",
            text=load_fixture("ring_session.json"),
        )
        mock.get(
            "https://api.ring.com/clients_api/ring_devices",
            text=load_fixture("ring_devices.json"),
        )
        mock.get(
            "https://api.ring.com/clients_api/dings/active",
            text=load_fixture("ring_ding_active.json"),
        )
        mock.get(
            "https://api.ring.com/clients_api/doorbots/987652/health",
            text=load_fixture("ring_doorboot_health_attrs.json"),
        )
        mock.get(
            "https://api.ring.com/clients_api/chimes/999999/health",
            text=load_fixture("ring_chime_health_attrs.json"),
        )

        with mock_storage(), patch("homeassistant.components.ring.PLATFORMS", []):
            run_coroutine_threadsafe(
                base_ring.async_setup(self.hass, VALID_CONFIG), self.hass.loop
            ).result()
            run_coroutine_threadsafe(
                self.hass.async_block_till_done(), self.hass.loop
            ).result()
            run_coroutine_threadsafe(
                ring.async_setup_entry(self.hass, None, self.add_entities),
                self.hass.loop,
            ).result()

        for device in self.DEVICES:
            device.update()
            if device.name == "Front Door Ding":
                assert "on" == device.state
                assert "America/New_York" == device.device_state_attributes["timezone"]
            elif device.name == "Front Door Motion":
                assert "off" == device.state
                assert "motion" == device.device_class

            assert device.entity_picture is None
            assert ATTRIBUTION == device.device_state_attributes["attribution"]
