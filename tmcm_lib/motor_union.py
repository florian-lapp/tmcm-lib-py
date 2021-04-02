from .module import Module
from .motor import Motor
from .exceptions import *

import functools
import operator
import time
import typing

class MotorUnion :
    """Set of motors of a module that move simultaneously."""

    def __init__(
        self,
        module : Module,
        motor_numbers : typing.Iterable[int],
        coordinate_number : int = 0
    ) -> None :
        """
        Constructs a motor union of motors of the given module and motor numbers.

        The coordinate number specifies the coordinate to temporarily store the position to move the
        motors to.
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
    def motors(self) -> typing.Sequence[Motor] :
        """Gets the motors of the motor union."""
        return self.__motors

    @property
    def velocity(self) -> typing.Sequence[float] :
        """Gets the velocity of the motor union as a vector in units of fullsteps per second."""
        return tuple(motor.velocity for motor in self.__motors)

    @property
    def acceleration(self) -> typing.Sequence[float] :
        """
        Gets the acceleration of the motor union as a vector in units of fullsteps per square
        second.
        """
        return tuple(motor.acceleration for motor in self.__motors)

    @property
    def position(self) -> typing.Sequence[int] :
        """Gets the position of the motor union as a vector in units of microsteps."""
        return tuple(motor.position for motor in self.__motors)

    @position.setter
    def position(self, position : typing.Iterable[int]) -> None :
        """
        Sets the position of the motor union as a vector in units of microsteps.

        Note: The position can not be set while any motor of the motor union is moving.
        """
        if self.moving :
            raise StateException()
        for motor, position in zip(self.__motors, position) :
            motor.position = position

    @property
    def moving(self) -> bool :
        """Gets if the motor union is moving."""
        return any(motor.moving for motor in self.__motors)

    def move_to(
        self,
        position : typing.Iterable[int],
        wait_while_moving : bool = True,
        *,
        synchronously : bool = True
    ) -> None :
        """
        Moves the motor union synchronously or asynchronously to the given position as a vector in
        units of microsteps.
        """
        self.__coordinate_set(position)
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

    def __coordinate_set(self, position : typing.Iterable[int]) -> None :
        """Sets the position of the coordinate in units of microsteps."""
        for motor, position in zip(self.__motors, position) :
            motor.coordinates[self.__coordinate_number] = position