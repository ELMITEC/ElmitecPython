# -*- coding: utf-8 -*-

from elmitec import Leem2000, UView
from time import perf_counter
import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':

    # UView and Leem2000 classes support the "with ... as ..." 
    # syntax, as shown below
    with UView() as uview:

        # Show UView version
        print(f'UView version: {uview.version()}')

        # Print all available markers
        for i in range(26):
            mi = uview.get_marker_info(i)
            if mi is not None:
                print(f'Marker {i}: {mi}')
        
        # Get current exposure time
        print(f'Exposure time: {uview.exposure_time()} ms')

        # Find out how quickly an image can be obtained
        start = perf_counter()
        for i in range(100):
            array = uview.get_image()
        stop = perf_counter()
        print(f'Frame rate: {round(100 / (stop - start))} fps')

        array = uview.get_image()
        if array is not None:
            # Show shape of the image
            print(f'Image shape: {array.shape}')

            # Show the image - the data is a valid numpy array and can be
            # easily processed with numpy
            plt.imshow(np.log10(np.pow(array, 0.4) + 1), cmap=plt.cm.gray)
            plt.waitforbuttonpress()


    with Leem2000() as leem:
        print(f'Leem2000 version: {leem.version()}')
