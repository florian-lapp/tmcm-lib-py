from tests.environment import instance as environment
from tmcm_lib import Motor

import unittest
import math

class TestMotor(unittest.TestCase) :

    # Decorator: Calls the decorated function once per motor.
    def subtest_motor(function) :
        def function_decorated(self) :
            for motor_number, motor in enumerate(self.__motors) :
                with self.subTest(motor_number) :
                    function(self, motor)
                    environment.reset()
        return function_decorated

    # Decorator: Calls the decorated function once per motor and direction.
    def subtest_motor_direction(function) :
        def function_decorated(self) :
            for motor_number, motor in enumerate(self.__motors) :
                for direction_reversed in [False, True] :
                    with self.subTest(f'{motor_number, direction_reversed}') :
                        motor.direction_reversed = direction_reversed
                        function(self, motor)
                        environment.reset()
        return function_decorated

    @classmethod
    def setUpClass(cls) :
        cls.__module = environment.module
        cls.__motors = environment.motors

    @subtest_motor
    def test_module(self, motor : Motor) :
        self.assertIs(motor.module, self.__module)

    def test_number(self) :
        for number, motor in enumerate(self.__motors) :
            with self.subTest(number) :
                self.assertIs(motor.number, number)

    @subtest_motor
    def test_current_moving(self, motor : Motor) :
        motor.current_moving = self.__module.motor_current_minimum
        self.assertEqual(motor.current_moving, self.__module.motor_current_minimum)
        motor.current_moving = self.__module.motor_current_maximum
        self.assertEqual(motor.current_moving, self.__module.motor_current_maximum)
        motor.current_moving = environment.MOTOR_CURRENT_MOVING
        self.assertEqual(motor.current_moving, environment.MOTOR_CURRENT_MOVING)
        with self.assertRaises(ValueError) :
            motor.current_moving = self.__module.motor_current_minimum - 1
        self.assertEqual(motor.current_moving, environment.MOTOR_CURRENT_MOVING)
        with self.assertRaises(ValueError) :
            motor.current_moving = self.__module.motor_current_maximum + 1
        self.assertEqual(motor.current_moving, environment.MOTOR_CURRENT_MOVING)

    @subtest_motor
    def test_current_standby(self, motor : Motor) :
        motor.current_standby = self.__module.motor_current_minimum
        self.assertEqual(motor.current_standby, self.__module.motor_current_minimum)
        motor.current_standby = self.__module.motor_current_maximum
        self.assertEqual(motor.current_standby, self.__module.motor_current_maximum)
        motor.current_standby = environment.MOTOR_CURRENT_STANDBY
        self.assertEqual(motor.current_standby, environment.MOTOR_CURRENT_STANDBY)
        with self.assertRaises(ValueError) :
            motor.current_standby = self.__module.motor_current_minimum - 1
        self.assertEqual(motor.current_standby, environment.MOTOR_CURRENT_STANDBY)
        with self.assertRaises(ValueError) :
            motor.current_standby = self.__module.motor_current_maximum + 1
        self.assertEqual(motor.current_standby, environment.MOTOR_CURRENT_STANDBY)

    @subtest_motor
    def test_direction_reversed(self, motor : Motor) :
        self.assertFalse(motor.direction_reversed)
        switch_limit_left = motor.switch_limit_left
        switch_limit_right = motor.switch_limit_right
        motor.position = +1234
        motor.direction_reversed = True
        self.assertTrue(motor.direction_reversed)
        self.assertIs(motor.switch_limit_left, switch_limit_right)
        self.assertIs(motor.switch_limit_right, switch_limit_left)
        self.assertEqual(motor.position, -1234)
        motor.direction_reversed = False
        self.assertFalse(motor.direction_reversed)
        self.assertIs(motor.switch_limit_left, switch_limit_left)
        self.assertIs(motor.switch_limit_right, switch_limit_right)
        self.assertEqual(motor.position, +1234)

    @subtest_motor
    def test_microstep_resolution(self, motor : Motor) :
        velocity_moving = motor.velocity_moving
        for microstep_resolution in Motor.MICROSTEP_RESOLUTIONS :
            motor.microstep_resolution = microstep_resolution
            self.assertEqual(motor.microstep_resolution, microstep_resolution)
            self.assertEqual(motor.velocity_moving, velocity_moving)
        with self.assertRaises(ValueError) :
            motor.microstep_resolution = 0
        with self.assertRaises(ValueError) :
            motor.microstep_resolution = 512

    @subtest_motor
    def test_velocity_moving_extrema(self, motor : Motor) :
        frequency_minimum = motor.module.motor_frequency_minimum
        frequency_maximum = motor.module.motor_frequency_maximum
        for microstep_resolution in Motor.MICROSTEP_RESOLUTIONS :
            motor.microstep_resolution = microstep_resolution
            velocity_minimum = frequency_minimum / microstep_resolution
            velocity_maximum = frequency_maximum / microstep_resolution
            self.assertEqual(motor.velocity_minimum, velocity_minimum)
            self.assertEqual(motor.velocity_maximum, velocity_maximum)

    @subtest_motor
    def test_velocity_moving(self, motor : Motor) :
        for microstep_resolution in Motor.MICROSTEP_RESOLUTIONS :
            motor.microstep_resolution = microstep_resolution
            with self.assertRaises(ValueError) :
                motor.velocity_moving = math.nextafter(motor.velocity_minimum, -math.inf)
            with self.assertRaises(ValueError) :
                motor.velocity_moving = math.nextafter(motor.velocity_maximum, +math.inf)
            motor.velocity_moving = motor.velocity_minimum
            self.assertEqual(motor.velocity_moving, motor.velocity_minimum)
            motor.velocity_moving = motor.velocity_maximum
            self.assertEqual(motor.velocity_moving, motor.velocity_maximum)

    @subtest_motor
    def test_acceleration_moving(self, motor : Motor) :
        for microstep_resolution in Motor.MICROSTEP_RESOLUTIONS :
            motor.microstep_resolution = microstep_resolution
            for pulse_divisor_exponent in range(0, 13 + 1) :
                velocity_moving = 250_000 / (microstep_resolution * 2 ** pulse_divisor_exponent)
                motor.velocity_moving = velocity_moving
                with self.assertRaises(ValueError) :
                    motor.acceleration_moving = math.nextafter(motor.acceleration_minimum, -math.inf)
                with self.assertRaises(ValueError) :
                    motor.acceleration_moving = math.nextafter(motor.acceleration_maximum, +math.inf)
                motor.acceleration_moving = motor.acceleration_minimum
                self.assertEqual(motor.acceleration_moving, motor.acceleration_minimum)
                motor.acceleration_moving = motor.acceleration_maximum
                self.assertEqual(motor.acceleration_moving, motor.acceleration_maximum)

    @subtest_motor_direction
    def test_position(self, motor : Motor) :
        self.assertEqual(motor.position, 0)
        position = 100 * motor.number
        motor.position = position
        self.assertEqual(motor.position, position)

    @subtest_motor_direction
    def test_velocity(self, motor : Motor) :
        self.assertEqual(motor.velocity, 0.0)

    @subtest_motor_direction
    def test_acceleration(self, motor : Motor) :
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_moving(self, motor : Motor) :
        self.assertFalse(motor.moving)

    @subtest_motor_direction
    def test_move_to_right(self, motor : Motor) :
        position_target = +environment.MOTOR_STEPS * motor.microstep_resolution
        motor.move_to(+position_target)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_to_right_no_wait(self, motor : Motor) :
        position_before = 0
        position_target = +environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_to(position_target, False)
        while True :
            position = motor.position
            if overshoot :
                self.assertLessEqual(position, position_before)
            else :
                self.assertGreaterEqual(position, position_before)
            position_before = position
            velocity = motor.velocity
            if not motor.moving :
                break
            self.assertNotEqual(velocity, 0.0)
            if overshoot is False and velocity < 0.0 :
                overshoot = True
            if overshoot :
                self.assertLess(velocity, 0.0)
            else :
                self.assertGreater(velocity, 0.0)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_to_left(self, motor : Motor) :
        position_target = -environment.MOTOR_STEPS * motor.microstep_resolution
        motor.move_to(position_target)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_to_left_no_wait(self, motor : Motor) :
        position_before = 0
        position_target = -environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_to(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertLessEqual(position, position_before)
            position_before = position
            velocity = motor.velocity
            if not motor.moving :
                break
            self.assertNotEqual(velocity, 0.0)
            if overshoot is False and velocity > 0.0 :
                overshoot = True
            if overshoot :
                self.assertGreater(velocity, 0.0)
            else :
                self.assertLess(velocity, 0.0)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_by_right_no_wait(self, motor : Motor) :
        position_before = 0
        position_target = +environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_by(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertGreaterEqual(position, position_before)
            position_before = position
            velocity = motor.velocity
            if not motor.moving :
                break
            if overshoot is False and velocity < 0.0 :
                overshoot = True
            if overshoot :
                self.assertLess(velocity, 0.0)
            else :
                self.assertGreater(velocity, 0.0)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_by_left_no_wait(self, motor : Motor) :
        position_before = 0
        position_target = -environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_by(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertLessEqual(position, position_before)
            position_before = position
            velocity = motor.velocity
            if not motor.moving :
                break
            if overshoot is False and velocity > 0.0 :
                overshoot = True
            if overshoot :
                self.assertGreater(velocity, 0.0)
            else :
                self.assertLess(velocity, 0.0)
        self.assertEqual(motor.position, position_target)
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_right(self, motor : Motor) :
        position_before = 0
        velocity_before = 0.0
        motor.move_right(False)
        while True :
            self.assertTrue(motor.moving)
            position = motor.position
            acceleration = motor.acceleration
            velocity = motor.velocity
            self.assertGreaterEqual(position, position_before)
            self.assertGreaterEqual(velocity, velocity_before)
            self.assertGreater(velocity, 0.0)
            position_before = position
            velocity_before = velocity
            if +velocity == motor.velocity_moving :
                break
            self.assertEqual(acceleration, motor.acceleration_moving)
        self.assertTrue(motor.moving)
        self.assertEqual(motor.velocity, +motor.velocity_moving)
        motor.stop(False)
        # Expects no overshoot.
        while True :
            acceleration = motor.acceleration
            velocity = motor.velocity
            position = motor.position
            moving = motor.moving
            if moving :
                self.assertGreater(velocity, 0.0)
                self.assertEqual(acceleration, -motor.acceleration_moving)
            self.assertLessEqual(velocity, velocity_before)
            self.assertGreaterEqual(position, position_before)
            velocity_before = velocity
            position_before = position
            if not moving :
                break
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_move_left(self, motor : Motor) :
        position_before = 0
        velocity_before = 0.0
        motor.move_left(False)
        while True :
            self.assertTrue(motor.moving)
            position = motor.position
            acceleration = motor.acceleration
            velocity = motor.velocity
            self.assertLessEqual(position, position_before)
            self.assertLessEqual(velocity, velocity_before)
            self.assertLess(velocity, 0.0)
            position_before = position
            velocity_before = velocity
            if -velocity == motor.velocity_moving :
                break
            self.assertEqual(acceleration, -motor.acceleration_moving)
        self.assertTrue(motor.moving)
        self.assertEqual(motor.velocity, -motor.velocity_moving)
        motor.stop(False)
        # Expects no overshoot.
        while True :
            acceleration = motor.acceleration
            velocity = motor.velocity
            position = motor.position
            moving = motor.moving
            if moving :
                self.assertLess(velocity, 0.0)
                self.assertEqual(acceleration, motor.acceleration_moving)
            self.assertGreaterEqual(velocity, velocity_before)
            self.assertLessEqual(position, position_before)
            velocity_before = velocity
            position_before = position
            if not moving :
                break
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_stop_right(self, motor : Motor) :
        motor.move_right(False)
        while motor.velocity < +motor.velocity_moving :
            pass
        motor.stop()
        self.__test_stopped(motor)

    @subtest_motor_direction
    def test_stop_left(self, motor : Motor) :
        motor.move_left(False)
        while motor.velocity > -motor.velocity_moving :
            pass
        motor.stop()
        self.__test_stopped(motor)

    def tearDown(self) :
        environment.reset()

    def __test_stopped(self, motor : Motor) :
        self.assertFalse(motor.moving)
        self.assertEqual(motor.velocity, 0.0)
        self.assertEqual(motor.acceleration, 0.0)