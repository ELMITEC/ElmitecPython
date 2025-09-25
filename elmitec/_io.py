# -*- coding: utf-8 -*-

from enum import Enum, auto


class Mode(Enum):
    STRING = auto()
    INTEGER = auto()
    FLOAT = auto()
    BINARY = auto()


def _send(sock, data, mode = Mode.STRING, delim = True):
    match mode:
        case Mode.STRING:
            if delim:
                sock.send((data + '\x00').encode('ascii'))
            else:
                sock.send(data.encode('ascii'))
        case Mode.BINARY:
            sock.send(data)
        case Mode.INTEGER:
            if delim:
                sock.send((str(data) + '\x00').encode('ascii'))
            else:
                sock.send(str(data).encode('ascii'))
        case _:
            pass


def _receive(sock, mode = Mode.STRING, length = -1):
    match mode:
        case Mode.BINARY:
            if length <= 0:
                raise ValueError()
            else:
                total_read = 0
                data = bytearray()
                while total_read < length:
                    tmp = sock.recv(length - total_read)
                    data += tmp
                    total_read += len(tmp)
                return data
        case Mode.STRING:
            terminate = False
            s = ''
            while not terminate:
                buff = sock.recv(1)
                if len(buff) == 0 or buff[0] == 0:
                    terminate = True
                else:
                    s += buff.decode('iso8859-1')
            return s
        case Mode.INTEGER:
            str = _receive(sock, Mode.STRING)
            if len(str) > 0:
                return int(str)
            else:
                return None
        case Mode.FLOAT:
            str = _receive(sock, Mode.STRING)
            if len(str) > 0:
                return float(str)
            else:
                return None
        case _:
            return None


def _cmd(sock, command: str, mode = Mode.STRING, length = -1):
    _send(sock, command)
    return _receive(sock, mode, length)

