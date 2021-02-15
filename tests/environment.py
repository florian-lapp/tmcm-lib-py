from tmcm_lib.port import Port
from tmcm_lib.module import Module
from tmcm_lib.motor import Motor

import typing

class __Environment :

    PORT_NAME = 'COM1'
    # Millivolts.
    SUPPLY_VOLTAGE = 24000
    # Millivolts.
    SUPPLY_VOLTAGE_TOLERANCE = 1000

    MOTOR_NUMBERS = (0, 1)
    # Milliamperes.
    MOTOR_CURRENT_MOVING = 173
    # Milliamperes.
    MOTOR_CURRENT_STANDBY = 86
    # Microsteps per fullstep.
    MOTOR_MICROSTEP_RESOLUTION = 256
    # Fullsteps per second.
    MOTOR_VELOCITY_MOVING = 800.0
    # Fullsteps per square second.
    MOTOR_ACCELERATION_MOVING = 1600.0
    # Fullsteps per revolution.
    MOTOR_STEPS = 200

    @property
    def port(self) -> Port :
        return self.__port

    @property
    def module(self) -> Module :
        return self.__module

    @property
    def motors(self) -> typing.Tuple[Motor, ...] :
        return self.__motors

    def reset(self) -> None :
        for motor in self.__module.motors :
            motor.stop()
            motor.current_moving = self.MOTOR_CURRENT_MOVING
            motor.current_standby = self.MOTOR_CURRENT_STANDBY
            motor.microstep_resolution = self.MOTOR_MICROSTEP_RESOLUTION
            motor.velocity_moving = self.MOTOR_VELOCITY_MOVING
            motor.acceleration_moving = self.MOTOR_ACCELERATION_MOVING
            motor.position = 0

    def __init__(self) -> None :
        port = Port(self.PORT_NAME)
        module = Module.construct(port)
        motors = module.motors
        self.__port = port
        self.__module = module
        self.__motors = tuple(motors[number] for number in self.MOTOR_NUMBERS)
        self.reset()

instance = __Environment()