import enum
import typing

if typing.TYPE_CHECKING :
    from .motor import Motor

class Switch :

    class Type(enum.IntEnum) :
        """Type of a switch."""

        # Right limit switch.
        LIMIT_RIGHT = 0,
        # Left limit switch.
        LIMIT_LEFT  = 1,
        # Home switch.
        HOME        = 2

    def __init__(self, motor : 'Motor', type : Type) :
        self.__motor = motor
        self.__type = type
        functions = Switch.__FUNCTIONS[type]
        from .motor import Motor
        self.__disabled_set = getattr(Motor, functions['disabled_set'], None)
        self.__disabled_get = getattr(Motor, functions['disabled_get'], None)
        self.__active_get = getattr(Motor, functions['active_get'])
        self.__enabled = not self.__disabled_get(motor) if self.__disabled_get else True

    @property
    def motor(self) -> 'Motor' :
        """Gets the motor of the switch."""
        return self.__motor

    @property
    def type(self) -> Type :
        """Gets the type of the switch."""
        return self.__type

    @property
    def enabled(self) -> bool :
        """
        Gets if the switch is enabled.

        Note: The home switch always is enabled.
        """
        return self.__enabled

    @enabled.setter
    def enabled(self, state : bool) -> None :
        """
        Sets if the switch is enabled.

        Note: The home switch can not be disabled.
        """
        if not self.__disabled_set :
            return
        self.__disabled_set(self.__motor, not state)
        self.__enabled = state

    @property
    def active(self) -> bool :
        """Gets if the switch is active."""
        return self.__active_get(self.__motor)

    __FUNCTIONS = {
        # Type.LIMIT_RIGHT
        0 : {
            'disabled_set' : '_switch_limit_right_disabled_set',
            'disabled_get' : '_switch_limit_right_disabled_get',
            'active_get'   : '_switch_limit_right_active_get'
        },
        # Type.LIMIT_LEFT
        1 : {
            'disabled_set' : '_switch_limit_left_disabled_set',
            'disabled_get' : '_switch_limit_left_disabled_get',
            'active_get'   : '_switch_limit_left_active_get'
        },
        # Type.HOME (Can not be disabled)
        2 : {
            # Nonexistent.
            'disabled_set' : '_switch_home_disabled_set',
            # Nonexistent.
            'disabled_get' : '_switch_home_disabled_get',
            'active_get'   : '_switch_home_active_get'
        }
    }