"""BlinkyTape Python communication library.

  This code assumes stock serialLoop() in the firmware.

  Commands are issued in 3-byte blocks, with pixel data
  encoded in RGB triplets in range 0-254, sent sequentially
  and a triplet ending with a 255 causes the accumulated pixel
  data to display (a show command).

  Note that with the stock firmware changing the maximum brightness
  over serial communication is impossible.
"""

import serial
import listports
import time

class BlinkyTape(object):
    def __init__(self, port=None, ledCount=60, buffered=True):
        """Creates a BlinkyTape object and opens the port.

        Parameters:
          port
            Optional, port name as accepted by PySerial library:
            http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial
            It is the same port name that is used in Arduino IDE.
            Ex.: COM5 (Windows), /dev/ttyACM0 (Linux).
            If no port is specified, the library will attempt to connect
            to the first port that looks like a BlinkyTape.
          ledCount
            Optional, total number of LEDs to work with,
            defaults to 60 LEDs. The limit is enforced and an
            attempt to send more pixel data will throw an exception.
          buffered
            Optional, enabled by default. If enabled, will buffer
            pixel data until a show command is issued. If disabled,
            the data will be sent in byte triplets as expected by firmware,
            with immediate flush of the serial buffers (slower).

        """

        # If a port was not specified, try to find one and connect automatically
        if port == None:
            ports = listports.listPorts()
            if len(ports) == 0:
                raise IOError("BlinkyTape not found!")
        
            port = listports.listPorts()[0]

        self.port = port                # Path of the serial port to connect to
        self.ledCount = ledCount        # Number of LEDs on the BlinkyTape
        self.buffered = buffered        # If Frue, buffer output data before sending
        self.buf = ""                   # Color data to send
        self.serial = serial.Serial(port, 115200)

        #self.show()  # Flush any incomplete data

    def send_list(self, colors):
        if len(colors) > self.ledCount:
            raise RuntimeError("Attempting to set pixel outside range!")
        for r, g, b in colors:
            self.sendPixel(r, g, b)
        self.show()

    def send_list(self, colors):
        data = ""
        for r, g, b in colors:
            if r >= 255:
                r = 254
            if g >= 255:
                g = 254
            if b >= 255:
                b = 254
            data += chr(r) + chr(g) + chr(b)
        self.serial.write(data)
        self.show()

    def sendPixel(self, r, g, b):
        """Sends the next pixel data triplet in RGB format.

        Values are clamped to 0-254 automatically.

        Throws a RuntimeException if [ledCount] pixels are already set.
        """
        data = ""
        if r < 0:
            r = 0
        if g < 0:
            g = 0
        if b < 0:
            b = 0
        if r >= 255:
            r = 254
        if g >= 255:
            g = 254
        if b >= 255:
            b = 254
        data = chr(r) + chr(g) + chr(b)
        if len(data)*3 < self.ledCount:
            if self.buffered:
                self.buf += data
            else:
                self.serial.write(data)
                self.serial.flush()
        else:
            raise RuntimeError("Attempting to set pixel outside range!")

    def show(self):
        """Sends the command(s) to display all accumulated pixel data.

        Resets the pixel buffer, flushes the serial buffer,
        and discards any accumulated responses from BlinkyTape.
        """
        control = chr(0) + chr(0) + chr(255)
        if self.buffered:
            self.serial.write(self.buf + control)
            self.buf = ""
        else:
            self.serial.write(control)
        self.serial.flush()
        self.serial.flushInput()  # Clear responses from BlinkyTape, if any

    def displayColor(self, r, g, b):
        """Fills [ledCount] pixels with RGB color and shows it."""
        for i in range(0, self.ledCount):
            self.sendPixel(r, g, b)
        self.show()

    def resetToBootloader(self):
        """Initiates a reset on BlinkyTape.

        Note that it will be disconnected.
        """
        self.serial.setBaudrate(1200)
        self.close()

    def sendCommand(self, command):
        
        controlEscapeSequence = ""
        for i in range(0,10):
            controlEscapeSequence += chr(255);

        self.serial.write(controlEscapeSequence)
        self.serial.write(command)
        self.serial.flush()

        # give a small pause and wait for data to be returned
        time.sleep(.01)
        ret = self.serial.read(2)

        status = (ret[0] == 'P')
        returnData = ""

        returnData = self.serial.read(ord(ret[1]) + 1)

        self.serial.flushInput()
        return status, returnData

    def programAddress(self, address):
        """Run the program address command (for WS2821/WS2822s only)
        """
        command = chr(0x01)
        command += chr((address >> 8) & 0xFF)   # 2 bytes address (0-1024 or so)
        command += chr(address        & 0xFF)

        self.sendCommand(command)

    def reloadAnimations(self):
        """Tell the animation system to reload
        """
        command = chr(0x02)

        self.sendCommand(command)

    def getFreeSpace(self):
        """Get the amount of free space on the flash
        """

        command = chr(0x10)

        status, returnData = self.sendCommand(command)

        space = 0
        if status:
            space += ord(returnData[0]) << 24
            space += ord(returnData[1]) << 16
            space += ord(returnData[2]) << 8
            space += ord(returnData[3]) << 0

        return space

    def getLargestFile(self):
        """Get the size of the largest file that can be created
        """

        command = chr(0x11)

        status, returnData = self.sendCommand(command)

        space = 0
        if status:
            space += ord(returnData[0]) << 24
            space += ord(returnData[1]) << 16
            space += ord(returnData[2]) << 8
            space += ord(returnData[3]) << 0

        return space

    def getFileCount(self):
        """Get the number of files in the file system
        """

        command = chr(0x12)

        status, returnData = self.sendCommand(command)

        space = 0
        if status:
            space += ord(returnData[0]) << 24
            space += ord(returnData[1]) << 16
            space += ord(returnData[2]) << 8
            space += ord(returnData[3]) << 0

        return space

    def getFirstFreeSector(self):
        """Get the first free sector in the flash
        """

        command = chr(0x13)

        status, returnData = self.sendCommand(command)

        sector = 0
        if status:
            sector += ord(returnData[0]) << 24
            sector += ord(returnData[1]) << 16
            sector += ord(returnData[2]) << 8
            sector += ord(returnData[3]) << 0

        return sector

    def getIsFile(self, sector):
        """Tests if the file exists, and gets the type if it does
        """

        command = chr(0x14)
        command += chr((sector >> 24) & 0xFF)
        command += chr((sector >> 16) & 0xFF)
        command += chr((sector >>  8) & 0xFF)
        command += chr((sector      ) & 0xFF)
        status, returnData = self.sendCommand(command)

        fileType = 0
        if status:
            fileType += ord(returnData[0]) << 24
            fileType += ord(returnData[1]) << 16
            fileType += ord(returnData[2]) << 8
            fileType += ord(returnData[3]) << 0

        return status, fileType

    def deleteFile(self, sector):
        """Delete a file
        """

        command = chr(0x15)
        command += chr((sector >> 24) & 0xFF)
        command += chr((sector >> 16) & 0xFF)
        command += chr((sector >>  8) & 0xFF)
        command += chr((sector      ) & 0xFF)
        status, returnData = self.sendCommand(command)

        return status

    def createFile(self, fileType, fileLength):
        """Store a file into the external flash memory
        """

        command = chr(0x18)
        command += chr(fileType           & 0xFF)
        command += chr((fileLength >> 24) & 0xFF)
        command += chr((fileLength >> 16) & 0xFF)
        command += chr((fileLength >>  8) & 0xFF)
        command += chr((fileLength      ) & 0xFF)
        status, returnData = self.sendCommand(command)

        sector = 0
        if status:
            sector += ord(returnData[0]) << 24
            sector += ord(returnData[1]) << 16
            sector += ord(returnData[2]) << 8
            sector += ord(returnData[3]) << 0

        return status, sector 

    def writeFilePage(self, sector, offset, data):
        """Write one page (256 bytes) of data to the specified animation
        """
        if len(data) != 256:
            return False

        command = chr(0x19)
        command += chr((sector >> 24) & 0xFF)
        command += chr((sector >> 16) & 0xFF)
        command += chr((sector >>  8) & 0xFF)
        command += chr((sector      ) & 0xFF)
        command += chr((offset >> 24) & 0xFF)
        command += chr((offset >> 16) & 0xFF)
        command += chr((offset >>  8) & 0xFF)
        command += chr((offset      ) & 0xFF)
        command += data

        status, returnData = self.sendCommand(command)

        return status

    def readFileData(self, sector, offset, length):
        """Read some data (up to 256 bytes) from a file
        """
        if length > 256:
            return False

        command = chr(0x1A)
        command += chr((sector >> 24) & 0xFF)
        command += chr((sector >> 16) & 0xFF)
        command += chr((sector >>  8) & 0xFF)
        command += chr((sector      ) & 0xFF)
        command += chr((offset >> 24) & 0xFF)
        command += chr((offset >> 16) & 0xFF)
        command += chr((offset >>  8) & 0xFF)
        command += chr((offset      ) & 0xFF)
        command += chr(length - 1     & 0xFF)

        return self.sendCommand(command)

    def flashErase(self):
        """Erase the entire external flash memory
        """
        command = chr(0x20)
        command += 'E'
        command += 'e'

        self.sendCommand(command)

    def flashRead(self, address, length):
        """Read a page of data from the flash
        """
        
        command = chr(0x21)
        command += chr((address >> 24) & 0xFF)
        command += chr((address >> 16) & 0xFF)
        command += chr((address >>  8) & 0xFF)
        command += chr((address >>  0) & 0xFF)
        command += chr((length >> 24) & 0xFF)
        command += chr((length >> 16) & 0xFF)
        command += chr((length >>  8) & 0xFF)
        command += chr((length >>  0) & 0xFF)

        return self.sendCommand(command)

    def close(self):
        """Safely closes the serial port."""
        self.serial.close()


# Example code

if __name__ == "__main__":

    import glob
    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-p", "--port", dest="portname",
                      help="serial port (ex: /dev/ttyUSB0)", default=None)
    (options, args) = parser.parse_args()

    port = options.portname

    bt = BlinkyTape(port)

    bt.programAddress(2)
    time.sleep(2)

    while True:
        for pixel in range(0, 12):
            for pos in range(0, 12):
                if pos == pixel:
                    bt.sendPixel(0,0,255)
                else:
                    bt.sendPixel(0,0,0)
            bt.show()
            time.sleep(.5)
