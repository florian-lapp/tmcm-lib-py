from tests.environment import instance as environment
from tmcm_lib import MotorUnion
from tmcm_lib import Direction

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

    def test_velocities(self) :
        self.assertEqual(
            self.__motor_union.velocities,
            tuple((0.0, Direction.NONE) for _ in self.__motor_union.motors)
        )

    def test_accelerations(self) :
        self.assertEqual(
            self.__motor_union.accelerations,
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
            self.__motor_union.velocities,
            tuple((0.0, Direction.NONE) for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.accelerations,
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
            velocities = self.__motor_union.velocities
            for (position_before, position, velocity, overshoot) in zip(
                position_before,
                position,
                velocities,
                overshoots
            ) :
                if overshoot :
                    self.assertLessEqual(position, position_before)
                else :
                    self.assertGreaterEqual(position, position_before)
                position_before = position
                (velocity_magnitude, velocity_direction) = velocity
                if not self.__motor_union.moving :
                    moving = False
                    break
                self.assertGreater(velocity_magnitude, 0.0)
                if overshoot is False and velocity_direction == Direction.LEFT :
                    overshoot = True
                if overshoot :
                    self.assertEqual(velocity_direction, Direction.LEFT)
                else :
                    self.assertEqual(velocity_direction, Direction.RIGHT)
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocities,
            tuple((0.0, Direction.NONE) for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.accelerations,
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
            self.__motor_union.velocities,
            tuple((0.0, Direction.NONE) for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.accelerations,
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
            velocities = self.__motor_union.velocities
            for (position_before, position, velocity, overshoot) in zip(
                position_before,
                position,
                velocities,
                overshoots
            ) :
                if overshoot :
                    self.assertGreaterEqual(position, position_before)
                else :
                    self.assertLessEqual(position, position_before)
                position_before = position
                (velocity_magnitude, velocity_direction) = velocity
                if not self.__motor_union.moving :
                    moving = False
                    break
                self.assertGreater(velocity_magnitude, 0.0)
                if overshoot is False and velocity_direction == Direction.RIGHT :
                    overshoot = True
                if overshoot :
                    self.assertEqual(velocity_direction, Direction.RIGHT)
                else :
                    self.assertEqual(velocity_direction, Direction.LEFT)
        self.assertFalse(self.__motor_union.moving)
        self.assertEqual(self.__motor_union.position, position_target)
        self.assertEqual(
            self.__motor_union.velocities,
            tuple((0.0, Direction.NONE) for _ in self.__motor_union.motors)
        )
        self.assertEqual(
            self.__motor_union.accelerations,
            tuple(0.0 for _ in self.__motor_union.motors)
        )

    def tearDown(self) :
        environment.reset()