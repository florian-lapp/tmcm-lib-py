from tmcm_lib.motor import Motor as MotorGeneric

import math
import typing

class Motor(MotorGeneric) :

    # Minimum frequency of the motors in units of hertz.
    _FREQUENCY_MINIMUM : float # Defined later.
    # Maximum frequency of the motors in units of hertz.
    _FREQUENCY_MAXIMUM : float # Defined later.

    # Overrides.
    def _velocity_moving_set_external(self, value : float) -> int :
        """
        Sets the moving velocity of the motor in units of fullsteps per second (rounded down to the
        next lower motor velocity step of the module).

        Returns the value set in internal units.
        """
        if value == 0.0 :
            pulse_divisor_exponent = 0
            portion = 0
        else :
            pulse_divisor_exponent, portion = Motor.__velocity_internal(
                value,
                self.microstep_resolution
            )
        self._pulse_divisor_exponent_set(pulse_divisor_exponent)
        return portion

    # Overrides.
    def _velocity_external(self, value : int) -> float :
        """
        Converts a velocity of the motor from internal units into units of fullsteps per second.
        """
        return Motor.__velocity_external(
            self._pulse_divisor_exponent_get(),
            value,
            self.microstep_resolution
        )

    # Overrides.
    def _acceleration_extrema_get_external(self) -> typing.Tuple[float, float] :
        """
        Gets the minimum and maximum moving acceleration of the motor in units of fullsteps per
        square second.
        """
        pulse_divisor_exponent = self._pulse_divisor_exponent_get()
        microstep_resolution = self.microstep_resolution
        minimum = Motor.__acceleration_external(
            pulse_divisor_exponent,
            min(Motor.__RAMP_DIVISOR_EXPONENT_MAXIMUM, pulse_divisor_exponent + 1),
            1,
            microstep_resolution
        )
        maximum = Motor.__acceleration_external(
            pulse_divisor_exponent,
            max(0, pulse_divisor_exponent - 1),
            Motor.__ACCELERATION_PORTIONS - 1,
            microstep_resolution
        )
        return minimum, maximum

    # Overrides.
    def _acceleration_moving_set_external(self, value : float) -> int :
        """
        Sets the moving acceleration of the motor in units of fullsteps per square second (rounded
        down to the next lower motor acceleration step of the module).

        Returns the value set in internal units.
        """
        if value == 0.0 :
            ramp_divisor_exponent = 0
            portion = 0
        else :
            pulse_divisor_exponent = self._pulse_divisor_exponent_get()
            ramp_divisor_exponent, portion = Motor.__acceleration_internal(
                pulse_divisor_exponent,
                value,
                self.microstep_resolution
            )
        self._ramp_divisor_exponent_set(ramp_divisor_exponent)
        return portion

    # Overrides.
    def _acceleration_external(self, value : int) -> float :
        """
        Converts an acceleration of the motor from internal units into units of fullsteps per
        second.
        """
        return Motor.__acceleration_external(
            self._pulse_divisor_exponent_get(),
            self._ramp_divisor_exponent_get(),
            value,
            self.microstep_resolution
        )

    # Motor parameters
    # Determined with velocity and acceleration calculation in firmware manual (Firmware version
    # 1.14, Document version 1.11).
    __VELOCITY_PORTIONS     = 2048
    __VELOCITY_DIVIDEND     = 16 * 1_000_000 // 32
    __ACCELERATION_PORTIONS = 2048
    __ACCELERATION_DIVIDEND = (16 * 1_000_000) ** 2 // 262_144
    __PULSE_DIVISOR_EXPONENT_MAXIMUM = 13
    __RAMP_DIVISOR_EXPONENT_MAXIMUM  = 13
    # Base of pulse and ramp divisors.
    __DIVISOR_BASE = 2

    @classmethod
    def __velocity_external(
        cls,
        pulse_divisor_exponent : int,
        portion : int,
        microstep_resolution : int
    ) -> float :
        """
        Converts a velocity of a motor from a pulse divisor exponent and a portion of
        `__VELOCITY_PORTIONS` into units of fullsteps per second.
        """
        return (
            portion * cls.__VELOCITY_DIVIDEND / (
                cls.__VELOCITY_PORTIONS *
                cls.__DIVISOR_BASE ** pulse_divisor_exponent
            ) / microstep_resolution
        )

    @classmethod
    def __velocity_internal(
        cls,
        value : float,
        microstep_resolution : int
    ) -> typing.Tuple[int, int] :
        """
        Converts a velocity of a motor from units of fullsteps per second into a pulse divisor
        exponent and a portion of `__VELOCITY_PORTIONS`.
        """
        pulse_divisor = cls.__VELOCITY_DIVIDEND / (microstep_resolution * value)
        pulse_divisor_exponent = min(
            cls.__PULSE_DIVISOR_EXPONENT_MAXIMUM,
            max(0, int(math.log(pulse_divisor, cls.__DIVISOR_BASE)))
        )
        maximum = cls.__velocity_external(
            pulse_divisor_exponent,
            cls.__VELOCITY_PORTIONS - 1,
            microstep_resolution
        )
        portion = int((cls.__VELOCITY_PORTIONS - 1) * value / maximum)
        return pulse_divisor_exponent, portion

    @classmethod
    def __acceleration_external(
        cls,
        pulse_divisor_exponent : int,
        ramp_divisor_exponent : int,
        portion : int,
        microstep_resolution : int
    ) -> float :
        """
        Converts an acceleration of a motor from a portion of `__ACCELERATION_PORTIONS` and a
        divisor exponent into units of fullsteps per square second.
        """
        return (
            portion * cls.__ACCELERATION_DIVIDEND / (
                cls.__ACCELERATION_PORTIONS *
                cls.__DIVISOR_BASE ** (
                    pulse_divisor_exponent + ramp_divisor_exponent
                )
            ) / microstep_resolution
        )

    @classmethod
    def __acceleration_internal(
        cls,
        pulse_divisor_exponent : int,
        value : float,
        microstep_resolution : int
    ) -> typing.Tuple[int, int] :
        """
        Converts an acceleration of a motor from units of fullsteps per square second into a ramp
        divisor exponent and a portion of `__ACCELERATION_PORTIONS`.
        """
        ramp_divisor = cls.__ACCELERATION_DIVIDEND / (
            microstep_resolution * value
        )
        ramp_divisor_exponent = min(
            pulse_divisor_exponent + 1,
            cls.__RAMP_DIVISOR_EXPONENT_MAXIMUM,
            max(
                pulse_divisor_exponent - 1,
                0,
                int(math.log(ramp_divisor, cls.__DIVISOR_BASE)) - pulse_divisor_exponent
            )
        )
        maximum = cls.__acceleration_external(
            pulse_divisor_exponent,
            ramp_divisor_exponent,
            cls.__ACCELERATION_PORTIONS - 1,
            microstep_resolution
        )
        portion = int((cls.__ACCELERATION_PORTIONS - 1) * value / maximum)
        return ramp_divisor_exponent, portion

    @classmethod
    def _initialize(cls) -> None :
        cls._FREQUENCY_MINIMUM = cls.__velocity_external(
            cls.__PULSE_DIVISOR_EXPONENT_MAXIMUM,
            1,
            1
        )
        cls._FREQUENCY_MAXIMUM = cls.__velocity_external(
            0,
            Motor.__VELOCITY_PORTIONS - 1,
            1
        )
        del cls._initialize

Motor._initialize()