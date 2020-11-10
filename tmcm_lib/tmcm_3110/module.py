from tmcm_lib.port import Port
from tmcm_lib.module import Module as ModuleGeneric
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
    MOTOR_FREQUENCY_MINIMUM : float = Motor._FREQUENCY_MINIMUM
    # Maximum motor frequency of the module in units of hertz.
    MOTOR_FREQUENCY_MAXIMUM : float = Motor._FREQUENCY_MAXIMUM

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
            Motor,
            Module.COORDINATE_COUNT
        )
        self._port_output_pullup_enabled_set(Module.__PORT_PULLUP_SWITCHES_LIMIT, False)
        self.__switch_limit_pullup_enabled = False

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
        if self.__switch_limit_pullup_enabled == enabled :
            return
        self._port_output_pullup_enabled_set(Module.__PORT_PULLUP_SWITCHES_LIMIT, enabled)
        self.__switch_limit_pullup_enabled = enabled

    __PORT_SUPPLY_VOLTAGE = 8
    __PORT_PULLUP_SWITCHES_LIMIT = 0