# -*- coding: utf-8 -*-

import sys
from elmitec import Leem2000, UView

if __name__ == '__main__':
    with UView() as uview:
        print(f'UView version: {uview.version()}')

    with Leem2000() as leem:
        print(f'Leem2000 version: {leem.version()}')
