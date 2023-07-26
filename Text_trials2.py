# Import required libraries
import os

import sys
import sdl2
import sdl2.ext
import time
import math

from resources import init_window, pump, check_for_quit, waitForResponse
from instructions import instructions

fontpath = os.path.join("_Resources", "DejaVuSans.ttf")
textpath = os.path.join("_Resources", "Hello_world.txt")


# Colours
black = (0,0,0)
white = (255, 255, 255)
lightGrey = (200, 200, 200, 255)

# Initialize and create the experiment window
viewingDistance = 100
stimDisplayWidth = 100
Window = init_window(fullscreen = True)
stimDisplayRes = Window.size
stimDisplayWidthInDegrees = math.degrees(
    math.atan((stimDisplayWidth / 2.0) / viewingDistance) * 2
)
PPD = stimDisplayRes[0] / stimDisplayWidthInDegrees  # Pixels per degree

# Create a renderer
renderflags = sdl2.SDL_RENDERER_SOFTWARE 
if "-hardware" in sys.argv:
    renderflags = (
        sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )
renderer = sdl2.ext.Renderer(Window, flags = renderflags)


# Initialize font rendering
fontsize = '{0}px'.format(int(PPD * 0.6))
font = sdl2.ext.FontTTF(fontpath, fontsize, white)
font.add_style("grey", fontsize, color=lightGrey)


# Location on screen
screen_w, screen_h = renderer.logical_size
loc_mid = (int(screen_w/2), int(screen_h/2))


def update_text(renderer, surface): 
    tx = sdl2.ext.Texture(renderer, surface)
    renderer.clear(black)
    renderer.rcopy(tx, loc = loc_mid, align = (0.5, 0.5))
    renderer.present()

def draw_text(myText):
    if isinstance(myText, list):
        myText = "\n".join(myText)

    txt_rendered = font.render_text(myText, width = 780, align = 'center')
    update_text(renderer, txt_rendered)

def show_message(myText, lockWait = False):
    messageViewingTimeStart = time.perf_counter()
    renderer.clear(black)
    renderer.present()
    renderer.clear(black)
    draw_text(myText)
    time.sleep(0.5)
    renderer.present()
    renderer.clear(black)
    if lockWait:
        response = None
        while response != 'return':
            response = waitForResponse(terminate = True)[0][0]
    else:
        response = waitForResponse(terminate = True)[0][0]
    renderer.present()
    renderer.clear()
    time.sleep(0.50)
    messageViewingTime = time.perf_counter() - messageViewingTimeStart
    return [response, messageViewingTime]


def get_input(getWhat):
    """
    Displays a prompt and collects text input.
    
    Returns the results on enter.
    """
    renderer.clear(black)
    renderer.present()
    time.sleep(0.50)

    getWhat = sdl2.ext.compat.utf8(getWhat)
    textInput = u''
    myText = getWhat + '\n' + textInput
    draw_text(myText)
    renderer.present()

    # Enter input into a collection loop
    renderer.clear(black)
    sdl2.SDL_StartTextInput()
    done = False
    while not done: 
        events = pump()
        check_for_quit(events)
        refresh = False
        for event in events: 
            # Check for new text input
            if event.type == sdl2.SDL_TEXTINPUT:
                textInput += event.text.text.decode('utf-8')
                refresh = True
            
            # Check for backspace or enter keys
            elif event.type == sdl2.SDL_KEYDOWN:
                k = event.key.keysym
                if len(textInput):
                    if k.sym == sdl2.SDLK_BACKSPACE:
                        textInput = textInput[:-1]
                        refresh = True
                    elif k.sym in (sdl2.SDLK_KP_ENTER, sdl2.SDLK_RETURN):
                        done = True

        # If necessary, update the contents of the screen
        if refresh: 
            myText = getWhat + '\n' + textInput
            renderer.clear(black)
            draw_text(myText)
            renderer.present()

    # Clear screen to black and return collected input
    renderer.clear(black)
    renderer.present()
    sdl2.SDL_StopTextInput()
    textInput = textInput.strip() # remove any trailing whitespace
    return textInput


def get_participant_info():
    """
    Collects demographics info from the participants
    """
    created = time.strftime("%Y-%m-%d %H:%M:%S")
    participant_id = get_input('ID (\'test\' to demo): ')

    # Create dictionary with participant info
    info = {'id': participant_id, 'created': created}

    if participant_id != 'test':
        info['sex'] = get_input('Sex (m or f): ')
        info['age'] = get_input('Age (2-digit): ')
        info['handedness'] = get_input('Handedness (r or l): ')

    else:
        info['sex'] = 'test'
        info['age'] = 'test'
        info['handedness'] = 'r'
    
    return info


def run():
    done = False
    while not done: 
        events = pump()
        check_for_quit(events)
        
        # text = open(textpath)
        # text = text.readlines()
        # draw_text(myText = text)
        # get_input("Input your handedness:")
        # participant_info = get_participant_info()
        # print(participant_info)
        show_message(instructions['Familiarization'], lockWait = True)


if __name__ == "__main__":
    sys.exit(run())

