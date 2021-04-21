from tests.test_module import TestModule as TestModuleGeneric
from tmcm_lib.tmcm_3110.module import Module

class TestModule(TestModuleGeneric) :

    CLASS = Module
    MODEL_NUMBER = 3110
    FIRMWARE_VERSION = (1, 14)
    MOTOR_COUNT = 3
    MOTOR_CURRENT_MINIMUM = 86
    MOTOR_CURRENT_MAXIMUM = 2768
    MOTOR_FREQUENCY_MINIMUM = 0.029802322387695312
    MOTOR_FREQUENCY_MAXIMUM = 499755.859375
    COORDINATE_COUNT = 20