# -*- coding: utf-8 -*-

from enum import Enum, auto
from typing import Optional, cast
from ._io import _cmd, _receive, Mode
import socket
import numpy as np


class FileFormat(Enum):
    DAT = 0
    PNG = 1
    TIFF = 2
    BMP = 3
    JPG = 4
    TIFF16 = 5


class FileContents(Enum):
    PROCESSED = 0
    RAW = 1
    GRAY16 = 2


class MarkerType(Enum):
    LINE = auto()
    HORIZLINE = auto()
    VERTLINE = auto()
    CIRCLE = auto()
    TEXT = auto()
    CROSS = auto()
    UNKNOWN = auto()


class UView:
    # Good defaults just in case
    __DEFAULT_PORT = 5570
    __DEFAULT_HOST = 'localhost'

    def __enter__(self):
        # If UView instance is not yet connected to U-View, connect it now
        # and mark that the instance shall automatically disconnect on
        # __exit__ call
        if not self.connected:
            self.connect()
            self.__disconnect_on_exit = True
        else:
            self.__disconnect_on_exit = False
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.__disconnect_on_exit:
            self.disconnect()

    def __init__(self, host=None, port=None):
        if not isinstance(host, str):
            self.__host = UView.__DEFAULT_HOST
        else:
            self.__host = host
        if not isinstance(port, int) or port < 0 or port > 65535:
            self.__port = UView.__DEFAULT_PORT
        else:
            self.__port = port
        self.connected = False
        self.__sock = None
    
    def __repr__(self):
        return f"<elmitec.UView('{self.__host}',{self.__port}) instance at {hex(id(self))}>"

    def __str__(self):
        return f"Instance of UView class at {hex(id(self))}:\n  Host: '{self.__host}', Port: {self.__port}\n" + \
               f"  Connected: {self.connected}"

    def get_image(self) -> Optional[np.ndarray]:
        """Load image data from currently active window. Returns None if not connected,
        otherwise two-dimensional NumPy array of cell type uin16 is returned."""
        if not self.connected:
            return None
        else:
            header = _cmd(self.__sock, "ida 0 0", Mode.BINARY, 19).decode('ascii')
            items = header.split()
            if len(items) != 3:
                return None
            width = int(items[1])
            height = int(items[2])
            image = _receive(self.__sock, Mode.BINARY, width * height * 2)
            image = np.frombuffer(image, np.uint16)
            _receive(self.__sock, Mode.BINARY, 1)
            return image.reshape((width, height))
    
    def export_image(self, name: str, format: FileFormat = FileFormat.DAT, contents: FileContents = FileContents.PROCESSED):
        """Exports the current image to a file stored on the machine where U-view software is running.
        The filename must be a valid string containing the PC-style filename without extension.
        Supported formats and file contents are:

        FileFormat.DAT - uncompressed 16-bit RAW data with overlay included in the file. The contents
        parameter is ignored.

        FileFormat.PNG - compressed image with RGB888 with x,y,z as seen on screen (FileContents.PROCESSED)
        RGB888 with x,y raw and z as seen on screen (FileContents.RAW) or RGB16 gray level image, x,y,z raw
        (FileContents.GRAY16)

        FileFormat.TIFF - compressed image with RGB888 with x,y,z as seen on screen (FileContents.PROCESSED)
        or RGB888 with x,y raw and z as seen on screen (FileContents.RAW)

        FileFormat.BMP - uncompressed image with RGB888 with x,y,z as seen on screen (FileContents.PROCESSED)
        or RGB888 with x,y raw and z as seen on screen (FileContents.RAW)

        FileFormat.JPG - compressed with quality as set in 'Save as Dialog' with RGB888 with x,y,z as seen
        on screen (FileContents.PROCESSED)

        FileFormat.TIFF16 - uncompressed 16-bit RAW x,y,z data. The contents parameter is ignored."""
        if not isinstance(name, str) or name == "":
            raise ValueError("Invalid filename")
        elif len(name) >= 260:
            raise ValueError("Filename too long")
        else:
            match format:
                case FileFormat.TIFF, FileFormat.BMP:
                    if contents == FileContents.GRAY16:
                        raise ValueError(f"GRAY16 format not supported in {format.name}")
                case FileFormat.JPG:
                    if contents != FileContents.PROCESSED:
                        raise ValueError(f"JPG format supports only {FileContents.PROCESSED.name}")
            retval = _cmd(self.__sock, f"exp {format.value}, {contents.value}, {name}")
            retval = retval.split()
            if len(retval) == 2 and retval[0] == "ErrorCode":
                raise SystemError(f"Received error code {retval[1]} from U-view")
    
    def set_averaging(self, avg: int):
        """Set U-view averaging mode. Valid argument is an integer from 0 to 499:
        0 - disables averaging,
        1 - enables sliding average mode,
        2..499 - set number of images for averaging to given value."""
        if not isinstance(avg, int) or avg < 0 or avg > 499:
            raise ValueError("avg parameter not an integer or out of range (0..499)")
        if self.connected:
            _cmd(self.__sock, f"avr {avg}")

    def averaging(self) -> Optional[int]:
        """Return averaging mode used by U-View or None if not connected. Retured value
        gives number of images used for averaging (value 2 and larger), indicates
        sliding average mode (value 1) or indicates disabled averaging (value 0)."""
        if not self.connected:
            return None
        else:
            return _cmd(self.__sock, "avr", Mode.INTEGER)

    def acquire_single_image(self, window: int = -1):
        """Set camera to receive a single image and put it into a window specified by
        supplied argument. If window number -1 is given, the image will be put into
        the active window."""
        if not isinstance(window, int) or window < -1:
            window = -1
        if not self.connected:
            return None
        else:
            _cmd(self.__sock, f"asi {window}")
    
    def acquisition_in_progress(self) -> Optional[bool]:
        """Get current status of image acquisition. Returns True of acquisition is in
        progress, False otherwise. Returns None if not connected to U-view."""
        if not self.connected:
            return None
        else:
            aip = _cmd(self.__sock, "aip", Mode.INTEGER)
            if aip == 0:
                return False
            else:
                return True

    def set_continuous_acquisition(self, continuous: bool = True):
        """Enable/disable continous acquisition in U-view."""
        if self.connected:
            if continuous:
                _cmd(self.__sock, "aip 1")
            else:
                _cmd(self.__sock, "aip 0")

    def get_camera_size(self) -> Optional[tuple]:
        """Returns a tuple giving the size of camera sensor in form (width, height)."""
        if not self.connected:
            return None
        else:
            size = _cmd(self.__sock, "gcs").split()
            if len(size) != 2:
                return None
            else:
                return (int(size[0]), int(size[1]))

    def get_roi(self) -> Optional[tuple]:
        """Returns region of interest (ROI) of active window. Returns a tuple containing
        of four floats: (minimum X, minimum Y, maximum X, maximum Y) or None if not
        connected"""
        if not self.connected:
            return None
        else:
            xmi = _cmd(self.__sock, "xmi", Mode.FLOAT)
            ymi = _cmd(self.__sock, "ymi", Mode.FLOAT)
            xma = _cmd(self.__sock, "xma", Mode.FLOAT)
            yma = _cmd(self.__sock, "yma", Mode.FLOAT)
            return (xmi, ymi, xma, yma)
    
    def get_marker_info(self, id: int) -> Optional[dict]:
        """Returns a dictionary containing information about marker specified by id passed
        as a parameter or null if marker is invalid or class not connected to U-view."""
        if not self.connected or not isinstance(id, int) or id < 0:
            return None
        else:
            reply = _cmd(self.__sock, f"mar {id}").split()
            if len(reply) != 7:
                return None
            match int(reply[2]):
                case 0:  type = MarkerType.LINE
                case 1:  type = MarkerType.HORIZLINE
                case 2:  type = MarkerType.VERTLINE
                case 5:  type = MarkerType.CIRCLE
                case 9:  type = MarkerType.TEXT
                case 10: type = MarkerType.CROSS
                case _:  type = MarkerType.UNKNOWN
            info = {
                "marker": id,
                "markerName": reply[0],
                "imgNr": int(reply[1]),
                "type": type,
                "typeNr": int(reply[2]),
                "pos": (int(reply[3]), int(reply[4]), int(reply[5]), int(reply[6]))}
            return info
    
    def exposure_time(self) -> Optional[float]:
        """Returns current exposure time in milliseconds or None, if not connected."""
        if not self.connected:
            return None
        else:
            return _cmd(self.__sock, "ext", Mode.FLOAT)

    def set_exposure_time(self, exposure: float):
        """Set exposure time in millisecond. The argument is float, but decimal part is
        ignored."""
        if self.connected:
            _cmd(self.__sock, f"ext {exposure:.0f}")

    def version(self) -> Optional[float]:
        """Obtain U-view version returned as a float type or None if not connected."""
        if not self.connected:
            return None
        else:
            return _cmd(self.__sock, "ver", Mode.FLOAT)

    def connect(self):
        """Establish new connection with U-view software. Does nothing if
        already connected."""
        if not self.connected:
            addr = (self.__host, self.__port)
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__sock.connect(addr)
            self.connected = True
    
    def disconnect(self):
        """Disconnect from U-view."""
        if self.connected and self.__sock is not None:
            self.__sock.close()
            self.__sock = None
            self.connected = False

    def set_port(self, port):
        """Set port for establishing new connection. Raises a ValueError exception if
        port number is not in the valid range (0..65535)."""
        if isinstance(port, int) and port >= 0 and port < 65536:
            self.__port = port
        else:
            raise ValueError('Port number must be an integer in range 0..65535')

    def port(self) -> int:
        return self.__port

    def set_host(self, host):
        """Set host name either in textual form or as an IP address. In both
        cases it must be a string, otherwise ValueException will be thrown."""
        if not isinstance(host, str):
            raise ValueError('host must be a valig string')
        else:
            self.__host = host

    def host(self) -> str:
        return self.__host

