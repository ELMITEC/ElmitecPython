# -*- coding: utf-8 -*-

from typing import Optional, cast
import socket
from ._io import _cmd, Mode


class Leem2000:
    # Good defaults just in case
    __DEFAULT_PORT = 5566
    __DEFAULT_HOST = 'localhost'

    def __enter__(self):
        # If Leem2000 instance is not yet connected to U-View, connect it now
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
            self.__host = Leem2000.__DEFAULT_HOST
        else:
            self.__host = host
        if not isinstance(port, int) or port < 0 or port > 65535:
            self.__port = Leem2000.__DEFAULT_PORT
        else:
            self.__port = port
        self.connected = False
        self.__sock = None

    def __repr__(self):
        return f"<elmitec.Leem2000('{self.__host}',{self.__port}) instance at {hex(id(self))}>"

    def __str__(self):
        return f"Instance of Leem2000 class at {hex(id(self))}:\n  Host: '{self.__host}', Port: {self.__port}\n" + \
               f"  Connected: {self.connected}"

    def number_of_modules(self) -> Optional[int]:
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            return _cmd(self.__sock, "nrm", Mode.INTEGER)  # type: ignore

    def update_values(self):
        """Update mnemonic map with values from all modules"""
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            self.values = {}
            for x in self.mnemonic:
                data = cast(str, _cmd(self.__sock, f"get {x}"))
                try:
                    self.values[x] = float(data)
                except ValueError:
                    pass
    
    def update_modules(self):
        """Update internal maps containing information about all available modules"""
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            self.nrModules = cast(int, self.number_of_modules())
            self.name = {}
            self.mnemonic = {}
            self.idByName = {}
            self.idByMnemonic = {}
            self.lowLimit = {}
            self.highLimit = {}
            self.unit = {}
            for x in range(self.nrModules):
                name = cast(str, _cmd(self.__sock, f"nam {x}"))
                if not name in ["", "no name", "invalid", "disabled"]:
                    self.name[x] = name
                    self.idByName[name.upper()] = x
                mnemonic = cast(str, _cmd(self.__sock, f"mne {x}"))
                if not mnemonic in ["", "no name", "invalid", "disabled"]:
                    self.mnemonic[x] = mnemonic
                    self.idByMnemonic[mnemonic.upper()] = x
                if x in self.name.keys():
                    unit = cast(str, _cmd(self.__sock, f"uni {x}"))
                    if not unit in ["", "no name", "invalid", "disabled"]:
                        self.unit[x] = unit
                low = cast(str, _cmd(self.__sock, f"psl {x}"))
                if not low in ["", "no name", "invalid", "disabled"]:
                    self.lowLimit[x] = float(low)
                high = cast(str, _cmd(self.__sock, f"psh {x}"))
                if not high in ["", "no name", "invalid", "disabled"]:
                    self.highLimit[x] = float(high)
    
    def version(self) -> float:
        """Obtain U-view version returned as a float type or None if not connected."""
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            return cast(float, _cmd(self.__sock, "ver", Mode.FLOAT))

    def connect(self):
        """Establish new connection with Leem2000 software. Does nothing if
        already connected."""
        if not self.connected:
            addr = (self.__host, self.__port)
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__sock.connect(addr)
            self.connected = True
            self.update_modules()
            self.update_values()

    def disconnect(self):
        """Disconnect from Leem2000."""
        if self.connected and self.__sock is not None:
            self.__sock.close()
            self.__sock = None
            self.connected = False

    def set_port(self, port):
        """Set port for establishing new connection. Raises a ValueError exception if
        port number is not in the valid range (0..65535). Raises TypeError exception
        if port is not an integer."""
        if isinstance(port, int):
            if port >= 0 and port < 65536:
                self.__port = port
            else:
                raise ValueError('Port number must be an integer in range 0..65535')
        else:
            raise TypeError('Port number must be of integer type')

    def port(self) -> int:
        return self.__port

    def set_host(self, host):
        """Set host name either in textual form or as an IP address. In both
        cases it must be a string, otherwise TypeError will be thrown."""
        if not isinstance(host, str):
            raise TypeError('Host must be a valig string')
        else:
            self.__host = host

    def host(self) -> str:
        return self.__host

    def get_value(self, id) -> float:
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            return cast(float, _cmd(self.__sock, f"get {id}", Mode.FLOAT))

    def set_value(self, id, value) -> bool:
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if isinstance(id, str):
                    if not id.upper() in self.idByName.keys() and not id.upper() in self.idByMnemonic.keys():
                        return False
                elif not isinstance(id, int) or isinstance(id, float):
                    raise TypeError("Id must be an integer or string")
                
                ret = cast(str, _cmd(self.__sock, f"set {id}={value}"))
                return ret == '0'
            else:
                raise TypeError('Value must be of float type')
    
    def get_low_limit(self, id) -> Optional[float]:
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            if isinstance(id, str):
                if id.upper() in self.idByName.keys():
                    id = self.idByName[id.upper()]
                elif id.upper() in self.idByMnemonic.keys():
                    id = self.idByMnemonic[id.upper()]
                else:
                    return None
            elif not isinstance(id, int) or isinstance(id, float):
                raise TypeError("Id must be an integer or string")
                
            return cast(float, _cmd(self.__sock, f"psl {id}", Mode.FLOAT))

    def get_high_limit(self, id) -> Optional[float]:
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            if isinstance(id, str):
                if id.upper() in self.idByName.keys():
                    id = self.idByName[id.upper()]
                elif id.upper() in self.idByMnemonic.keys():
                    id = self.idByMnemonic[id.upper()]
                else:
                    return None
            elif not isinstance(id, int) or isinstance(id, float):
                raise TypeError("Id must be an integer or string")
                
            return cast(float, _cmd(self.__sock, f"psh {id}", Mode.FLOAT))

    def get_fov(self):
        """Get Field-of-View from current preset"""
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            data = cast(str, _cmd(self.__sock, "prl"))
            part = data.partition('µ')
            if part[1] == 'µ':
                try:
                    fov = float(part[0])
                    return (fov, True)
                except:
                    return (data, False)
            return (data, False)

    def get_modified_modules(self):
        """Get names and values from modules which changed"""
        if not self.connected:
            raise ConnectionError("Not connected to LEEM2000")
        else:
            data = cast(str, _cmd(self.__sock, 'chm'))
            if data != '0':
                items = data.split()
                nchanges = int(items[0])
                chg = []
                for i in range(nchanges):
                    idx = int(items[2 * i + 1])
                    val = float(items[2 * i + 2])
                    if idx in self.name.keys():
                        name = self.name[idx]
                    else:
                        name = f"Unknown{idx}"
                    chg.append({ 'moduleName': name, 'moduleNr': idx, 'newValue': val })
                return (nchanges, chg)
        return (0, None)
