from tests.environment import instance as environment
from tmcm_lib import Motor
from tmcm_lib import Direction

import unittest

class TestMotor(unittest.TestCase) :

    # Decorator.
    def subtest_motor(function) :
        def function_decorated(self) :
            for (motor_number, motor) in enumerate(self.__motors) :
                with self.subTest(motor_number) :
                    function(self, motor)
        return function_decorated

    @classmethod
    def setUpClass(cls) :
        cls.__module = environment.module
        cls.__motors = environment.motors

    @subtest_motor
    def test_module(self, motor : Motor) :
        self.assertIs(motor.module, self.__module)

    def test_number(self) :
        for (number, motor) in enumerate(self.__motors) :
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
    def test_current_standby(self, motor: Motor) :
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
        import math
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
        import math
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

    @subtest_motor
    def test_position(self, motor : Motor) :
        self.assertEqual(motor.position, 0)

    @subtest_motor
    def test_velocity(self, motor : Motor) :
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))

    @subtest_motor
    def test_acceleration(self, motor : Motor) :
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_moving(self, motor : Motor) :
        self.assertFalse(motor.moving)

    @subtest_motor
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
            (velocity_magnitude, velocity_direction) = motor.velocity
            if not motor.moving :
                break
            self.assertGreater(velocity_magnitude, 0.0)
            if overshoot is False and velocity_direction == Direction.LEFT :
                overshoot = True
            if overshoot :
                self.assertEqual(velocity_direction, Direction.LEFT)
            else :
                self.assertEqual(velocity_direction, Direction.RIGHT)
        self.assertFalse(motor.moving)
        self.assertEqual(motor.position, position_target)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_move_to_left_no_wait(self, motor: Motor) :
        position_before = 0
        position_target = -environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_to(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertLessEqual(position, position_before)
            position_before = position
            (velocity_magnitude, velocity_direction) = motor.velocity
            if not motor.moving :
                break
            self.assertGreater(velocity_magnitude, 0.0)
            if overshoot is False and velocity_direction == Direction.RIGHT :
                overshoot = True
            if overshoot :
                self.assertEqual(velocity_direction, Direction.RIGHT)
            else :
                self.assertEqual(velocity_direction, Direction.LEFT)
        self.assertFalse(motor.moving)
        self.assertEqual(motor.position, position_target)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_move_by_right_no_wait(self, motor: Motor) :
        position_before = 0
        position_target = +environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_by(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertGreaterEqual(position, position_before)
            position_before = position
            (velocity_magnitude, velocity_direction) = motor.velocity
            if not motor.moving :
                break
            self.assertGreater(velocity_magnitude, 0.0)
            if overshoot is False and velocity_direction == Direction.LEFT :
                overshoot = True
            if overshoot :
                self.assertEqual(velocity_direction, Direction.LEFT)
            else :
                self.assertEqual(velocity_direction, Direction.RIGHT)
        self.assertFalse(motor.moving)
        self.assertEqual(motor.position, position_target)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_move_by_left_no_wait(self, motor: Motor) :
        self.assertEqual(motor._position_actual_get(), 0)
        position_before = 0
        position_target = -environment.MOTOR_STEPS * motor.microstep_resolution
        overshoot = False
        motor.move_by(position_target, False)
        while True :
            position = motor.position
            if overshoot is False :
                self.assertLessEqual(position, position_before)
            position_before = position
            (velocity_magnitude, velocity_direction) = motor.velocity
            if not motor.moving :
                break
            self.assertGreater(velocity_magnitude, 0.0)
            if overshoot is False and velocity_direction == Direction.RIGHT :
                overshoot = True
            if overshoot :
                self.assertEqual(velocity_direction, Direction.RIGHT)
            else :
                self.assertEqual(velocity_direction, Direction.LEFT)
        self.assertFalse(motor.moving)
        self.assertEqual(motor.position, position_target)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_move_right(self, motor : Motor) :
        position_before = 0
        velocity_magnitude_before = 0
        motor.move_right(False)
        while True :
            self.assertTrue(motor.moving)
            position = motor.position
            acceleration = motor.acceleration
            (velocity_magnitude, velocity_direction) = motor.velocity
            self.assertGreaterEqual(position, position_before)
            self.assertGreaterEqual(velocity_magnitude, velocity_magnitude_before)
            self.assertEqual(velocity_direction, Direction.RIGHT)
            position_before = position
            velocity_magnitude_before = velocity_magnitude
            if velocity_magnitude == motor.velocity_moving :
                break
            self.assertEqual(acceleration, motor.acceleration_moving)
        self.assertTrue(motor.moving)
        self.assertEqual(motor.velocity, (motor.velocity_moving, Direction.RIGHT))
        motor.stop(False)
        # Expects no overshoot.
        while True :
            acceleration = motor.acceleration
            (velocity_magnitude, velocity_direction) = motor.velocity
            position = motor.position
            moving = motor.moving
            if moving :
                self.assertEqual(velocity_direction, Direction.RIGHT)
                self.assertEqual(acceleration, -motor.acceleration_moving)
            self.assertLessEqual(velocity_magnitude, velocity_magnitude_before)
            self.assertGreaterEqual(position, position_before)
            velocity_magnitude_before = velocity_magnitude
            position_before = position
            if not moving :
                break
        self.assertFalse(motor.moving)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_move_left(self, motor: Motor) :
        position_before = 0
        velocity_magnitude_before = 0
        motor.move_left(False)
        while True :
            self.assertTrue(motor.moving)
            position = motor.position
            acceleration = motor.acceleration
            (velocity_magnitude, velocity_direction) = motor.velocity
            self.assertLessEqual(position, position_before)
            self.assertGreaterEqual(velocity_magnitude, velocity_magnitude_before)
            self.assertEqual(velocity_direction, Direction.LEFT)
            position_before = position
            velocity_magnitude_before = velocity_magnitude
            if velocity_magnitude == motor.velocity_moving :
                break
            self.assertEqual(acceleration, -motor.acceleration_moving)
        self.assertTrue(motor.moving)
        self.assertEqual(motor.velocity, (motor.velocity_moving, Direction.LEFT))
        motor.stop(False)
        # Expects no overshoot.
        while True :
            acceleration = motor.acceleration
            (velocity_magnitude, velocity_direction) = motor.velocity
            position = motor.position
            moving = motor.moving
            if moving :
                self.assertEqual(velocity_direction, Direction.LEFT)
                self.assertEqual(acceleration, motor.acceleration_moving)
            self.assertLessEqual(velocity_magnitude, velocity_magnitude_before)
            self.assertLessEqual(position, position_before)
            velocity_magnitude_before = velocity_magnitude
            position_before = position
            if not moving :
                break
        self.assertFalse(motor.moving)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_stop_right(self, motor : Motor) :
        motor.move_right(False)
        while motor.velocity[0] < motor.velocity_moving :
            pass
        motor.stop()
        self.assertFalse(motor.moving)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    @subtest_motor
    def test_stop_left(self, motor: Motor) :
        motor.move_left(False)
        while motor.velocity[0] < motor.velocity_moving :
            pass
        motor.stop()
        self.assertFalse(motor.moving)
        self.assertEqual(motor.velocity, (0.0, Direction.NONE))
        self.assertEqual(motor.acceleration, 0.0)

    def tearDown(self) :
        environment.reset()