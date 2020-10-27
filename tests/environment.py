from tmcm_lib.port import Port
from tmcm_lib.module import Module

class __Environment :

    PORT_NAME = 'COM1'
    # Millivolts.
    SUPPLY_VOLTAGE = 24000
    # Millivolts.
    SUPPLY_VOLTAGE_TOLERANCE = 1000
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

    def reset(self) -> None :
        for motor in self.__module.motors :
            motor.stop()
            motor.position = 0
            motor.current_moving = self.MOTOR_CURRENT_MOVING
            motor.current_standby = self.MOTOR_CURRENT_STANDBY
            motor.microstep_resolution = self.MOTOR_MICROSTEP_RESOLUTION
            motor.velocity_moving = self.MOTOR_VELOCITY_MOVING
            motor.acceleration_moving = self.MOTOR_ACCELERATION_MOVING

    def __init__(self) :
        port = Port(self.PORT_NAME)
        module = Module.construct(port)
        self.__port = port
        self.__module = module
        self.reset()

instance = __Environment()