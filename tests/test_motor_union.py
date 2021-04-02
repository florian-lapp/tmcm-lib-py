from tests.environment import instance as environment
from tmcm_lib import MotorUnion

import unittest

class TestMotor(unittest.TestCase) :

    @classmethod
    def setUpClass(cls) :
        cls.__module = environment.module
        cls.__motor_union = MotorUnion(environment.module, environment.MOTOR_NUMBERS)

    def test_module(self) :
        self.assertIs(self.__motor_union.module, self.__module)

    def test_motors(self) :
        self.assertEqual(self.__motor_union.motors, environment.motors)

    def test_position(self) :
        self.assertEqual(self.__motor_union.position, tuple(0 for _ in self.__motor_union.motors))
        position = tuple(100 * motor.number for motor in self.__motor_union.motors)
        self.__motor_union.position = position
        self.assertEqual(self.__motor_union.position, position)

    def test_velocity(self) :
        self.assertEqual(
            self.__motor_union.velocity,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def test_acceleration(self) :
        self.assertEqual(
            self.__motor_union.acceleration,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def test_moving(self) :
        self.assertFalse(self.__motor_union.moving)

    def test_move_to_right(self) :
        position_target = tuple(
            +environment.MOTOR_STEPS * motor.microstep_resolution
            for motor in self.__motor_union.motors
        )
        self.__motor_union.move_to(position_target)
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocity,
            tuple(0.0 for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.acceleration,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def test_move_to_right_no_wait(self) :
        position_before = tuple(0 for _ in self.__motor_union.motors)
        position_target = tuple(
            +environment.MOTOR_STEPS * motor.microstep_resolution
            for motor in self.__motor_union.motors
        )
        overshoots = tuple(False for _ in self.__motor_union.motors)
        self.__motor_union.move_to(position_target, False)
        moving = True
        while moving :
            position = self.__motor_union.position
            velocity = self.__motor_union.velocity
            for position_before_scalar, position_scalar, velocity_scalar, overshoot in zip(
                position_before, position, velocity, overshoots
            ) :
                if overshoot :
                    self.assertLessEqual(position_scalar, position_before_scalar)
                else :
                    self.assertGreaterEqual(position_scalar, position_before_scalar)
                if not self.__motor_union.moving :
                    moving = False
                    break
                if overshoot is False and velocity_scalar < 0.0 :
                    overshoot = True
                if overshoot :
                    self.assertLess(velocity_scalar, 0.0)
                else :
                    self.assertGreater(velocity_scalar, 0.0)
            position_before = position
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocity,
            tuple(0.0 for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.acceleration,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def test_move_to_left(self) :
        position_target = tuple(
            -environment.MOTOR_STEPS * motor.microstep_resolution
            for motor in self.__motor_union.motors
        )
        self.__motor_union.move_to(position_target)
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocity,
            tuple(0.0 for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.acceleration,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def test_move_to_left_no_wait(self) :
        position_before = tuple(0 for _ in self.__motor_union.motors)
        position_target = tuple(
            -environment.MOTOR_STEPS * motor.microstep_resolution
            for motor in self.__motor_union.motors
        )
        overshoots = tuple(False for _ in self.__motor_union.motors)
        self.__motor_union.move_to(position_target, False)
        moving = True
        while moving :
            position = self.__motor_union.position
            velocity = self.__motor_union.velocity
            for position_before_scalar, position_scalar, velocity_scalar, overshoot in zip(
                position_before, position, velocity, overshoots
            ) :
                if overshoot :
                    self.assertGreaterEqual(position_scalar, position_before_scalar)
                else :
                    self.assertLessEqual(position_scalar, position_before_scalar)
                if not self.__motor_union.moving :
                    moving = False
                    break
                if overshoot is False and velocity_scalar > 0.0 :
                    overshoot = True
                if overshoot :
                    self.assertGreater(velocity_scalar, 0.0)
                else :
                    self.assertLess(velocity_scalar, 0.0)
            position_before = position
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocity,
            tuple(0.0 for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.acceleration,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def tearDown(self) :
        environment.reset()