from .port import Port
from .module import Module as ModuleGeneric
from .motor import Motor

import math

class Module(ModuleGeneric) :
    """Module TMCM-3110."""

    # Identity of the module.
    IDENTITY = 3110

    # Motor count of the module.
    MOTOR_COUNT = 3

    # Maximum motor current (RMS) of the module in units of milliamperes.
    # Determined with current steps in TMCL-IDE (Version 3.1.0.0).
    MOTOR_CURRENT_MAXIMUM = 2768

    # Minimum motor frequency of the module in units of hertz.
    MOTOR_FREQUENCY_MINIMUM : float # Defined later.
    # Maximum motor frequency of the module in units of hertz.
    MOTOR_FREQUENCY_MAXIMUM : float # Defined later.

    # Coordinate count of the module.
    COORDINATE_COUNT = 20

    def __init__(self, port : Port) -> None :
        """Creates a module connected to the given port."""
        super().__init__(
            port,
            Module.IDENTITY,
            Module.MOTOR_COUNT,
            Module.MOTOR_CURRENT_MAXIMUM,
            Module.MOTOR_FREQUENCY_MINIMUM,
            Module.MOTOR_FREQUENCY_MAXIMUM,
            Module.COORDINATE_COUNT
        )
        self.switch_limit_pullup_enabled = False

    @property
    def supply_voltage(self) -> int :
        """Gets the supply voltage of the module in units of millivolts."""
        # Supply voltage is returned as decivolts.
        return 100 * self._port_input_analog_get(Module.__PORT_SUPPLY_VOLTAGE)

    @property
    def switch_limit_pullup_enabled(self) -> bool :
        """Gets if the pull-up resistors of the limit switches of the module are enabled."""
        return self.__switch_limit_pullup_enabled

    @switch_limit_pullup_enabled.setter
    def switch_limit_pullup_enabled(self, enabled : bool) -> None :
        """Sets if the pull-up resistors of the limit switches of the module are enabled."""
        self._port_output_pullup_enabled_set(Module.__PORT_PULLUP_SWITCHES_LIMIT, enabled)
        self.__switch_limit_pullup_enabled = enabled

    # Overrides.
    def _motor_velocity_moving_set_external(self, motor: Motor, value : float) -> (int, float) :
        """
        Sets the moving velocity of a motor in units of fullsteps per second (rounded down to the
        next lower motor velocity step of the module).

        Returns the value set (internal and external).
        """
        if value == 0.0 :
            motor._pulse_divisor_exponent_set(0)
            motor._velocity_moving_set(0)
            return (0, 0.0)
        microstep_resolution = motor.microstep_resolution
        (pulse_divisor_exponent, portion) = Module.__motor_velocity_internal(
            value,
            motor.velocity_maximum,
            microstep_resolution
        )
        motor._pulse_divisor_exponent_set(pulse_divisor_exponent)
        motor._velocity_moving_set(portion)
        return (portion, Module.__motor_velocity_external(
            pulse_divisor_exponent,
            portion,
            microstep_resolution
        ))

    # Overrides.
    def _motor_velocity_external(self, motor : Motor, value : int) -> float :
        """Converts a velocity of a motor from internal units in units of fullsteps per second."""
        return Module.__motor_velocity_external(
            motor._pulse_divisor_exponent_get(),
            value,
            motor.microstep_resolution
        )

    # Overrides.
    def _motor_acceleration_extrema_get_external(self, motor : 'Motor') -> (float, float) :
        """
        Gets the minimum and maximum moving acceleration of a motor in units of fullsteps per
        square second.
        """
        pulse_divisor_exponent = motor._pulse_divisor_exponent_get()
        microstep_resolution = motor.microstep_resolution
        minimum = Module.__motor_acceleration_external(
            pulse_divisor_exponent,
            Module.__MOTOR_RAMP_DIVISOR_EXPONENT_MAXIMUM,
            1,
            microstep_resolution
        )
        maximum = Module.__motor_acceleration_external(
            pulse_divisor_exponent,
            0,
            Module._MOTOR_ACCELERATION_PORTIONS - 1,
            microstep_resolution
        )
        return (minimum, maximum)

    # Overrides.
    def _motor_acceleration_moving_set_external(self, motor : 'Motor', value : float) -> float :
        """
        Sets the moving acceleration of a motor in units of fullsteps per square second (rounded
        down to the next lower motor acceleration step of the module).

        Returns the value set.
        """
        if value == 0.0 :
            motor._ramp_divisor_exponent_set(0)
            motor._acceleration_moving_set(0)
            return 0
        pulse_divisor_exponent = motor._pulse_divisor_exponent_get()
        microstep_resolution = motor.microstep_resolution
        (ramp_divisor_exponent, portion) = Module.__motor_acceleration_internal(
            pulse_divisor_exponent,
            value,
            motor.acceleration_maximum,
            microstep_resolution
        )
        motor._ramp_divisor_exponent_set(ramp_divisor_exponent)
        motor._acceleration_moving_set(portion)
        return Module.__motor_acceleration_external(
            pulse_divisor_exponent,
            ramp_divisor_exponent,
            portion,
            microstep_resolution
        )

    # Overrides.
    def _motor_acceleration_moving_get_external(self, motor : Motor) -> float :
        """Gets the moving acceleration of a motor in units of fullsteps per square second."""
        return Module.__motor_acceleration_external(
            motor._pulse_divisor_exponent_get(),
            motor._ramp_divisor_exponent_get(),
            motor._acceleration_moving_get(),
            motor.microstep_resolution
        )

    __MOTOR_PULSE_DIVISOR_EXPONENT_MAXIMUM = 13
    __MOTOR_RAMP_DIVISOR_EXPONENT_MAXIMUM  = 13

    __PORT_SUPPLY_VOLTAGE = 8
    __PORT_PULLUP_SWITCHES_LIMIT = 0

    # Motor parameters
    # Determined with velocity and acceleration calculation in firmware manual (Firmware version
    # 1.14, Document version 1.11).
    __MOTOR_VELOCITY_DIVIDEND     = 16 * 1_000_000 // 32
    __MOTOR_ACCELERATION_DIVIDEND = (16 * 1_000_000) ** 2 // 262_144

    @classmethod
    def __motor_velocity_external(
        cls,
        pulse_divisor_exponent : int,
        portion : int,
        microstep_resolution : int
    ) -> float :
        """
        Converts a motor velocity from a pulse divisor exponent and a portion of
        `__MOTOR_VELOCITY_PORTIONS` into units of fullsteps per second.
        """
        return (
            portion * cls.__MOTOR_VELOCITY_DIVIDEND / (
                cls._MOTOR_VELOCITY_PORTIONS *
                cls._MOTOR_DIVISOR_BASE ** pulse_divisor_exponent
            ) / microstep_resolution
        )

    @classmethod
    def __motor_velocity_internal(
        cls,
        value : float,
        maximum : float,
        microstep_resolution : int
    ) -> (int, int) :
        """
        Converts a motor velocity from units of fullsteps per second into a pulse divisor exponent
        and a portion of `__MOTOR_VELOCITY_PORTIONS`.
        """
        pulse_divisor = maximum / value
        pulse_divisor_exponent = min(
            cls.__MOTOR_PULSE_DIVISOR_EXPONENT_MAXIMUM,
            int(math.log(pulse_divisor, cls._MOTOR_DIVISOR_BASE))
        )
        maximum = math.ceil(cls.__motor_velocity_external(
            pulse_divisor_exponent,
            cls._MOTOR_VELOCITY_PORTIONS - 1,
            microstep_resolution
        ))
        portion = int(cls._MOTOR_VELOCITY_PORTIONS * value / maximum)
        return (pulse_divisor_exponent, portion)

    @classmethod
    def __motor_acceleration_external(
        cls,
        pulse_divisor_exponent : int,
        ramp_divisor_exponent: int,
        portion : int,
        microstep_resolution : int
    ) -> float :
        """
        Converts a motor acceleration from a portion of `__MOTOR_ACCELERATION_PORTIONS` and a
        divisor exponent into units of fullsteps per square second.
        """
        return (
            portion * cls.__MOTOR_ACCELERATION_DIVIDEND / (
                    cls._MOTOR_ACCELERATION_PORTIONS *
                    cls._MOTOR_DIVISOR_BASE ** (
                        pulse_divisor_exponent + ramp_divisor_exponent
                    )
            ) / microstep_resolution
        )

    @classmethod
    def __motor_acceleration_internal(
        cls,
        pulse_divisor_exponent : int,
        value : float,
        maximum : float,
        microstep_resolution : int
    ) -> (int, int) :
        """
        Converts a motor acceleration from units of fullsteps per square second into a ramp
        divisor exponent and a portion of `__MOTOR_ACCELERATION_PORTIONS`.
        """
        ramp_divisor = maximum / value
        ramp_divisor_exponent = min(
            cls.__MOTOR_RAMP_DIVISOR_EXPONENT_MAXIMUM,
            max(0, int(math.log(ramp_divisor, cls._MOTOR_DIVISOR_BASE)) - pulse_divisor_exponent)
        )
        maximum = math.ceil(cls.__motor_acceleration_external(
            pulse_divisor_exponent,
            ramp_divisor_exponent,
            cls._MOTOR_ACCELERATION_PORTIONS - 1,
            microstep_resolution
        ))
        portion = int(cls._MOTOR_ACCELERATION_PORTIONS * value / maximum)
        return (ramp_divisor_exponent, portion)

    @classmethod
    def _initialize(cls) -> None :
        cls.MOTOR_FREQUENCY_MINIMUM = cls.__motor_velocity_external(
            cls.__MOTOR_PULSE_DIVISOR_EXPONENT_MAXIMUM,
            1,
            1
        )
        cls.MOTOR_FREQUENCY_MAXIMUM = cls.__motor_velocity_external(
            0,
            cls._MOTOR_VELOCITY_PORTIONS - 1,
            1
        )

        del cls._initialize

Module._initialize()