from .module import Module
from .motor import Motor
from .exceptions import *

import functools
import operator
import time
import typing

class MotorUnion :
    """Set of motors that move simultaneously."""

    def __init__(
        self,
        module : Module,
        motor_numbers : typing.Set[int],
        coordinate_number : int = 0
    ) -> None :
        """
        Creates a motor union of motors of the given module and motor numbers.

        The coordinate number specifies the coordinate to temporarily store the positions to move
        the motors to.
        """
        self.__module = module
        self.__motors = tuple(module.motors[motor_number] for motor_number in motor_numbers)
        self.__coordinate_number = coordinate_number
        self.__motor_numbers = functools.reduce(
            operator.ior,
            map(lambda motor_number: 2 ** motor_number, motor_numbers)
        )
        module.coordinates._number_verify(coordinate_number)

    @property
    def module(self) -> Module :
        """Gets the module of the motor union."""
        return self.__module

    @property
    def motors(self) -> typing.Tuple[Motor, ...] :
        """Gets the motors of the motor union."""
        return self.__motors

    @property
    def positions(self) -> typing.Tuple[int, ...] :
        """Gets the positions of the motor union in units of microsteps."""
        return tuple(motor.position for motor in self.__motors)

    @positions.setter
    def positions(self, value : typing.Iterable[int]) -> None :
        """
        Sets the positions of the motor union in units of microsteps.

        Note: The positions can not be set while any motor of the motor union is moving.
        """
        if self.moving :
            raise ExceptionState()
        for (motor, position) in zip(self.__motors, value) :
            motor.position = position

    @property
    def moving(self) -> bool :
        """Gets if the motor union is moving."""
        return any(motor.moving for motor in self.__motors)

    def move_to(
        self,
        positions : typing.Iterable[int],
        wait_while_moving : bool = True,
        *,
        synchronously : bool = True
    ) -> None :
        """
        Moves the motor union synchronously or asynchronously to the given positions in units of
        microsteps.
        """
        self.__coordinate_set(positions)
        for motor in self.__motors :
            motor._move_indicate(Motor._RampMode.POSITION)
        self.__module._motor_move_to_coordinate(
            self.__motor_numbers |
            (
                MotorUnion.__MOVE_SYNCHRONOUSLY if synchronously else
                MotorUnion.__MOVE_ASYNCHRONOUSLY
            ),
            self.__coordinate_number
        )
        if wait_while_moving :
            self.wait_while_moving()

    def stop(self, wait_while_moving : bool = True) -> None :
        for motor in self.__motors :
            motor.stop(False)
        if wait_while_moving :
            self.wait_while_moving()

    def wait_while_moving(self) -> None :
        """Waits while the motor union is moving."""
        while self.moving :
            time.sleep(Motor.MOVING_POLL_DELAY)

    __MOVE_SYNCHRONOUSLY = 0x40
    __MOVE_ASYNCHRONOUSLY = 0x80

    def __coordinate_set(self, positions : typing.Iterable[int]) -> None :
        """Sets the positions of the coordinate in units of microsteps."""
        for (motor, position) in zip(self.__motors, positions) :
            motor.coordinates[self.__coordinate_number] = position