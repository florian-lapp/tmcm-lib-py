import serial

class Port :

    class Unavailability(Exception) :
        pass

    def __init__(self, name : str, baud_rate : int = 0) -> None :
        try :
            self.__serial = serial.Serial(
                port = name,
                baudrate = baud_rate
            )
        except ValueError :
            raise ValueError('Baud rate invalid.')
        except serial.SerialException :
            raise Port.Unavailability()

    def transfer(self, data : bytes) -> None :
        self.__serial.write(data)

    def receive(self, data_length) -> bytes :
        return self.__serial.read(data_length)

    def transceive(self, data_transfer : bytes, data_receive_length : int) -> bytes :
        self.transfer(data_transfer)
        return self.receive(data_receive_length)