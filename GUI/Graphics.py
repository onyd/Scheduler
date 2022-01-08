from itertools import chain
from typing import Text
import numpy as np
from array import array

from kivy.graphics.texture import Texture


class Gradient:
    @staticmethod
    def horizontal(*args):
        texture = Texture.create(size=(len(args), 1), colorfmt='rgba')
        buf = bytes([int(v)
                     for v in chain(*args)])  # flattens

        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(*args):
        texture = Texture.create(size=(1, len(args)), colorfmt='rgba')
        buf = bytes([int(v)
                     for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def interp_grad(*args, acc=10, interp=None):
        if interp is None:
            interp = Gradient.linear_interpolation

        texture = Texture.create(size=((len(args) - 1) * acc, 1),
                                 colorfmt='rgba')
        X = np.linspace(0, 1, acc)
        buf = []
        for i in range(len(args) - 1):
            # interpolate at each x
            for x in X:
                # iterate over color components
                for j in range(len(args[i])):
                    # add the interpolate color components in the buffer
                    buf.append(int(
                        interp(args[i][j], args[i + 1][j], x) * 255))
        texture.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def linear_interpolation(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def poly_interpolation(a, b, t):
        c = 6 * t**5 - 15 * t**4 + 10 * t**3  # (1-np.cos(np.pi*t))/2
        return (1 - c) * a + c * b
