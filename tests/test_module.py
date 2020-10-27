from tests.environment import instance as environment
from tmcm_lib import Module

import unittest
import typing

class TestModule(unittest.TestCase) :

    CLASS : typing.Type[Module]
    IDENTITY : int
    FIRMWARE_VERSION : (int, int)
    MOTOR_COUNT : int
    MOTOR_CURRENT_MINIMUM : int
    MOTOR_CURRENT_MAXIMUM : int
    MOTOR_FREQUENCY_MINIMUM : float
    MOTOR_FREQUENCY_MAXIMUM : float
    COORDINATE_COUNT : int

    def test_identify(self) :
        self.assertEqual(Module.identify(environment.port), (
            self.IDENTITY,
            self.FIRMWARE_VERSION
        ))

    def test_construct(self) :
        module = Module.construct(environment.port)
        self.assertIsInstance(module, Module)
        self.assertEqual(module.identity, self.IDENTITY)

    def test_identity(self) :
        self.assertEqual(self.__module.identity, self.IDENTITY)

    def test_firmware_version(self) :
        self.assertEqual(self.__module.firmware_version, self.FIRMWARE_VERSION)

    def test_supply_voltage(self) :
        supply_voltage = self.__module.supply_voltage
        self.assertGreaterEqual(
            supply_voltage,
            environment.SUPPLY_VOLTAGE - environment.SUPPLY_VOLTAGE_TOLERANCE
        )
        self.assertLessEqual(
            supply_voltage,
            environment.SUPPLY_VOLTAGE + environment.SUPPLY_VOLTAGE_TOLERANCE
        )

    def test_motor_count(self) :
        self.assertEqual(self.__module.motor_count, self.MOTOR_COUNT)
        self.assertEqual(len(self.__module.motors), self.MOTOR_COUNT)

    def test_motor_current_extrema(self) :
        self.assertEqual(self.__module.motor_current_minimum, self.MOTOR_CURRENT_MINIMUM)
        self.assertEqual(self.__module.motor_current_maximum, self.MOTOR_CURRENT_MAXIMUM)

    def test_motor_frequency_extrema(self) :
        self.assertEqual(self.__module.motor_frequency_minimum, self.MOTOR_FREQUENCY_MINIMUM)
        self.assertEqual(self.__module.motor_frequency_maximum, self.MOTOR_FREQUENCY_MAXIMUM)

    def test_coordinate_count(self) :
        self.assertEqual(self.__module.coordinate_count, self.COORDINATE_COUNT)
        self.assertEqual(len(self.__module.coordinates), self.COORDINATE_COUNT)

    @classmethod
    def setUpClass(cls) -> None :
        if cls == TestModule :
            raise unittest.SkipTest('Generic test case')
        module = environment.module
        if cls.IDENTITY != module.identity :
            raise unittest.SkipTest('Module identity different')
        cls.__module = module