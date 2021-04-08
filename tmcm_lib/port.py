import serial

class Port :
    """Port a module is connected to."""

    BAUD_RATE_DEFAULT = 9600
    """Default baud rate."""

    class Unavailability(Exception) :
        """Exception that indicates the unavailability of a port."""
        pass

    def __init__(self, name : str, baud_rate : int = BAUD_RATE_DEFAULT) -> None :
        """
        Constructs a port.

        :param name:
            Name of the port.
        :param baud_rate:
            Baud rate at which data is exchanged via the port.
        :raises ValueError:
            The baud rate is invalid or not supported by the port.
        :raises Unavailability:
            The port is unavailable (e.g. in use or not connected).
        """
        try :
            self.__serial = serial.Serial(
                port = name,
                baudrate = baud_rate
            )
        except ValueError :
            raise ValueError('Baud rate invalid.')
        except serial.SerialException :
            raise Port.Unavailability()

    def _transmit(self, data : bytes) -> None :
        """
        Transmits data to the port.

        :param data:
            Data to transmit.
        """
        self.__serial.write(data)

    def _receive(self, data_length : int) -> bytes :
        """
        Receives data from the port.

        :param data_length:
            Length of the data to receive.
        """
        return self.__serial.read(data_length)