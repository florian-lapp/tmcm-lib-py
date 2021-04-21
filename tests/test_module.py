import time

from tests.environment import instance as environment
from tmcm_lib import Module, AddressException, ModelException

import unittest
import typing

class TestModule(unittest.TestCase) :

    CLASS : typing.Type[Module]
    MODEL_NUMBER : int
    FIRMWARE_VERSION : (int, int)
    MOTOR_COUNT : int
    MOTOR_CURRENT_MINIMUM : int
    MOTOR_CURRENT_MAXIMUM : int
    MOTOR_FREQUENCY_MINIMUM : float
    MOTOR_FREQUENCY_MAXIMUM : float
    COORDINATE_COUNT : int

    def test_identify(self) :
        self.assertEqual(Module.identify(environment.port, address = environment.ADDRESS), (
            self.MODEL_NUMBER,
            self.FIRMWARE_VERSION,
        ))

    def test_construct(self) :
        with self.assertRaises(ValueError) :
            Module.construct(environment.port, address = 0)
        with self.assertRaises(ValueError) :
            Module.construct(environment.port, address = 256)
        with self.assertRaises(AddressException) :
            Module.construct(
                environment.port, address = (
                    environment.ADDRESS + 1
                    if environment.ADDRESS < 128 else
                    environment.ADDRESS - 1
                )
            )
        with self.assertRaises(ModelException) :
            Module.construct(
                environment.port,
                address = environment.ADDRESS,
                model_number = -1
            )
        module = Module.construct(
            environment.port, address = environment.ADDRESS, model_number = self.MODEL_NUMBER
        )
        self.assertIsInstance(module, Module)
        self.assertEqual(module.address, environment.ADDRESS)
        self.assertEqual(module.model_number, self.MODEL_NUMBER)

    def test_address(self) :
        self.assertEqual(self.__module.address, environment.ADDRESS)

    def test_model_number(self) :
        self.assertEqual(self.__module.model_number, self.MODEL_NUMBER)

    def test_firmware_version(self) :
        self.assertEqual(self.__module.firmware_version, self.FIRMWARE_VERSION)

    def test_heartbeat_timeout(self) :
        self.assertEqual(self.__module.heartbeat_timeout, environment.HEARTBEAT_TIMEOUT)
        for heartbeat_timeout in [-1, Module.HEARTBEAT_TIMEOUT_LIMIT + 1] :
            with self.assertRaises(ValueError) :
                self.__module.heartbeat_timeout = heartbeat_timeout
        motors = self.__module.motors
        for motor in motors :
            motor.move_right(False)
        self.__module.heartbeat_timeout = 250
        time.sleep(0.5)
        self.assertTrue(all(motor.moving for motor in motors))

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
        if cls.MODEL_NUMBER != module.model_number :
            raise unittest.SkipTest('Module model different')
        cls.__module = module

    def tearDown(self) :
        environment.reset()