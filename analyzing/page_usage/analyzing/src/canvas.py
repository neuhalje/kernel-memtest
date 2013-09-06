'''
This source code is distributed under the MIT License

Copyright (c) 2010, Jens Neuhalfen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
try:
    import Image
    import ImageDraw
except ImportError:
    print "Please try to 'easy_install PIL'"
    raise ImportError


from kpageflags import *

class MemoryCanvas:
    """
    A canvas that allows each `page`of memory to be represented as
    colored block.
    The finished image can be saved as PNG 
    """
    def __init__(self, width, height, point_size = 1, point_spacing = 0, background="#000000"):
        """
        width and heigth are the logical width and height, e.g. draw
        a picture that contains `width` frames per row.
        """
        self.width = width
        self.height = height

        self.point_size = point_size # Size of a `page`
        self.point_spacing = point_spacing# Spacing between `pages`

        self.img = Image.new('RGB',self.get_physical_size())
        self.drawer = ImageDraw.Draw(self.img)
        self.background = background

    def get_physical_size(self):
        d = self.point_spacing + self.point_size
        return (self.width * d, self.height * d)

    def clear(self):
        self.drawer.rectangle((0,0,self.width-1,self.height-1), fill=self.background)

    def draw(self, x,y,  filling):

        x *= (self.point_size + self.point_spacing)
        y *= (self.point_size + self.point_spacing)

        self.drawer.rectangle((x, y, x + self.point_size - 1 , y + self.point_size - 1 ), fill=filling)

    def save(self, filename):
        print("%s: %sx%s ; point size: %s ; point spacing: %s" % (filename,self.width,self.height, self.point_size, self.point_spacing))
        self.img.save(filename, "PNG",bits=8)


class StaticColorMap:
    def __init__(self, key_to_color , default_color):
        self.default_color  = default_color
        self.color_map = key_to_color

    def color(self,flags):
        if flags in self.color_map:
            c = self.color_map[flags]
        else:
            c = self.default_color
        return c

class HistoColorMap:
    """
    A color map that matches a priority list of colors to the
    page-flags. The flags are sorted by count of occurence
    and the most frequent flag-combination gets the first
    color assigned, the second most frequent combination the second
    color in the list and so on.

    If no colors are left in the list of colors, `default_color`
    is returned.
    """
    def __init__(self, histogram, colors, default_color):
        """ histo is a dictionary type -> number_of_occurences_of_this_type """
        self.histogram = histogram
        self.colors = colors
        self.default_color  = default_color
        self._build_color_map()

    def color(self,flags):
        if self.color_map.has_key(flags):
            c = self.color_map[flags]
        else:
            c = self.default_color

        return c

    def _build_color_map(self):
        flags = [ (k, v) for k, v in self.histogram.iteritems() ]
        flags = sorted(flags, key=lambda x: x[1], reverse=True)

        self.color_map = {}

        idx = 0
        for top in flags[:len(self.colors)]:
            self.color_map[top[0]] =  self.colors[idx]
            idx += 1

class FlagColorMap:
    """
    A color map that matches a priority list of flags to the
    list of colors. 
    """
    def __init__(self, colors, default_color, decorated = None):
        """ mapping is a list (flags, color) """
        self.colors = colors
        self.default_color  = default_color
        self.decorated = decorated

    def color(self,flags):
        if self.decorated:
            base_color = self.decorated.color(flags)
        else:
            base_color = (0,0,0)

        for f,c in self.colors:
           if flags.all_set_in(f):
               return self.color_add(c, base_color)

        return self.color_add(self.default_color, base_color)

    def color_add(self, a,b):
        """
        Mix two colors `a` `b` by adding their RGB values.
        """
        r1,g1,b1 = a
        r2,g2,b2 = b
        return (r1 + r2, g1 + g2, b1 + b2)
        
