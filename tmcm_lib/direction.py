import enum

class Direction(enum.IntEnum) :
    """
    Direction of a motor movement.

    Movement in right direction is a clockwise rotation.
    Movement in left direction is a counterclockwise rotation.
    """
    NONE  =  0,
    RIGHT = +1,
    LEFT  = -1