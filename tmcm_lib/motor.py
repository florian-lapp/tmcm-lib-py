from .module import Module
from .switch import Switch
from .exceptions import *

import abc
import enum
import time
import typing

class Motor(abc.ABC) :
    """Motor of a module."""

    POSITION_MINIMUM = -2_147_483_648
    """Minimum position a motor can move to."""
    POSITION_MAXIMUM = +2_147_483_647
    """Maximum position a motor can move to."""
    DISTANCE_MINIMUM = -2_147_483_648
    """Minimum distance a motor can move by."""
    DISTANCE_MAXIMUM = +2_147_483_647
    """Maximum distance a motor can move by."""

    MICROSTEP_RESOLUTIONS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
    """Microstep resolutions a motor can have."""

    STANDBY_DELAY_MINIMUM = 10
    """Minimum standby delay a motor can have in units of milliseconds."""
    STANDBY_DELAY_MAXIMUM = 10 * 65_535
    """Maximum standby delay a motor can have in units of milliseconds."""

    FREEWHEELING_DELAY_DISABLED = 0
    """Freewheeling delay of a motor with disabled freewheeling."""
    FREEWHEELING_DELAY_MINIMUM = 10
    """Minimum freewheeling delay a motor can have in units of milliseconds."""
    FREEWHEELING_DELAY_MAXIMUM = 10 * 65_535
    """Maximum freewheeling delay a motor can have in units of milliseconds."""

    MOVING_POLL_DELAY = 0.05
    """Delay between moving polls while waiting in units of seconds."""

    @property
    def module(self) -> Module :
        """Gets the module of the motor."""
        return self.__module

    @property
    def number(self) -> int :
        """
        Gets the number of the motor.

        Values: [0, `module.motor_count`)
        """
        return self.__number

    @property
    def switch_limit_right(self) -> Switch :
        """Gets the right limit switch of the motor."""
        return self.__switch_limit_right

    @property
    def switch_limit_left(self) -> Switch :
        """Gets the left limit switch of the motor."""
        return self.__switch_limit_left

    @property
    def switch_home(self) -> Switch :
        """Gets the home switch of the motor."""
        return self.__switch_home

    @property
    def direction_reversed(self) -> bool :
        """Gets if the direction of the motor is reversed."""
        return self.__direction_sign < 0

    @direction_reversed.setter
    def direction_reversed(self, direction_reversed : bool) -> None :
        """Sets if the direction of the motor is reversed."""
        direction_sign = -1 if direction_reversed else +1
        if direction_sign == self.__direction_sign :
            return
        self.__switch_limit_right, self.__switch_limit_left = (
            self.__switch_limit_left, self.__switch_limit_right
        )
        self.__position *= -1
        self.__coordinates._revert()
        self.__direction_sign = direction_sign

    @property
    def current_moving(self) -> int :
        """
        Gets the moving current of the motor in units of milliamperes.

        Values: [`module.motor_current_minimum`, `module.motor_current_maximum`]
        """
        return self.__current_moving

    @current_moving.setter
    def current_moving(self, value : int) -> None :
        """
        Sets the moving current of the motor in units of milliamperes.

        Values: [`module.motor_current_minimum`, `module.motor_current_maximum`]

        :raises ValueError:
            Current invalid.

        Note: The value is rounded down to the next lower motor current step of the module.
        """
        value_internal = self.__module._motor_current_internal(value)
        if value_internal == self.__current_moving_internal :
            return
        self._current_moving_set(value_internal)
        self.__current_moving_internal = value_internal
        self.__current_moving = self.__module._motor_current_external(value_internal)

    @property
    def current_standby(self) -> int :
        """
        Gets the standby current of the motor in units of milliamperes.

        The standby current is used when the motor is not moving.

        Values: [`module.motor_current_minimum`, `module.motor_current_maximum`]
        """
        return self.__current_standby

    @current_standby.setter
    def current_standby(self, value : int) -> None :
        """
        Sets the standby current of the motor in units of milliamperes.

        Values: [`module.motor_current_minimum`, `module.motor_current_maximum`]

        :raises ValueError:
            Current invalid.

        Note: The value is rounded down to the next lower motor current step of the module.
        """
        value_internal = self.__module._motor_current_internal(value)
        if value_internal == self.__current_standby_internal :
            return
        self._current_standby_set(value_internal)
        self.__current_standby_internal = value_internal
        self.__current_standby = self.__module._motor_current_external(value_internal)

    @property
    def velocity_minimum(self) -> float :
        """Gets the minimum velocity of the motor in units of fullsteps per second."""
        return self.__velocity_minimum

    @property
    def velocity_maximum(self) -> float :
        """Gets the maximum velocity of the motor in units of fullsteps per second."""
        return self.__velocity_maximum

    @property
    def velocity_moving(self) -> float :
        """
        Gets the moving velocity of the motor in units of fullsteps per second.

        Values: [`velocity_minimum`, `velocity_maximum`]
        """
        return self.__velocity_moving

    @velocity_moving.setter
    def velocity_moving(self, value : float) -> None :
        """
        Sets the moving velocity of the motor in units of fullsteps per second.

        The moving velocity can not be set while the motor is moving.

        Values: [`velocity_minimum`, `velocity_maximum`]

        :raises StateException:
            Motor is moving.
        :raises ValueError:
            Velocity invalid.

        Note: The value is rounded down to the next lower motor velocity step of the module.

        Note: Changing the moving velocity sometimes moves the motor by one microstep.
        """
        if self.moving :
            raise StateException()
        if value < self.__velocity_minimum or value > self.__velocity_maximum :
            raise ValueError('Velocity invalid: Value exceeds limit.')
        if value == self.__velocity_moving :
            return
        self.__velocity_moving_set_external(value)
        self.__acceleration_extrema_update()

    @property
    def velocity(self) -> float :
        """
        Gets the velocity of the motor in units of fullsteps per second.

        A positive value indicates a moving in right direction.

        A negative value indicates a moving in left direction.

        Values: [`-velocity_moving`, `+velocity_moving`]
        """
        if not self.__moving :
            return 0.0
        return self.__velocity_actual_get_external()

    @property
    def acceleration_minimum(self) -> float :
        """Gets the minimum acceleration of the motor in units of fullsteps per square second."""
        return self.__acceleration_minimum

    @property
    def acceleration_maximum(self) -> float :
        """Gets the maximum acceleration of the motor in units of fullsteps per square second."""
        return self.__acceleration_maximum

    @property
    def acceleration_moving(self) -> float :
        """
        Gets the moving acceleration of the motor in units of fullsteps per square second.

        Values: [`acceleration_minimum`, `acceleration_maximum`]
        """
        return self.__direction_sign * self.__acceleration_moving

    @acceleration_moving.setter
    def acceleration_moving(self, value : float) -> None :
        """
        Sets the moving acceleration of the motor in units of of fullsteps per square second.

        The moving acceleration can not be set while the motor is moving.

        Values: [`acceleration_minimum`, `acceleration_maximum`]

        :raises StateException:
            Motor is moving.
        :raises ValueError:
            Acceleration invalid.

        Note: The value is rounded down to the next lower motor acceleration step of the module.
        """
        if self.moving :
            raise StateException()
        if value < self.__acceleration_minimum or value > self.__acceleration_maximum :
            raise ValueError('Acceleration invalid: Value exceeds limit.')
        if value == self.__acceleration_moving :
            return
        self.__acceleration_moving_set_external(value)

    @property
    def acceleration(self) -> float :
        """
        Gets the acceleration of the motor in units of fullsteps per square second.

        A negative value indicates a deceleration.

        Values: [`-acceleration_moving`, `+acceleration_moving`]
        """
        if not self.__moving :
            return 0.0
        return self.__acceleration_actual_get_external()

    @property
    def position(self) -> int :
        """
        Gets the position of the motor in units of microsteps.

        Values: [`POSITION_MINIMUM`, `POSITION_MAXIMUM`]
        """
        if self.__position_valid :
            return self.__position
        value = self.__direction_sign * self._position_actual_get()
        if not self.__moving :
            self.__position = value
            self.__position_valid = True
        return value

    @position.setter
    def position(self, value : int) -> None :
        """
        Sets the position of the motor in units of microsteps.

        The position can not be set while the motor is moving.

        Values: [`POSITION_MINIMUM`, `POSITION_MAXIMUM`]

        :raises StateException:
            Motor is moving.
        :raises ValueError:
            Position invalid.
        """
        if self.moving :
            raise StateException()
        Motor._position_verify(value)
        self._position_set(value)

    @property
    def position_target(self) -> int :
        """
        Gets the target position of the motor in units of microsteps.

        Values: [`POSITION_MINIMUM`, `POSITION_MAXIMUM`]
        """
        return self.__direction_sign * self._position_target_get()

    @property
    def moving(self) -> bool :
        """Gets if the motor is moving."""
        if not self.__moving :
            return False
        return self.__moving_detect()

    @property
    def microstep_resolution(self) -> int :
        """
        Gets the microstep resolution of the motor.

        Values: `MICROSTEP_RESOLUTIONS`
        """
        return self.__microstep_resolution

    @microstep_resolution.setter
    def microstep_resolution(self, value : int) -> None :
        """
        Sets the microstep resolution of the motor.

        The microstep resolution can not be set while the motor is moving.

        Values: `MICROSTEP_RESOLUTIONS`

        :raises StateException:
            Motor is moving.
        :raises ValueError:
            Microstep resolution invalid.

        This value dictates the maximum velocity of the motor.

        If the resulting maximum velocity exceeds the moving velocity, the moving velocity is
        reduced to the maximum velocity.
        """
        if self.moving :
            raise StateException()
        try :
            value_internal = Motor.__MICROSTEP_RESOLUTION[value]
        except KeyError :
            raise ValueError('Microstep resolution invalid: Value unknown.')
        if value == self.__microstep_resolution :
            return
        self._microstep_resolution_set(value_internal)
        self.__microstep_resolution = value
        self.__velocity_extrema_update()
        self.__acceleration_extrema_update()

    @property
    def standby_delay(self) -> int :
        """
        Gets the standby delay of the motor in units of milliseconds.

        Values: [`STANDBY_DELAY_MINIMUM`, `STANDBY_DELAY_MAXIMUM`]
        """
        return self.__standby_delay

    @standby_delay.setter
    def standby_delay(self, value: int) -> None :
        """
        Sets the standby delay of the motor in units of milliseconds.

        Values: [`STANDBY_DELAY_MINIMUM`, `STANDBY_DELAY_MAXIMUM`]

        :raises ValueError:
            Standby delay invalid.
        """
        if value < Motor.STANDBY_DELAY_MINIMUM or value > Motor.STANDBY_DELAY_MAXIMUM :
            raise ValueError("Standby delay invalid: Value exceeds limit.")
        value_internal = value // 10
        value = 10 * value_internal
        if value == self.__standby_delay :
            return
        self._standby_delay_set(value_internal)
        self.__standby_delay = value

    @property
    def freewheeling_delay(self) -> int :
        """
        Gets the freewheeling delay of the motor in units of milliseconds.

        Values: `FREEWHEELING_DELAY_DISABLED`, [`FREEWHEELING_DELAY_MINIMUM`,
        `FREEWHEELING_DELAY_MAXIMUM`]
        """
        return self.__freewheeling_delay

    @freewheeling_delay.setter
    def freewheeling_delay(self, value : int) -> None :
        """
        Sets the freewheeling delay of the motor in units of milliseconds.

        Values: `FREEWHEELING_DELAY_DISABLED`, [`FREEWHEELING_DELAY_MINIMUM`,
        `FREEWHEELING_DELAY_MAXIMUM`]

        :raises ValueError:
            Freewheeling delay invalid.
        """
        if value != Motor.FREEWHEELING_DELAY_DISABLED and (
            value < Motor.FREEWHEELING_DELAY_MINIMUM or value > Motor.FREEWHEELING_DELAY_MAXIMUM
        ) :
            raise ValueError("Freewheeling delay invalid: Value exceeds limit.")
        value_internal = value // 10
        value = 10 * value_internal
        if value == self.__freewheeling_delay :
            return
        self._freewheeling_delay_set(value_internal)
        self.__freewheeling_delay = value

    class Coordinates :
        """Coordinates of a motor."""

        def __init__(self, motor : 'Motor') -> None :
            self.__motor = motor
            self.__module_coordinates = motor.module.coordinates

        def __len__(self) -> int :
            """Gets the count of the coordinates."""
            return len(self.__module_coordinates)

        def __getitem__(self, number : int) -> int :
            """
            Gets the position of a coordinate in units of microsteps.

            Values [`Motor.POSITION_MINIMUM`, `Motor.POSITION_MAXIMUM`]

            :param number:
                Number of the coordinate.
                Values: [0, len(self))

            :raises ValueError:
                Coordinate number invalid.
            """
            self.__module_coordinates._number_verify(number)
            position = self.__module_coordinates._get(number, self.__motor.number)
            return self.__motor._direction_sign * position

        def __setitem__(self, number : int, position : int) -> None :
            """
            Sets the position of a coordinate in units of microsteps.

            :param number:
                Number of the coordinate.
                Values: [0, len(self))
            :param position:
                Position of the coordinate.
                Values: [`Motor.POSITION_MINIMUM`, `Motor.POSITION_MAXIMUM`]

            :raises ValueError:
                Coordinate number invalid.
            :raises ValueError:
                Position invalid.
            """
            self.__module_coordinates._number_verify(number)
            Motor._position_verify(position)
            return self.__module_coordinates._set(
                number, self.__motor.number,
                self.__motor._direction_sign * position
            )

        def _revert(self) -> None :
            module_coordinates = self.__module_coordinates
            motor_number = self.__motor.number
            for number in range(len(self)) :
                position = module_coordinates._get(number, motor_number)
                if position == 0 :
                    continue
                position *= -1
                module_coordinates._set(number, motor_number, position)

    @property
    def coordinates(self) -> Coordinates :
        """Gets the coordinates of the motor."""
        return self.__coordinates

    def move_right(self, wait_while_moving : bool = True) -> None :
        """
        Moves the motor in right direction until stopped.

        :param wait_while_moving:
            If the function waits while the motor is moving.
        """
        self._move_indicate(Motor._RampMode.VELOCITY)
        if not self.direction_reversed :
            self.__module._motor_rotate_right(self.__number, self.__velocity_moving_internal)
        else :
            self.__module._motor_rotate_left(self.__number, self.__velocity_moving_internal)
        if wait_while_moving :
            self.wait_while_moving()

    def move_left(self, wait_while_moving : bool = True) -> None :
        """
        Moves the motor in left direction until stopped.

        :param wait_while_moving:
            If the function waits while the motor is moving.
        """
        self._move_indicate(Motor._RampMode.VELOCITY)
        if not self.direction_reversed :
            self.__module._motor_rotate_left(self.__number, self.__velocity_moving_internal)
        else :
            self.__module._motor_rotate_right(self.__number, self.__velocity_moving_internal)
        if wait_while_moving :
            self.wait_while_moving()

    def move_to(self, position : int, wait_while_moving : bool = True) -> None :
        """
        Moves the motor to a position in units of microsteps.

        If the position is greater then the current position of the motor, the motor moves in right
        direction.

        If the position is less then the current position of the motor, the motor moves in left
        direction.

        :param position:
            Position to move the motor to.
            Values: [`POSITION_MINIMUM`, `POSITION_MAXIMUM`]
        :param wait_while_moving:
            If the function waits while the motor is moving.

        :raises ValueError:
            Position invalid.
        """
        if not self.__moving and self.__position_valid and self.__position == position :
            return
        Motor._position_verify(position)
        self._move_indicate(Motor._RampMode.POSITION)
        self.__module._motor_move_to(self.__number, self.__direction_sign * position)
        if wait_while_moving :
            self.wait_while_moving()

    def move_to_coordinate(self, coordinate_number : int, wait_while_moving : bool = True) -> None :
        """
        Moves the motor to a coordinate.

        :param coordinate_number:
            Number of the coordinate to move the motor to.
            Values: [´0´, `module.coordinate_count`)
        :param wait_while_moving:
            If the function waits while the motor is moving.

        :raises ValueError:
            Coordinate number invalid.
        """
        if coordinate_number < 0 or coordinate_number >= self.__module.coordinate_count :
            raise ValueError('Coordinate number invalid: Value negative or exceeds limit.')
        self._move_indicate(Motor._RampMode.POSITION)
        self.__module._motor_move_to_coordinate(self.__number, coordinate_number)
        if wait_while_moving :
            self.wait_while_moving()

    def move_by(self, distance : int, wait_while_moving : bool = True) -> None :
        """
        Moves the motor by a distance in units of microsteps.

        If the distance is positive, the motor moves in right direction.

        If the distance is negative, the motor moves in left direction.

        The position of the motor will overflow if the sum of the position and the distance exceeds
        the limits of the position of `POSITION_MINIMUM` or `POSITION_MAXIMUM`.

        :param distance:
            Position to move the motor to.
            Values: Values: [`DISTANCE_MINIMUM`, `DISTANCE_MAXIMUM`]
        :param wait_while_moving:
            If the function waits while the motor is moving.

        :raises ValueError:
            Distance invalid.
        """
        if distance == 0 and not self.__moving :
            return
        Motor._distance_verify(distance)
        self._move_indicate(Motor._RampMode.POSITION)
        self.__module._motor_move_by(self.__number, self.__direction_sign * distance)
        if wait_while_moving :
            self.wait_while_moving()

    def stop(self, wait_while_moving : bool = True) -> None :
        """
        Stops the motor.

        :param wait_while_moving:
            If the function waits while the motor is moving.
        """
        if not self.__moving :
            return
        self.__ramp_mode = Motor._RampMode.VELOCITY
        self.__moving_detect = self.__moving_detect_velocity
        self.__module._motor_stop(self.__number)
        if wait_while_moving :
            self.wait_while_moving()

    def wait_while_moving(self) -> None :
        """Waits while the motor is moving."""
        while self.moving :
            time.sleep(Motor.MOVING_POLL_DELAY)

    @staticmethod
    def _position_verify(value : int) -> None :
        if value < Motor.POSITION_MINIMUM or value > Motor.POSITION_MAXIMUM :
            raise ValueError('Position invalid: Value exceeds limit.')

    def _position_set(self, value : int) -> None :
        if self.__position_valid and self.__position == value :
            return
        # Setting the position while ramp mode is not "velocity" moves the motor.
        if self.__ramp_mode != Motor._RampMode.VELOCITY :
            self._ramp_mode_set(Motor._RampMode.VELOCITY)
        self._position_actual_set(self.__direction_sign * value)
        self.__position = value
        self.__position_valid = True

    @staticmethod
    def _distance_verify(value : int) -> None :
        if value < Motor.DISTANCE_MINIMUM or value > Motor.DISTANCE_MAXIMUM :
            raise ValueError('Distance invalid: Value exceeds limit.')

    def __init__(self, module : Module, number : int) -> None :
        self.__module = module
        self.__number = number
        self.__switch_limit_right = Switch(self, Switch.Type.LIMIT_RIGHT)
        self.__switch_limit_left = Switch(self, Switch.Type.LIMIT_LEFT)
        self.__switch_home = Switch(self, Switch.Type.HOME)
        self.__current_moving_internal = self._current_moving_get()
        self.__current_moving = self.__module._motor_current_external(
            self.__current_moving_internal
        )
        self.__current_standby_internal = self._current_standby_get()
        self.__current_standby = self.__module._motor_current_external(
            self.__current_standby_internal
        )
        self.__microstep_resolution = self.__microstep_resolution_get_external()
        self.__standby_delay = self.__standby_delay_get_external()
        self.__freewheeling_delay = self.__freewheeling_delay_get_external()
        self.__pulse_divisor_exponent_valid = False
        self.__pulse_divisor_exponent = 0
        self.__ramp_divisor_exponent_valid = False
        self.__ramp_divisor_exponent = 0
        self.__position_valid = False
        self.__position = 0
        self.__direction_sign = 1
        self.__velocity_moving_internal = self._velocity_moving_get()
        self.__velocity_moving = self._velocity_external(
            self.__velocity_moving_internal
        )
        self.__acceleration_moving_internal = self._acceleration_moving_get()
        self.__acceleration_moving = self._acceleration_external(
            self.__acceleration_moving_internal
        )
        self.__velocity_extrema_update()
        self.__acceleration_extrema_update()
        self.__coordinates = Motor.Coordinates(self)
        self._move_indicate(self._ramp_mode_get())

    @abc.abstractmethod
    def _velocity_moving_set_external(self, value : float) -> int :
        """
        Sets the moving velocity of the motor in units of fullsteps per second (rounded down to the
        next lower motor velocity step of the module).

        Returns the value set in internal units.
        """
        pass

    @abc.abstractmethod
    def _velocity_external(self, value : int) -> float :
        """
        Converts a velocity of the motor from internal units into units of fullsteps per second.
        """
        pass

    @abc.abstractmethod
    def _acceleration_extrema_get_external(self) -> typing.Tuple[float, float] :
        """
        Gets the minimum and maximum moving acceleration of the motor in units of fullsteps per
        square second.
        """
        pass

    @abc.abstractmethod
    def _acceleration_moving_set_external(self, value : float) -> int :
        """
        Sets the moving acceleration of the motor in units of fullsteps per square second (rounded
        down to the next lower motor acceleration step of the module).

        Returns the value set in internal units.
        """
        pass

    @abc.abstractmethod
    def _acceleration_external(self, value : int) -> float :
        """
        Converts an acceleration of the motor from internal units into units of fullsteps per
        second.
        """
        pass

    def _position_target_set(self, value : int) -> None :
        self.__parameter_set(Motor.__Parameter.POSITION_TARGET, value)

    def _position_target_get(self) -> int :
        return self.__parameter_get(Motor.__Parameter.POSITION_TARGET)

    def _position_actual_set(self, value : int) -> None :
        self.__parameter_set(Motor.__Parameter.POSITION_ACTUAL, value)

    def _position_actual_get(self) -> int :
        return self.__parameter_get(Motor.__Parameter.POSITION_ACTUAL)

    def _position_reached_get(self) -> bool :
        """Gets if the motor has reached its target position."""
        return self.__parameter_get_bool(Motor.__Parameter.POSITION_REACHED)

    @property
    def _direction_sign(self) -> int :
        return self.__direction_sign

    def _pulse_divisor_exponent_set(self, value : int) -> None :
        """Sets the exponent of the pulse divisor of the motor."""
        if self.__pulse_divisor_exponent_valid and self.__pulse_divisor_exponent == value :
            return
        self.__parameter_set(Motor.__Parameter.PULSE_DIVISOR_EXPONENT, value)
        self.__pulse_divisor_exponent = value
        self.__pulse_divisor_exponent_valid = True
        # Note: Setting the pulse divisor sometimes moves the motor by one microstep.
        # Therefore: Invalidate position.
        self.__position_valid = False

    def _pulse_divisor_exponent_get(self) -> int :
        """Gets the exponent of the pulse divisor of the motor."""
        if self.__pulse_divisor_exponent_valid :
            return self.__pulse_divisor_exponent
        value = self.__parameter_get(Motor.__Parameter.PULSE_DIVISOR_EXPONENT)
        self.__pulse_divisor_exponent = value
        self.__pulse_divisor_exponent_valid = True
        return value

    def _ramp_divisor_exponent_set(self, value : int) -> None :
        """Sets the exponent of the ramp divisor of the motor."""
        if self.__ramp_divisor_exponent_valid and self.__ramp_divisor_exponent == value :
            return
        self.__parameter_set(Motor.__Parameter.RAMP_DIVISOR_EXPONENT, value)
        self.__ramp_divisor_exponent = value
        self.__ramp_divisor_exponent_valid = True

    def _ramp_divisor_exponent_get(self) -> int :
        """Gets the exponent of the ramp divisor of the motor."""
        if self.__ramp_divisor_exponent_valid :
            return self.__ramp_divisor_exponent
        value = self.__parameter_get(Motor.__Parameter.RAMP_DIVISOR_EXPONENT)
        self.__ramp_divisor_exponent = value
        self.__ramp_divisor_exponent_valid = True
        return value

    def _velocity_target_set(self, value : int) -> None :
        self.__parameter_set(Motor.__Parameter.VELOCITY_TARGET, value)

    def _velocity_target_get(self) -> int :
        return self.__parameter_get(Motor.__Parameter.VELOCITY_TARGET)

    def _velocity_actual_get(self) -> int :
        """
        Gets the actual velocity of the motor.

        The unit depends on the module.
        """
        return self.__parameter_get(Motor.__Parameter.VELOCITY_ACTUAL)

    def _velocity_moving_set(self, value : int) -> None :
        """
        Sets the moving velocity of the motor.

        The unit depends on the module.
        """
        self.__parameter_set(Motor.__Parameter.VELOCITY_MOVING, value)

    def _velocity_moving_get(self) -> int :
        """
        Gets the moving velocity of the motor.

        The unit depends on the module.
        """
        return self.__parameter_get(Motor.__Parameter.VELOCITY_MOVING)

    def _acceleration_actual_get(self) -> int :
        """
        Gets the actual acceleration of the motor.

        The unit depends on the module.
        """
        return self.__parameter_get(Motor.__Parameter.ACCELERATION_ACTUAL)

    def _acceleration_moving_set(self, value : int) -> None :
        """
        Sets the the moving acceleration of the motor.

        The unit depends on the module.
        """
        self.__parameter_set(Motor.__Parameter.ACCELERATION_MOVING, value)

    def _acceleration_moving_get(self) -> int :
        """
        Gets the the moving acceleration of the motor.

        The unit depends on the module.
        """
        return self.__parameter_get(Motor.__Parameter.ACCELERATION_MOVING)

    def _current_moving_set(self, value : int) -> None :
        """Sets the moving current of the motor as portion of `_MOTOR_CURRENT_PORTIONS`."""
        return self.__parameter_set(Motor.__Parameter.CURRENT_MOVING, value)

    def _current_moving_get(self) -> int :
        """Gets the moving current of the motor as portion of `_MOTOR_CURRENT_PORTIONS`."""
        return self.__parameter_get(Motor.__Parameter.CURRENT_MOVING)

    def _current_standby_set(self, value : int) -> None :
        """Sets the standby current of the motor as portion of `_MOTOR_CURRENT_PORTIONS`."""
        return self.__parameter_set(Motor.__Parameter.CURRENT_STANDBY, value)

    def _current_standby_get(self) -> int :
        """Gets the standby current of the motor as portion of `_MOTOR_CURRENT_PORTIONS`."""
        return self.__parameter_get(Motor.__Parameter.CURRENT_STANDBY)

    def _microstep_resolution_set(self, value : int) -> None :
        """Sets the microstep resolution of the motor as base of values to the power of 2."""
        self.__parameter_set(Motor.__Parameter.MICROSTEP_RESOLUTION, value)

    def _microstep_resolution_get(self) -> int :
        """Gets the microstep resolution of the motor as base of values to the power of 2."""
        return self.__parameter_get(Motor.__Parameter.MICROSTEP_RESOLUTION)

    class _RampMode(enum.IntEnum) :
        """Ramp mode of a motor."""
        POSITION      = 0
        POSITION_SOFT = 1
        VELOCITY      = 2

    def _ramp_mode_set(self, ramp_mode : _RampMode) -> None :
        """Sets the ramp mode of the motor."""
        self.__parameter_set(Motor.__Parameter.RAMP_MODE, ramp_mode)

    def _ramp_mode_get(self) -> _RampMode :
        """Gets the ramp mode of the motor."""
        return Motor._RampMode(self.__parameter_get(Motor.__Parameter.RAMP_MODE))

    def _standby_delay_set(self, value : int) -> None :
        """Sets the standby delay of the motor in units of centiseconds."""
        self.__parameter_set(Motor.__Parameter.STANDBY_DELAY, value)

    def _standby_delay_get(self) -> int :
        """Gets the standby delay of the motor in units of centiseconds."""
        return self.__parameter_get(Motor.__Parameter.STANDBY_DELAY)

    def _freewheeling_delay_set(self, value : int) -> None :
        """Sets the freewheeling delay of the motor in units of centiseconds."""
        self.__parameter_set(Motor.__Parameter.FREEWHEELING_DELAY, value)

    def _freewheeling_delay_get(self) -> int :
        """Gets the freewheeling delay of the motor in units of centiseconds."""
        return self.__parameter_get(Motor.__Parameter.FREEWHEELING_DELAY)

    def _switch_limit_right_disabled_set(self, state : bool) -> None :
        """Sets if the right limit switch of the motor is disabled."""
        self.__parameter_set_bool(Motor.__Parameter.SWITCH_LIMIT_RIGHT_DISABLED, state)

    def _switch_limit_right_disabled_get(self) -> bool :
        """Gets if the right limit switch of the motor is disabled."""
        return self.__parameter_get_bool(Motor.__Parameter.SWITCH_LIMIT_RIGHT_DISABLED)

    def _switch_limit_right_active_get(self) -> bool :
        """Gets if the right limit switch of the motor is active."""
        return self.__parameter_get_bool(Motor.__Parameter.SWITCH_LIMIT_RIGHT_ACTIVE)

    def _switch_limit_left_disabled_set(self, state : bool) -> None :
        """Sets if the left limit switch of the motor is disabled."""
        self.__parameter_set_bool(Motor.__Parameter.SWITCH_LIMIT_LEFT_DISABLED, state)

    def _switch_limit_left_disabled_get(self) -> bool :
        """Gets if the left limit switch of the motor is disabled."""
        return self.__parameter_get_bool(Motor.__Parameter.SWITCH_LIMIT_LEFT_DISABLED)

    def _switch_limit_left_active_get(self) -> bool :
        """Gets if the left limit switch of the motor is active."""
        return self.__parameter_get_bool(Motor.__Parameter.SWITCH_LIMIT_LEFT_ACTIVE)

    def _switch_home_active_get(self) -> bool :
        """Gets if the home switch of the motor is active."""
        return self.__parameter_get_bool(Motor.__Parameter.SWITCH_HOME_ACTIVE)

    def _move_indicate(
        self,
        ramp_mode : _RampMode
    ) -> None :
        """Indicates a move of the motor."""
        self.__ramp_mode = ramp_mode
        self.__moving = True
        self.__moving_detect = (
            self.__moving_detect_velocity
            if ramp_mode == Motor._RampMode.VELOCITY else
            self.__moving_detect_position
        )
        self.__position_valid = False
        self.__position = 0

    class __Parameter(enum.IntEnum) :
        POSITION_TARGET         = 0
        POSITION_ACTUAL         = 1
        POSITION_REACHED        = 8

        PULSE_DIVISOR_EXPONENT  = 154
        RAMP_DIVISOR_EXPONENT   = 153

        VELOCITY_TARGET         = 2
        VELOCITY_ACTUAL         = 3
        VELOCITY_MOVING         = 4

        ACCELERATION_ACTUAL     = 135
        ACCELERATION_MOVING     = 5
        
        CURRENT_MOVING          = 6
        CURRENT_STANDBY         = 7
        CURRENT_ACCELERATION    = 200
        
        MICROSTEP_RESOLUTION    = 140

        RAMP_MODE               = 138

        STANDBY_DELAY           = 214
        FREEWHEELING_DELAY      = 204

        SWITCH_LIMIT_RIGHT_DISABLED = 12
        SWITCH_LIMIT_LEFT_DISABLED  = 13
        SWITCH_LIMIT_RIGHT_ACTIVE   = 10
        SWITCH_LIMIT_LEFT_ACTIVE    = 11
        SWITCH_HOME_ACTIVE          = 9

    __MICROSTEP_RESOLUTION = {
          1 : 0,
          2 : 1,
          4 : 2,
          8 : 3,
         16 : 4,
         32 : 5,
         64 : 6,
        128 : 7,
        256 : 8
    }

    def __parameter_set(self, parameter : __Parameter, value : int) -> None :
        self.__module._axis_parameter_set(self.__number, parameter.value, value)

    def __parameter_set_bool(self, parameter : __Parameter, state : bool) -> None :
        self.__parameter_set(parameter, int(state))

    def __parameter_get(self, parameter : __Parameter) -> int :
        return self.__module._axis_parameter_get(self.__number, parameter.value)

    def __parameter_get_bool(self, parameter : __Parameter) -> bool :
        return bool(self.__parameter_get(parameter))

    def __microstep_resolution_get_external(self) -> int :
        """Gets the microstep resolution of the motor in units of microsteps per fullstep."""
        return 2 ** self._microstep_resolution_get()

    def __standby_delay_get_external(self) -> int :
        """Gets the standby delay of the motor in units of milliseconds."""
        return 10 * self._standby_delay_get()

    def __freewheeling_delay_get_external(self) -> int :
        """Gets the freewheeling delay of the motor in units of milliseconds."""
        return 10 * self._freewheeling_delay_get()

    def __velocity_actual_get_external(self) -> float :
        """Gets the actual velocity of the motor in units of fullsteps per second."""
        return self.__direction_sign * self._velocity_external(self._velocity_actual_get())

    def __velocity_moving_set_external(self, value : float) -> None :
        value_internal = self._velocity_moving_set_external(value)
        if self.__velocity_moving_internal != value_internal :
            self._velocity_moving_set(value_internal)
            self.__velocity_moving_internal = value_internal
        self.__velocity_moving = self._velocity_external(value_internal)

    def __velocity_extrema_update(self) -> None :
        minimum = self.__module.motor_frequency_minimum / self.__microstep_resolution
        maximum = self.__module.motor_frequency_maximum / self.__microstep_resolution
        moving = self.__velocity_moving
        self.__velocity_minimum = minimum
        self.__velocity_maximum = maximum
        if moving < minimum :
            moving = minimum
        elif moving > maximum :
            moving = maximum
        self.__velocity_moving_set_external(moving)

    def __acceleration_actual_get_external(self) -> float :
        """Gets the actual acceleration of the motor in units of fullsteps per square second."""
        return self._acceleration_external(self._acceleration_actual_get())

    def __acceleration_moving_set_external(self, value : float) -> None :
        value_internal = self._acceleration_moving_set_external(value)
        if value_internal != self.__acceleration_moving_internal :
            self._acceleration_moving_set(value_internal)
            self.__acceleration_moving_internal = value_internal
        self.__acceleration_moving = self._acceleration_external(value_internal)

    def __acceleration_extrema_update(self) -> None :
        minimum, maximum = self._acceleration_extrema_get_external()
        moving = self.__acceleration_moving
        self.__acceleration_minimum = minimum
        self.__acceleration_maximum = maximum
        if moving < minimum :
            moving = minimum
        elif moving > maximum :
            moving = maximum
        self.__acceleration_moving_set_external(moving)

    def __moving_detect_false(self) -> bool :
        return False

    def __moving_detect_position(self) -> bool :
        if not self._position_reached_get() :
            return True
        self.__moving = False
        self.__moving_detect = self.__moving_detect_false
        return False

    def __moving_detect_velocity(self) -> bool :
        velocity_target = self._velocity_target_get()
        if velocity_target != 0 :
            return True
        moving_detect = self.__moving_detect_velocity_2
        self.__moving_detect = moving_detect
        return moving_detect()

    def __moving_detect_velocity_2(self) -> bool :
        velocity = self._velocity_actual_get()
        if velocity != 0 :
            return True
        self.__moving = False
        self.__moving_detect = self.__moving_detect_false
        return False