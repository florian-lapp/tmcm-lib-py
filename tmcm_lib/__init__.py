"""TMCM-Lib – Trinamic Motion Control Module Library for Python"""

VERSION = '1.0.0'
"""Version of TMCM-Lib."""

from .port import Port
from .module import Module
from .motor import Motor
from .motor_union import MotorUnion
from .switch import Switch
from .exceptions import *

from .module_3110.module import Module as Module_3110