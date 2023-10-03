import os
import io
import csv
import sys

import sdl2
import sdl2.ext
import time

from math import sqrt
from PIL import Image
from aggdraw import Draw

def pump():
    """Gets events
    
    Returns
    -------
    sdl2.ext.get_events
        A list of sdl2 events
    """

    sdl2.SDL_PumpEvents()
    return sdl2.ext.get_events()

def check_for_quit(queue):
    """Checks for quit events
    
    Parameters
    ----------
    queue: list
        A list of sdl2 events
    """

    quitting = False
    for event in queue:
        # Quit on system quit events
        if event.type == sdl2.SDL_QUIT:
            quitting = True
            break
        # Quit on Esc or Ctrl-Q
        elif event.type == sdl2.SDL_KEYDOWN:
            k = event.key.keysym
            ctrl = k.mod & sdl2.KMOD_CTRL != 0
            if k.sym == sdl2.SDLK_ESCAPE or (ctrl and k.sym == sdl2.SDLK_q):
                quitting = True
                break

    if quitting:
        sdl2.ext.quit()
        sys.exit()

def init_window(fullscreen=True):
    """Sets up SDL2 and returns a window

    Parameters
    ----------
    fullscreen: bool
        Default True, creates a window that is full screen. 
        If set to false, create a window size 960, 540
    
    Returns
    -------
    sdl2.ext.Window
        A sdl2 Window
    """

    # Properly support HIDPI on Windows, disable minimize on focus loss
    sdl2.SDL_SetHint(b"SDL_WINDOWS_DPI_AWARENESS", b"permonitor")
    sdl2.SDL_SetHint(b"SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS", b"0")

    # Initialize video backends
    sdl2.ext.init()

    # Determine the mode and resolution for the experiment window
    display = sdl2.ext.get_displays()[0]
    mode = display.desktop_mode
    if fullscreen:
        win_flags = sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
        res = (mode.w, mode.h)
    else:
        win_flags = sdl2.SDL_WINDOW_SHOWN
        res = (960, 540)

    # Create and show the window, hiding the mouse cursor if fullscreen
    window = sdl2.ext.Window("Circle", size=res, flags = win_flags)
    if fullscreen:
        sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)
    sdl2.SDL_PumpEvents()

    return window

def new_draw_context(width, height):
    """Initialize a blank transparent context on which to draw shapes

    Parameters
    ----------
    width: int
        Width of the new context
    height: int
        Height of the new context
    
    Returns
    -------
    PIL.Image
    aggDraw.canvas
    """
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    canvas = Draw(img)
    canvas.setantialias(True)
    return(img, canvas)

def draw_circle(radius, fill = None, stroke = None): 
    """Create empty aggdraw surface on which to draw circle

    Parameters
    ----------
    radius: int
        The radius of the circle to be drawn
    fill: aggDraw.Brush
        The colour of the circle. Default is none
    stroke: 
        Outline of circle. Default is none
    
    Returns
    -------
    sdl2.ext.pillow_to_surface()
    """

    size = int(radius*2)
    img, canvas = new_draw_context(size + 2, size + 2)

    # Draw circle to surface
    canvas.ellipse([1,1, size + 1, size + 1], stroke, fill)
    canvas.flush() # copies canvas contents to img
    # Convert Image surface to SDL surface
    surf = sdl2.ext.pillow_to_surface(img)
    return surf

def get_radius(size = 10, screensize = 24):
    """Determines the radius of the circle needed to create a 10 mm circle

    mm to inches and inches to pixels

    Parameters
    ----------
    size: int
        The size of radius wanted in mm
    screensize: int
        The size of screen used for display
    
    Returns
    -------
    int
        An integer of the radius in pixels
    """

    display_size = sdl2.ext.get_displays()[0]
    display_x = display_size.desktop_mode.w
    display_y = display_size.desktop_mode.h
    display_d = sqrt((display_x**2)+(display_y**2))
    radius = ((size/10)*(1/2.54)*(display_d/screensize))/2 
    return radius

def get_mm(pixels, screensize = 24):
    """Converts pixels to mm for a 13.5 inch screen

    Parameters
    ----------
    pixels: int
        The pixel int needed to be converted to mm
    screensize: int
        The size of screen used for display
    
    Returns
    -------
    int
        Integer that represents mm
    """

    display_size = sdl2.ext.get_displays()[0]
    display_x = display_size.desktop_mode.w
    display_y = display_size.desktop_mode.h
    display_d = sqrt((display_x**2)+(display_y**2))
    mm = pixels*(screensize/display_d)*2.54*10
    return mm

class DataFile(object):
    """A robust class for creating and writing to data files.

    The output file and its header are written immediately when the DataFile
    is created, and additional rows are added to the file using `write_row`.

    Each row is validated to ensure the columns match the column names defined
    in the header, avoiding issues with missing or misaligned data rows.

    Args:
        outpath (str): The path at which to create the output file.
        header (list): A list defining the names and order of columns for
            the file.
        comments (list, optional): A list of lines to append to the top of
            the file above the header. Each line will be prefixed with '# '
            so they can be easily ignored when reading in the data.
        sep (str, optional): The delimiter character to use to separate columns
            in the output file. Defaults to a single tab.

    """
    def __init__(self, outpath, header, comments=[], sep="\t"):
        self.filepath = outpath
        self.header = header
        self.comments = "\n".join(["# " + line for line in comments])
        self.sep = sep

        self._create()

    def _create(self):
        # Get header and any comments to write to top of file
        content = self.sep.join(self.header)
        if self.comments:
            content = self.comments + "\n\n" + content

        # Create new data file and write header, replacing if it already exists
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
        with io.open(self.filepath, 'w+', encoding='utf-8') as out:
            out.write(sdl2.ext.compat.utf8(content + "\n"))

    def write_row(self, dat):
        """Writes a row of data to the output file.

        Args:
            dat (dict): A dictionary with fields matching each of the column
                names in the header.

        """
        # First, make sure all columns in row exist in the header
        for col in dat.keys():
            if col not in self.header:
                e = "'{0}' exists in row data but not data file header."
                raise RuntimeError(e.format(col))

        # Then, sanitize the data to make sure it's all unicode text
        out = {}
        for col in self.header:
            try:
                out[col] = sdl2.ext.compat.utf8(dat[col])
            except KeyError:
                e = "No value for column '{0}' provided."
                raise RuntimeError(e.format(col))
        
        # Finally, write the colletcted data to the file
        with io.open(self.filepath, 'a', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.header, delimiter=self.sep)
            writer.writerow(out)

#define a function that waits for a response
def waitForResponse(timeout=None,terminate=False):
    """Waits for a response
    
    Parameters
    ----------
    timeout: int
        Default is None. 
        Wait for response will time out according to set value
    
    terminate: Bool
        Default is False
        ???
    
    Returns
    -------
    list
        A list of responses 
    """
    responses = []
    done = False
    while not done:
        if timeout!=None:
            if time.perf_counter()>timeout:
                done = True
        events = pump()
        check_for_quit(events)
        for event in events:
            if event.type == sdl2.SDL_KEYDOWN:
                response = sdl2.SDL_GetKeyName(event.key.keysym.sym)
                response = sdl2.ext.compat.stringify(response).lower()
                responses.append([response,event.key.timestamp/1000.0])
                if terminate:
                    done = True
    return responses



