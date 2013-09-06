#!/usr/bin/env python

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

from baseanalyzer import BaseAnalyzer
from kpageflags import *
from kpagecount import CountDataSource
from PIL import ImageFont
from canvas import MemoryCanvas, HistoColorMap, FlagColorMap, StaticColorMap
from file_utils import FileSetIterator
import os
import glob



import math
from optparse import OptionParser


#SOLARIZED HEX     16/8 TERMCOL  XTERM/HEX   L*A*B      RGB         HSB
#--------- ------- ---- -------  ----------- ---------- ----------- -----------
#
base03=    '#002b36'
base02=    '#073642'
base01=    '#586e75'
base00=    '#657b83'
base0=     '#839496'
base1=     '#93a1a1'
base2=     '#eee8d5'
base3=     '#fdf6e3'
yellow=    '#b58900'
orange=    '#cb4b16'
red=       '#dc322f'
magenta=   '#d33682'
violet=    '#6c71c4'
blue=      '#268bd2'
cyan=      '#2aa198'
green=     '#859900'

default_cell_fill = base0
background=base03

class BasePainter(BaseAnalyzer):
    """
    Paints the mapcount and the pageflags of a pfn onto
    the canvas.
    """

    def __init__(self, canvas, colors,legend_font):
        self.canvas = canvas
        self.colors = colors
        self.legend_font = legend_font

    def process_record(self, pfn, page_count, page_flags):
        if self.pf_statistics.has_key(page_flags):
            self.pf_statistics[page_flags] = self.pf_statistics[page_flags] + 1
        else:
            self.pf_statistics[page_flags] = 1

        if self.pc_statistics.has_key(page_count):
            self.pc_statistics[page_count] = self.pc_statistics[page_count] + 1
        else:
            self.pc_statistics[page_count] = 1

        if self.max_num_drawings > 0:
            self.max_num_drawings -= 1

            x, y = self.coords(pfn)

            self.canvas.draw(x,y,  self.color(pfn, page_count, page_flags))


    def coords(self, pfn):
        x = pfn % self.canvas.width
        y = pfn / self.canvas.height
        return (x,y)

    def stop_processing(self):
        self.draw_legend()

    def start_processing(self):
        self.canvas.clear()
        # Limit ourself to 4 GiB of memory
        self.max_num_drawings = 1024 * 1024

        # Stats per image
        self.pf_statistics = {}
        self.pc_statistics = {}

    def draw_legend(self):
        pass


class FlagsPainter(BasePainter):
    def color(self, pfn, page_count, page_flags):
        return self.colors.color(page_flags)

    def print_status(self):
        flags = [ (k, v) for k, v in self.pf_statistics.iteritems() ]
        flags = sorted(flags, key=lambda x: x[1], reverse=True)
        flags = flags[:10]

        def fmt_flags(flags):
            if flags.flags:
                return " | ".join(flags.set_flags())
            else:
                return "(no flags set)"

        lines = [ "%60s  %7d pages (~%4d MiB)" % (fmt_flags(top[0]),  top[1], top[1] * 4096 / (1024*1024)) for top in flags[:10] ]

        max_text_height = 0
        max_text_width = 0
        for line in lines:
            print(line)
            width, height = legend_font.getsize(line)
            if height > max_text_height: max_text_height = height
            if width > max_text_width: max_text_width = width

        table_height = max_text_height * len(lines)
        y_text = self.canvas.height - table_height - 10

        dot_width, dot_height = legend_font.getsize('X')

        x_text = 10
        x_dot =  x_text + max_text_width + 10 +  dot_width 

        lineno = 0
        for line in lines:
            self.canvas.drawer.text((x_text, y_text), line, font = legend_font)
            self.canvas.drawer.rectangle((x_dot, y_text, x_dot + dot_width, y_text + dot_height), fill=self.colors.color(flags[lineno][0]))
            y_text += max_text_height
            lineno += 1

    def draw_legend(self):
        self.print_status()


class CountPainter(BasePainter):
    def color(self, pfn, page_count, page_flags):
        return self.colors.color(page_count)


def build_flag_analyzer_static_colors(canvas,  legend_font):
    """
    Magic happens here: Depending on the
    """

    # Filer out all other flags



#                           (no flags set/page non existent)   137223 pages (~ 536 MiB)
#                                 REFERENCED | UPTODATE | LRU   129320 pages (~ 505 MiB)
#                                     UPTODATE | LRU | ACTIVE   103831 pages (~ 405 MiB)
#                   ANON | UPTODATE | LRU | SWAPBACKED | MMAP    18239 pages (~  71 MiB)
#                                               COMPOUND_TAIL    17749 pages (~  69 MiB)
#          ANON | UPTODATE | LRU | SWAPBACKED | ACTIVE | MMAP    17707 pages (~  69 MiB)
#                                                        SLAB    15209 pages (~  59 MiB)
#                        REFERENCED | UPTODATE | LRU | ACTIVE    14748 pages (~  57 MiB)
#                                              UPTODATE | LRU    10539 pages (~  41 MiB)
#                                                  UNKNOWN_32     9908 pages (~  38 MiB)




    # Static map established by running `flag_stats.py`
    flags_to_color = {
        KPageFlags(0) : base03,
        KPageFlags(REFERENCED| UPTODATE| LRU)  : base3,
        KPageFlags(UPTODATE| LRU| ACTIVE)  : red,
        KPageFlags(ANON| UPTODATE| LRU| SWAPBACKED| MMAP)  : magenta,
        KPageFlags(ANON| UPTODATE| LRU| SWAPBACKED| ACTIVE| MMAP)  : cyan,
        KPageFlags(COMPOUND_TAIL)  : orange,
        KPageFlags(REFERENCED| UPTODATE| LRU| ACTIVE)  : red,
        KPageFlags(SLAB)  : yellow,
        KPageFlags(UNKNOWN_32) :green
        }

    flags_to_color = {
        KPageFlags(0) : base03,
        KPageFlags(MMAP)  : yellow,
        KPageFlags(MMAP|ANON)  : orange,
        KPageFlags(ANON)  : red
        }

    flag_colors = StaticColorMap(  flags_to_color , default_cell_fill)
    flag_analyzer = FlagsPainter(canvas, flag_colors,legend_font)

    return flag_analyzer

def build_flag_analyzer_histo(canvas,  legend_font):

    # These colors are assigned on priority base
    # The most common flag-combination gets the color[0], the next color[1]...
    flag_cell_fill = [(255,0,0),(0,255,0),(0,0,255),(0,0,255),(0,128,64),(0,255,255),(255,0,255),(128,128,128),(128,64,128),(128,0,128)]
    # flag_cell_fill + [(255, 255 * g / 5 ,0) for g in xrange(1,3)]
    default_cell_fill = "(20,20,20)"


#                           (no flags set/page non existent)   137223 pages (~ 536 MiB)
#                                 REFERENCED | UPTODATE | LRU   129320 pages (~ 505 MiB)
#                                     UPTODATE | LRU | ACTIVE   103831 pages (~ 405 MiB)
#                   ANON | UPTODATE | LRU | SWAPBACKED | MMAP    18239 pages (~  71 MiB)
#                                               COMPOUND_TAIL    17749 pages (~  69 MiB)
#          ANON | UPTODATE | LRU | SWAPBACKED | ACTIVE | MMAP    17707 pages (~  69 MiB)
#                                                        SLAB    15209 pages (~  59 MiB)
#                        REFERENCED | UPTODATE | LRU | ACTIVE    14748 pages (~  57 MiB)
#                                              UPTODATE | LRU    10539 pages (~  41 MiB)
#                                                  UNKNOWN_32     9908 pages (~  38 MiB)


    # Static map established by running `flag_stats.py`
    pf_statistics = {
        KPageFlags(0) : 10,
        KPageFlags(REFERENCED| UPTODATE| LRU)  : 9,
        KPageFlags(UPTODATE| LRU| ACTIVE)  : 8,
        KPageFlags(ANON| UPTODATE| LRU| SWAPBACKED| MMAP)  : 6,
        KPageFlags(ANON| UPTODATE| LRU| SWAPBACKED| ACTIVE| MMAP)  : 5,
        KPageFlags(COMPOUND_TAIL)  : 4,
        KPageFlags(REFERENCED| UPTODATE| LRU| ACTIVE)  : 3,
        KPageFlags(SLAB)  : 2,
        KPageFlags(UNKNOWN_32) : 1
        }

    flag_colors = HistoColorMap( pf_statistics, flag_cell_fill, default_cell_fill)
    flag_analyzer = FlagsPainter(canvas, flag_colors,legend_font)

    return flag_analyzer

def build_flag_analyzer(canvas, legend_font):
    """
    Chain multiple FlagColorMap-instances together to provide a
    differentiated color scheme for specific flag combinations.

    The list of color mappers is chained together from the tail (`base`) to the
    head. The `FlagColorMap` instances add their color to the resulting color
    when their filter condition matches the flags analyzed.

    E.g.
    A flag combination ACTIVE | ANON would result in an RGB value of
    (0,128,64).
    """

    black = "(0,0,0)"

    pf_statistics = {
        KPageFlags(0) : 10
    }

    base = HistoColorMap( pf_statistics, [(20,20,20) ], black)

    anon_tint = [ (ANON, (0,128,0)) ]
    anon_colors = FlagColorMap( anon_tint, default_cell_fill, base)

    active_tint = [ (ACTIVE, (0,0,64)), (REFERENCED, (0,0,128)) ]
    active_colors = FlagColorMap( active_tint, default_cell_fill, anon_colors)


    buddy_tint = [ (BUDDY, (32,0,0)), (SLAB, (128,0,0))  ]
    buddy_colors = FlagColorMap( buddy_tint, default_cell_fill, active_colors)


    flag_colors = buddy_colors
    flag_analyzer = FlagsPainter(canvas, flag_colors, legend_font)

    return flag_analyzer

class CountColors:
    """
    A coloring scheme for `mapcount` that leverages that facts that color perception
    is not linear, and that green is the color that can be distinguished best.

    `max_count` describes the "maximum count that gets differentiated", values
    `v > max_count` get the same color values as `max_count`.

    The color map is build logarithmically.
    """
    def __init__(self, max_count):
        self.max_count  =  max_count
        self.scale = 255 / math.log(1+ max_count)

    def color(self, count):
        if (count > self.max_count):
            count = self.max_count

        val = math.log(1 + count)

        scaled = int(self.scale * val)

        return (0,scaled,0)

def build_count_analyzer(canvas):
    return CountPainter(canvas, CountColors(3))

if __name__ == "__main__":
        #
    usage = """This tool builds images visualizing `kpageflags`/`pagecount`.
    usage: %prog [options] sourcedir"""
    parser = OptionParser(usage=usage)


    parser.add_option("-v", action="store_true", dest="verbose",
                  help="Print filenames as they are processed.", default=False)


    parser.add_option("-x", "--x-res",
                      default=1280,type=int,dest="x",
                      metavar="RESOLUTION-X", help="Horizontal resolution  of the images. [default: %default]")

    parser.add_option("-y", "--y-res",dest="y",
                      default=820,type=int,
                      metavar="RESOLUTION-Y", help="Vertical resolution  of the images. [default: %default]")

    parser.add_option("-s", "--spacing",
                      default=0,type=int,
                      metavar="SPACING", help="Spacing between frames (in pixels). [default: %default]")

    parser.add_option("-f", "--flags",action="store_true", dest="flags",
                      default=False,
                      metavar="FLAGS", help="Create images visualizing page flags (filter for files:'^.*kpageflags@(\d+)\.bin$' ). You still need the flags AND the cout files. [default: %default]")

    parser.add_option("-c", "--count",action="store_true", dest="count",
                      default=False,
                      metavar="COUNT", help="Create images visualizing page count (filter for files:'^.*kpagecount@(\d+)\.bin$' ). You still need the flags AND the cout files. [default: %default]")


    parser.add_option("-p", "--pattern",
                      default='*kpage*.bin',
                      metavar="PATTERN", help="use this PATTERN (glob) to filter the page-flags AND kpagecount files. [default: %default]")

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")

    if not (options.flags or options.count):
        parser.error("please choose -f and/or -c.")

    legend_font_path = "/opt/local/share/fonts/dejavu-fonts/DejaVuSansMono.ttf"
    legend_font = ImageFont.truetype(legend_font_path, 14, encoding='unic')

    set_interesting_pageflag_filter(  MMAP |   ANON )

    all_analyzers =  []
    all_canvases  =  []

    if options.flags:
        flags_canvas =  MemoryCanvas(options.x, options.y,1, options.spacing, background=background)
        flag_analyzer = build_flag_analyzer_static_colors(flags_canvas, legend_font)
        all_analyzers.append(flag_analyzer)
        all_canvases.append(flags_canvas)

    if options.count:
        count_canvas =  MemoryCanvas(options.x, options.y,1, options.spacing)
        count_analyser = build_count_analyzer(count_canvas, legend_font)
        all_analyzers.append(count_analyser)
        all_canvases.append(count_canvas)


    path = args[0]

    file_names = glob.glob( os.path.join(path, options.pattern) )

    files = FileSetIterator(file_names)

    for (flags_file, count_file)  in  files:
        if options.verbose:
            print "processing \n\t%s\t%s" % (flags_file, count_file)

        pageflags = FlagsDataSource('flags',flags_file)
        pagecount = CountDataSource('count',count_file)

        for analyzer in all_analyzers:
            analyzer.analyze(pageflags, pagecount)

        if options.flags:
            flags_canvas.save(flags_file.replace('.bin','.png'))
        if options.count:
            count_canvas.save(count_file.replace('.bin','.png'))

    def video_help(type,canvas):
        print("Convert to a video by calling")
        print('cd %s ' % (path, ))
        file = "file_%s_list.txt" % (type,)
        size = canvas.get_physical_size()

        print('find . -name \*%s\*.png|sort > %s' % (type, file))
        print('mencoder mf://@%s  -nosound -mf w=%d:h=%d:fps=5:type=png  -ovc x264 -x264encopts bitrate=8000 -xvidencopts pass=1 -vf scale=%d:%d -o %s.avi' % (file, size[0], size[1], options.x, options.y, type))

    if options.flags:
        video_help("flags", flags_canvas)
    if options.count:
        video_help("count", count_canvas)
