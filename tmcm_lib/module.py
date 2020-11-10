from .port import Port
from .exceptions import *

import abc
import enum
import typing

if typing.TYPE_CHECKING :
    from .motor import Motor

class Module(abc.ABC) :

    @classmethod
    def identify(cls, port : Port) -> (int, (int, int)) :
        """Gets the identity and the firmware version of the module connected to the given port."""
        return cls.__firmware_version_get(port)

    @classmethod
    def construct(cls, port : Port) -> 'Module' :
        """
        Constructs a module of the class identified by the module connected to the given port.

        Raises an NotImplementedError if the connected module is not implemented.
        """
        identity, _ = cls.identify(port)
        import importlib
        try :
            module = importlib.import_module('.' + cls.__MODULE_NAME.format(identity), __package__)
        except ImportError :
            pass
        else :
            module_cls = getattr(module, cls.__CLASS_NAME, None)
            if module_cls and issubclass(module_cls, Module) :
                return module_cls(port)
        raise NotImplementedError()

    @property
    def identity(self) -> int :
        """Gets the identity of the module."""
        return self.__identity

    @property
    def firmware_version(self) -> (int, int) :
        """Gets the firmware version of the module as major version and minor version."""
        return self.__firmware_version

    @property
    def supply_voltage(self) -> int :
        """Gets the supply voltage of the module in units of millivolts."""
        raise NotImplementedError()

    @property
    def switch_limit_activity(self) -> bool :
        """
        Gets the activity of the limit switches of the module.

        Values:
            | True  : Active high
            | False : Active low
        """
        return self.__switch_limit_activity

    @switch_limit_activity.setter
    def switch_limit_activity(self, activity : bool) -> None :
        """
        Sets the activity of the limit switches of the module.

        Values:
            | True  : Active high
            | False : Active low
        """
        if activity == self.__switch_limit_activity :
            return
        self._switch_limit_polarity_set(not activity)
        self.__switch_limit_activity = activity

    def factory_settings_restore(self) -> None :
        """Restores the factory settings of the module."""
        self.__factory_settings_restore()

    @property
    def motor_count(self) -> int :
        """Gets the motor count of the module."""
        return len(self.__motors)

    @property
    def motor_current_minimum(self) -> int :
        """Gets the minimum motor current (RMS) of the module in units of milliamperes."""
        return self.__motor_current_minimum

    @property
    def motor_current_maximum(self) -> int :
        """Gets the maximum motor current (RMS) of the module in units of milliamperes."""
        return self.__motor_current_maximum

    @property
    def motor_frequency_minimum(self) -> float :
        """Gets the minimum motor frequency of the module in units of hertz."""
        return self.__motor_frequency_minimum

    @property
    def motor_frequency_maximum(self) -> float :
        """Gets the maximum motor frequency of the module in units of hertz."""
        return self.__motor_frequency_maximum

    @property
    def motors(self) -> ('Motor', ...) :
        """Gets the motors of the module."""
        return self.__motors

    @property
    def coordinate_count(self) -> int :
        """Gets the coordinate count of the module."""
        return len(self.__coordinates)

    class Coordinates :
        """Coordinates of a module."""

        def __init__(self, module : 'Module', count : int, motor_count : int) -> None :
            self.__module = module
            self.__count = count
            self.__motor_count = motor_count
        
        def __len__(self) -> int :
            """Gets the count of the coordinates."""
            return self.__count

        def __getitem__(self, number : int) -> (int, ...) :
            """
            Gets the positions of a coordinate.

            Number values: [0, len(self))

            Position values: [`Motor.POSITION_MINIMUM`, `Motor.POSITION_MAXIMUM`]
            """
            self._number_verify(number)
            return tuple(
                self._get(number, motor_number)
                for motor_number in range(self.__motor_count)
            )

        def __setitem__(self, number : int, positions : typing.Iterable[int]) -> None :
            """
            Sets the positions of a coordinate.

            Number values: [0, len(self))

            Position values: [`Motor.POSITION_MINIMUM`, `Motor.POSITION_MAXIMUM`]
            """
            self._number_verify(number)
            from .motor import Motor
            for position in positions :
                Motor._position_verify(position)
            for (motor_number, position) in zip(range(self.__motor_count), positions) :
                self._set(number, motor_number, position)

        def _number_verify(self, value : int) -> None :
            if value < 0 or value >= self.__count :
                raise IndexError()

        def _get(self, number : int, motor_number : int) -> int :
            return self.__module._motor_coordinate_position_get(motor_number, number)

        def _set(self, number : int, motor_number : int, position : int) -> None :
            self.__module._motor_coordinate_position_set(motor_number, number, position)

    @property
    def coordinates(self) -> Coordinates :
        """Gets the coordinates of the module."""
        return self.__coordinates

    _MOTOR_CURRENT_PORTIONS         = 256
    _MOTOR_CURRENT_STEP_COUNT       = 32
    _MOTOR_CURRENT_STEP_SIZE        = _MOTOR_CURRENT_PORTIONS // _MOTOR_CURRENT_STEP_COUNT

    _MOTOR_VELOCITY_PORTIONS        = 2048
    _MOTOR_ACCELERATION_PORTIONS    = 2048

    # Base of pulse and ramp divisors.
    _MOTOR_DIVISOR_BASE = 2

    def __init__(
        self,
        port : Port,
        identity : int,
        motor_count : int,
        motor_current_maximum : int,
        motor_frequency_minimum : float,
        motor_frequency_maximum : float,
        motor_class : typing.Type['Motor'],
        coordinate_count : int
    ) -> None :
        identity_, firmware_version = self.__firmware_version_get(port)
        if identity_ != identity :
            raise ExceptionModuleIdentity()
        self.__port = port
        self.__identity = identity_
        self.__firmware_version = firmware_version
        self.__motor_current_minimum = motor_current_maximum // Module._MOTOR_CURRENT_STEP_COUNT
        self.__motor_current_maximum = motor_current_maximum
        self.__motor_frequency_minimum = motor_frequency_minimum
        self.__motor_frequency_maximum = motor_frequency_maximum
        self.__switch_limit_activity = not self._switch_limit_polarity_get()
        self.__coordinates = Module.Coordinates(self, coordinate_count, motor_count)
        self.__motors = tuple(
            motor_class(self, motor_number)
            for motor_number in range(motor_count)
        )

    def _motor_current_internal(self, value : int) -> int :
        """
        Converts a motor current from units of milliamperes into a portion of
        `_MOTOR_CURRENT_PORTIONS`.

        Values: [`motor_current_minimum`, `motor_current_maximum`]
        """
        if (
            value < self.__motor_current_minimum or
            value > self.__motor_current_maximum
        ) :
            raise ValueError('Current invalid.')
        return (
            (
                value * Module._MOTOR_CURRENT_PORTIONS +
                Module._MOTOR_CURRENT_PORTIONS - 1
            ) //
            self.__motor_current_maximum -
            Module._MOTOR_CURRENT_STEP_SIZE
        )

    def _motor_current_external(self, portion : int) -> int :
        """
        Converts a motor current from a portion of `_MOTOR_CURRENT_PORTIONS` into units of
        milliamperes.

        Values: [`motor_current_minimum`, `motor_current_maximum`]
        """
        portion_steps = (
            (portion + Module._MOTOR_CURRENT_STEP_SIZE) //
            Module._MOTOR_CURRENT_STEP_SIZE
        )
        return (
            self.__motor_current_maximum *
            portion_steps //
            Module._MOTOR_CURRENT_STEP_COUNT
        )
    
    def _axis_parameter_set(self, motor_number : int, parameter : int, value : int) -> None :
        self.__command_transceive(Module.__Command.SAP, parameter, motor_number, value)

    def _axis_parameter_get(self, motor_number : int, parameter : int) -> int :
        return self.__command_transceive(Module.__Command.GAP, parameter, motor_number)

    def _port_output_pullup_enabled_set(self, port_number : int, state : bool) -> None :
        """Sets if the pull-up resistors of the port is enabled."""
        self.__command_transceive(
            Module.__Command.SIO,
            port_number,
            Module.__SIO_BANK_PULLUP,
            int(state)
        )

    def _port_input_digital_get(self, port_number : int) -> bool :
        """Gets the status of an digital input port."""
        return bool(self.__command_transceive(
            Module.__Command.GIO,
            port_number,
            Module.__GIO_BANK_INPUT_DIGITAL
        ))

    def _port_input_analog_get(self, port_number : int) -> int :
        """Gets the state of an analog input port."""
        return self.__command_transceive(
            Module.__Command.GIO,
            port_number,
            Module.__GIO_BANK_INPUT_ANALOG
        )

    def _port_output_digital_get(self, port_number : int) -> bool :
        """Gets the state of an digital output port."""
        return bool(self.__command_transceive(
            Module.__Command.GIO,
            port_number,
            Module.__GIO_BANK_OUTPUT_DIGITAL
        ))

    def _switch_limit_polarity_set(self, polarity : bool) -> None :
        """Sets the polarity of the limit switches."""
        self.__parameter_set_bool(Module.__Parameter.SWITCH_LIMIT_POLARITY, polarity)

    def _switch_limit_polarity_get(self) -> bool :
        """Gets the polarity of the limit switches."""
        return self.__parameter_get_bool(Module.__Parameter.SWITCH_LIMIT_POLARITY)

    def _motor_coordinate_position_set(
        self,
        motor_number : int,
        coordinate_number : int,
        position : int
    ) -> None :
        self.__command_transceive(Module.__Command.SCO, coordinate_number, motor_number, position)

    def _motor_coordinate_position_get(
        self,
        motor_number : int,
        coordinate_number : int
    ) -> int :
        return self.__command_transceive(Module.__Command.GCO, coordinate_number, motor_number)

    def _motor_rotate_right(self, motor_number : int, velocity : int) -> None :
        self.__command_transceive(Module.__Command.ROR, 0, motor_number, velocity)

    def _motor_rotate_left(self, motor_number : int, velocity : int) -> None :
        self.__command_transceive(Module.__Command.ROL, 0, motor_number, velocity)

    def _motor_stop(self, motor_number : int) -> None :
        self.__command_transceive(Module.__Command.MST, 0, motor_number)

    def _motor_move_to(self, motor_number : int, position : int) -> None :
        self.__command_transceive(
            Module.__Command.MVP,
            Module.__MVP_TYPE_ABSOLUTE,
            motor_number,
            position
        )

    def _motor_move_to_coordinate(self, motor_number : int, coordinate_number : int) -> None :
        self.__command_transceive(
            Module.__Command.MVP,
            Module.__MVP_TYPE_COORDINATE,
            motor_number,
            coordinate_number
        )

    def _motor_move_by(self, motor_number : int, difference : int) -> None :
        self.__command_transceive(
            Module.__Command.MVP,
            Module.__MVP_TYPE_RELATIVE,
            motor_number,
            difference
        )

    __MODULE_NAME = 'tmcm_{:04d}.module'
    __CLASS_NAME = 'Module'

    class __Command(enum.IntEnum) :
        # Mnemonic commands
        # Rotate right
        ROR = 1,
        # Rotate left
        ROL = 2,
        # Motor stop
        MST = 3,
        # Move to position
        MVP = 4,
        # Set axis parameter
        SAP = 5,
        # Get axis parameter
        GAP = 6,
        # Set global parameter
        SGP = 9,
        # Get global parameter
        GGP = 10,
        # Set input/output
        SIO = 14,
        # Get input/output
        GIO = 15,
        # Set coordinate
        SCO = 30,
        # Get coordinate
        GCO = 31
        # Control commands
        CTL_FIRMWARE_VERSION_GET       = 136,
        CTL_FACTORY_SETTINGS_RESTORE   = 137

    class __Status(enum.IntEnum) :
        SUCCESS             = 100,
        COMMAND_LOADED      = 101,
        CHECKSUM_WRONG      = 1,
        COMMAND_INVALID     = 2,
        TYPE_WRONG          = 3,
        VALUE_INVALID       = 4,
        STORAGE_LOCKED      = 5,
        COMMAND_UNAVAILABLE = 6

    class __Parameter(enum.IntEnum) :
        SWITCH_LIMIT_POLARITY = 79

    __COMMAND_REPLY_LENGTH = 9
    __COMMAND_BYTE_ORDER = 'big'

    __MVP_TYPE_ABSOLUTE   = 0
    __MVP_TYPE_RELATIVE   = 1
    __MVP_TYPE_COORDINATE = 2

    __SIO_BANK_PULLUP         = 0
    __SIO_BANK_OUTPUT_DIGITAL = 2

    __GIO_BANK_INPUT_DIGITAL  = 0
    __GIO_BANK_INPUT_ANALOG   = 1
    __GIO_BANK_OUTPUT_DIGITAL = 2

    __CTL_FIRMWARE_VERSION_GET_TYPE_BINARY = 1

    __CTL_FACTORY_SETTINGS_RESTORE_VALUE = 1234

    @staticmethod
    def __command_checksum_calculate(data) -> int :
        return sum(data) & 0xFF

    @classmethod
    def __command_request_transfer_port(
        cls,
        port : Port,
        command_number : int,
        type_number : int,
        bank_number : int,
        value : int
    ) -> None :
        module_address = 0
        data = [
            module_address,
            command_number,
            type_number,
            bank_number,
            *value.to_bytes(4, byteorder = cls.__COMMAND_BYTE_ORDER, signed = True),
            0
        ]
        data[8] = cls.__command_checksum_calculate(data[0 : 8])
        # DEBUG
        # print(
        #     command_number.name,
        #     type_number.name if hasattr(type_number, 'name') else type_number,
        #     bank_number,
        #     value
        # )
        port.transfer(bytes(data))

    def __command_request_transfer(
        self,
        command_number : int,
        type_number : int = 0,
        bank_number : int = 0,
        value : int = 0
    ) -> None :
        Module.__command_request_transfer_port(
            self.__port,
            command_number,
            type_number,
            bank_number,
            value
        )

    @classmethod
    def __command_reply_receive_port(cls, port : Port) -> int :
        data = port.receive(Module.__COMMAND_REPLY_LENGTH)
        # Irrelevant for USB connections.
        # host_address = data[0]
        # Irrelevant for USB connections.
        # module_address = data[1]
        status = data[2]
        # Irrelevant.
        # command_number = data[3]
        value = int.from_bytes(data[4 : 8], byteorder = cls.__COMMAND_BYTE_ORDER, signed = True)
        checksum = data[8]
        if checksum != cls.__command_checksum_calculate(data[0 : 8]) :
            raise ExceptionChecksumReply()
        if status == cls.__Status.CHECKSUM_WRONG :
            raise ExceptionChecksumRequest()
        if status != cls.__Status.SUCCESS :
            raise ExceptionInternal()
        return value

    def __command_reply_receive(self) -> int :
        return Module.__command_reply_receive_port(self.__port)

    @classmethod
    def __command_transceive_port(
        cls,
        port : Port,
        command_number : int,
        type_number : int = 0,
        bank_number : int = 0,
        value : int = 0
    ) -> int :
        cls.__command_request_transfer_port(
            port,
            command_number,
            type_number,
            bank_number,
            value
        )
        value_return = cls.__command_reply_receive_port(port)
        # DEBUG
        # print(
        #     command_number.name,
        #     type_number.name if hasattr(type_number, 'name') else type_number,
        #     bank_number,
        #     value,
        #     value_return
        # )
        return value_return

    def __command_transceive(
        self,
        command_number: int,
        type_number: int = 0,
        bank_number: int = 0,
        value: int = 0
    ) -> int :
        return Module.__command_transceive_port(
            self.__port,
            command_number,
            type_number,
            bank_number,
            value
        )

    @classmethod
    def __firmware_version_get(cls, port : Port) -> (int, (int, int)) :
        value = cls.__command_transceive_port(
            port,
            Module.__Command.CTL_FIRMWARE_VERSION_GET,
            Module.__CTL_FIRMWARE_VERSION_GET_TYPE_BINARY
        )
        identity      = (value >> 16) & 0xFFFF
        version_major = (value >>  8) & 0xFF
        version_minor = (value      ) & 0xFF
        return (identity, (version_major, version_minor))

    def __factory_settings_restore(self) -> None :
        self.__command_request_transfer(
            Module.__Command.CTL_FACTORY_SETTINGS_RESTORE,
            0,
            0,
            Module.__CTL_FACTORY_SETTINGS_RESTORE_VALUE
        )

    def __parameter_set(self, parameter : __Parameter, value : int) -> None :
        self.__command_transceive(Module.__Command.SGP, parameter, 0, value)

    def __parameter_set_bool(self, parameter : __Parameter, state : bool) -> None :
        self.__parameter_set(parameter, int(state))

    def __parameter_get(self, parameter : __Parameter) -> int :
        return self.__command_transceive(Module.__Command.GGP, parameter)

    def __parameter_get_bool(self, parameter : __Parameter) -> bool :
        return bool(self.__parameter_get(parameter))