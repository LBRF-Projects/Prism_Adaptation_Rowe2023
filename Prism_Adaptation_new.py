# Import required libraries
import os
import sys
import sdl2
import sdl2.ext
from sdl2.ext import get_events, key_pressed, get_clicks
from communication import get_trigger_port

from math import nan, degrees, atan
import random
import time
import shutil
from instructions import instructions
from aggdraw import Brush
from resources import init_window, draw_circle, get_radius, get_mm, DataFile, pump, check_for_quit, waitForResponse

# Initialize paths
data_dir = "_Data"
if not os.path.exists(data_dir):
    os.mkdir(data_dir)

fontpath = os.path.join("_Resources", "DejaVuSans.ttf")

# Column names and order for DataFile
data_cols = [
    "id", "created", "sex", "age", "handedness",
    "block", "group", "trial_num", "response_time", "reaction_time",
    "points_x", "points_y", "location_x", "location_y",
    "distance_x", "distance_y", "run_time"
    ] 

# Trigger port for PLATO goggles
port = get_trigger_port()

# Indicates trial start for EMG collection
port.add_codes({
    'trial_start': 2,
    'circle_on': 4,
    'trial_end': 8
})

# Initialize and create the experiment window
viewingDistance = 100
stimDisplayWidth = 100
Window = init_window(fullscreen = True)
stimDisplayRes = Window.size
stimDisplayWidthInDegrees = degrees(
    atan((stimDisplayWidth / 2.0) / viewingDistance) * 2
)
PPD = stimDisplayRes[0] / stimDisplayWidthInDegrees  # Pixels per degree

# Create a renderer
renderflags = sdl2.SDL_RENDERER_SOFTWARE 
if "-hardware" in sys.argv:
    renderflags = (
        sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )
renderer = sdl2.ext.Renderer(Window, flags = renderflags)

# Define colours for the experiment
# Colours
black = (0,0,0)
white = (255, 255, 255)
lightGrey = (200, 200, 200, 255)

# Initialize font rendering
fontsize = '{0}px'.format(int(PPD * 0.6))
font = sdl2.ext.FontTTF(fontpath, fontsize, white)
font.add_style("grey", fontsize, color = lightGrey)

# Import an image file and convert it to a texture.
# A texture is an SDL surface that has been prepared for use with a given renderer
fill = Brush((255, 0, 0, 255))
r = get_radius(10) #specify 10 mm circle. This is default
tst_img = draw_circle(r, fill)
tx = sdl2.ext.Texture(renderer, tst_img)

# location of the stimuli to be presented on the window
screen_w, screen_h = renderer.logical_size
# list of three locations for the circles: 
loc_left = (int(screen_w*0.4), int(screen_h/2))
loc_mid = (int(screen_w/2), int(screen_h/2))
loc_right = (int(screen_w*0.6), int(screen_h/2))
loc_opt = [loc_left, loc_mid, loc_right]

def update_text(renderer, surface):
    """Updates text to a renderer

    Parameters
    ----------
    renderer: sdl2.ext.Renderer
        The renderer to be used 
    
    surface: sdl2.SDL_surface
        The contents to be updated to the renderer
    """ 

    tx = sdl2.ext.Texture(renderer, surface)
    renderer.clear(black)
    renderer.rcopy(tx, loc = loc_mid, align = (0.5, 0.5))
    renderer.present()

def draw_text(myText):
    """Draws text to rendered surface

    Parameters
    ----------
    myText: str
        The text to be renderer to the surface
    """

    if isinstance(myText, list):
        myText = "\n".join(myText)

    txt_rendered = font.render_text(myText, width = 780, align = 'center')
    update_text(renderer, txt_rendered)

def show_message(myText, lockWait = False):
    """Prints a message on the window while looking for user input to continue.

    The function returns the total time it waited.
    If the argument 'lockWait' isn't passed, the default allows users
    to press any key to exit the message shown.

    Parameters
    ----------
    myText: str
        The message that will be presented on the window
    lockWait: bool, optional
        If True, users must press enter to exit message on window (default False)
    
    Returns
    -------
    str
        a string of the user key response
    float
        a float representing the time it took user to respond
    """

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
    """Displays a prompt and collects text input on return

    Parameters
    ----------
    getWhat: str
        The input of the user
    
    Returns
    -------
    str
        A string of the user's input 
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
    """Collects demographics info from the participants

    Returns
    -------
    dict
        A dictionary of participant info
    """

    created = time.strftime("%Y-%m-%d %H:%M:%S")

    while True:
        participant_id = get_input('ID (\'test\' to demo): ')
        participant_id = participant_id.upper() #ensures that all files with have capitalized values
        folder = '_Data'
        sub_folders = [name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder,name))] # Grabs all the folder names in the folder _Data
        # Raises message if subject folder already exists
        if (participant_id in sub_folders) and participant_id.lower() != 'test':
            show_message('This file already exists\nPlease input new participant code\nPress Enter to continue', lockWait = True)
            continue
        else: 
            info = {'id': participant_id, 'created': created}
            break

    # Create dictionary with participant info

    if participant_id.lower() != 'test':
        while True:
            sex = get_input('Sex (m or f): ') 
            sex = sex.lower() #ensures input will be lowercase 
            if sex in ['m', 'f']:
                info['sex'] = sex
                break
            else:
                show_message('Error\nPlease input m or f\nPress Enter to continue', lockWait = True)
                continue
        
        while True:
            age = int(get_input('Age (2-digit): '))
            if 18 <= age <= 99:
                info['age'] = age
                break
            else:
                show_message('Error!\nPlease input a number between 18 and 99\nPress Enter to continue', lockWait = True)
                continue
        
        while True:
            handedness = get_input('Handedness (r or l): ')
            handedness = handedness.lower() #ensures input is lowercase
            if handedness in ["r", "l"]:
                info['handedness'] = handedness
                break
            else: 
                show_message('Error!\nPlease input r or l\nPress Enter to continue', lockWait = True)
                continue
        
        while True:
            group = get_input('Group (PP50, PP-MI, PP-CTRL, PP-None): ') 
            if group in ["PP50", "PP-MI", "PP-CTRL", "PP-None"]:
                info['group'] = group
                break
            else:
                show_message('Error!\nPlease input PP50, PP-MI, PP-CTRL, PP-None\nPress Enter to continue', lockWait = True)
                continue

    else:
        info['sex'] = 'test'
        info['age'] = 'test'
        info['handedness'] = 'r'
        info['group'] = 'test'
    
    return info

def open_goggles():
    port._write_trigger(0, port = 'FIO')

def close_goggles():
    port._write_trigger(3, port = 'FIO')

def run_trial(block, group, participant_info):
    """Parameters for different trial types of a reach and point task

    During motor imagery and control exposure trials, the stimulus disappears when the spacebar is lifted.
    During all other trials, stimulus disappears when stimulus is touched.

    Parameters
    ----------
    block: str
        The block type for the trials. These include Familiarization, Baseline,
        Exposure, and PostTest. 
    group: str
        The group type of the participant being run. These include:
        PP: Physical practice
        MI-CE: Motor imagery concurrent exposure
        MI-TE: Motor imagery terminal exposure
        CTRL: Control
    participant_info: dict
        A dictionary containing participant info
    
    Returns
    -------
    dict
        A dictionary containing data output
    """

    #display black screen
    renderer.clear(black)
    renderer.present()
    port.send('trial_start')

    # PLATO goggles open
    port._write_trigger(0)

    # Initialize trial data
    data = participant_info.copy()
    data["reaction_time"] = nan        
    
    while True: 
        events = pump()
        check_for_quit(events)
        wait_time = (random.randint(400, 600))/1000  
        if key_pressed(events, key = 'space'):
            time.sleep(wait_time) # Wait between 400-600 ms before presenting stimuli 
            events = get_events()
            # If the spacebar is release prior to stimulus shown,
            # Error message "too fast" is displayed
            if key_pressed(events, key = 'space', released = True ):
                show_message("Too fast!\nPress Enter to try again", lockWait = True)
                get_events()
                continue
            break

    # Shows circle stimuli on the renderer
    renderer.clear(black)
    location = random.choice(loc_opt)
    renderer.rcopy(tx, loc= location, align = (0.5, 0.5)) #show stimuli at one of 3 random locations
    renderer.present()
    port.send('circle_on')
    start_time = time.perf_counter() # Grabs start time to measure reaction time
    events = pump()        

    # x and y location of the simuli 
    location_x = get_mm(location[0]) 
    location_y = get_mm(location[1])

    # Gathers response time for motor imagery and control groups
    response_time = None
    if ((block == "Exposure") and group in ["PP-MI", "PP-CTRL"]):
        while not response_time:
            events = pump()
            check_for_quit(events)
            if key_pressed(events, key = "space", released = True):
                response_time = (time.perf_counter() - start_time)*1000
                points_x = nan
                points_y = nan
                data.update({
                    'response_time': response_time,
                    'reaction_time': nan,
                    'points_x': points_x,
                    'points_y': points_y,
                    'location_x': location_x,
                    'location_y': location_y,
                    'distance_x': nan,
                    'distance_y': nan
                })

        # Clear screen when spacebar is unclicked
        get_events()
        renderer.clear(black)
        renderer.present()
    
    if block in ["Baseline", "PostTest"]:
        # Grabs distance x, distance y, response time, and reaction time during a physical practice trial
        while not response_time:
            events = pump()
            check_for_quit(events)

            # Grabs reaction time. 
            # Time from when stimulus is presented to time when finger released from button
            reaction_time = None

            if key_pressed(events, key = 'space', released = True): 
                reaction_time = (time.perf_counter() - start_time)*1000 
                close_goggles() 
                data.update({
                    'reaction_time': reaction_time
                })
            
            # Grabs clicks events 
            points = get_clicks(events)
            
            # Grabs response time, distance x, and distance y.
            # Time from when stimulus is presented to time when stimulus is touched
            if len(points) > 0:
                response_time = (time.perf_counter() - start_time)*1000

                points_x = get_mm(points[0][0])
                points_y = get_mm(points[0][1])
                distance_x = points_x - location_x
                distance_y = points_y - location_y
                data.update({
                    'response_time': response_time,
                    'points_x': points_x,
                    'points_y': points_y,
                    'location_x': location_x,
                    'location_y': location_y,
                    'distance_x': distance_x,
                    'distance_y': distance_y
                }) 

    else:
        # Grabs distance x, distance y, response time, and reaction time during a physical practice trial
        while not response_time:
            events = pump()
            check_for_quit(events)

            # Grabs reaction time. 
            # Time from when stimulus is presented to time when finger released from button
            reaction_time = None
            if key_pressed(events, key = 'space', released = True): 
                reaction_time = (time.perf_counter() - start_time)*1000 
                data.update({
                    'reaction_time': reaction_time
                })
            
            # Grabs clicks events 
            points = get_clicks(events)
            
            # Grabs response time, distance x, and distance y.
            # Time from when stimulus is presented to time when stimulus is touched
            if len(points) > 0:
                response_time = (time.perf_counter() - start_time)*1000
                points_x = get_mm(points[0][0])
                points_y = get_mm(points[0][1])
                distance_x = points_x - location_x
                distance_y = points_y - location_y
                data.update({
                    'response_time': response_time,
                    'points_x': points_x,
                    'points_y': points_y,
                    'location_x': location_x,
                    'location_y': location_y,
                    'distance_x': distance_x,
                    'distance_y': distance_y
                })         
            
    get_events()
    renderer.clear(black) 
    renderer.present()
    port.send('trial_end')
    time.sleep(0.25) # Wait 250 ms before opening goggles
    open_goggles()
    return data


def run_block(block, group, participant_info, df):
    """Defines the different blocks types

    Familiarization: 40 trials
    Baseline: 10 trials
    PPExposure: 20 trials
    Exposure: 230 trials
    PP50Exposure: 250 trials
    PostTest: 10 trials

    Parameters
    ----------
    block: str
        The block type for the trials. These include Familiarization, Baseline,
        Exposure, and PostTest. 
    group: str
        The group type of the participant being run. These include:
        PP50: Physical practice with 50 post-test trials
        PP-MI: Phyiscal Practice then Motor Imagery
        PP-CTRL: Physical Practice then control
        PP-None: Only 20 PP exposure trials
    participant_info: dict
        A dictionary containing participant info
    df: Datafile obj
        Datafile containing experiment data
    """
    
    if block == "Familiarization":
        trial_num = 40
    elif block == "Baseline":
        trial_num = 10
    elif block == "PP50Exposure":
        trial_num = 25 #repeat 10 time (total 250 trials) 
    elif block == "PPExposure":
        trial_num = 20
    elif block == "Exposure":
        trial_num = 23 #repeat 10 times (total 230 trials)
    elif block == "PostTest":
        trial_num = 50
    trials = 0
    start_time = time.time()
    for i in range(trial_num):
            trials += 1
            data = run_trial(block, group, participant_info)
            data["trial_num"] = trials
            end_time = time.time()
            run_time = end_time - start_time
            data["run_time"] = run_time
            data["block"] = block
            data["group"] = group
            df.write_row(data)

def init_data(participant_id):
    """Creates a participant data folder with experiment data and experiment code
    
    Parameters
    ----------
    participant_id: dict
        A dictionary of participant data
    
    Returns
    -------
    dict
        A dictionary containing data output files for the participant
    """

    # Create the data folder for the participant
    filebase = participant_id
    participant_dir = os.path.join(data_dir, filebase)
    if not os.path.exists(participant_dir):
        os.mkdir(participant_dir)

    # Make a copy of the code the experiment was run with
    code_path = os.path.join(participant_dir, filebase + "_code.py")
    shutil.copy(sys.argv[0], code_path)

    # Get the data outputs for the participant
    data_path = os.path.join(participant_dir, filebase + "reach_and_point.csv")

    # Create data output files for the participant
    df = {'Data': DataFile(data_path, data_cols, sep = ',')}

    return df

### Actually run the experiment ###
def run():
    """Runs the experiment from start to end
    """

    participant_info = get_participant_info()
    participant_id = participant_info['id']
    group = participant_info['group']

    # Create data folder/files for the participant
    df = init_data(participant_id)

    # Familiarization block
    show_message(instructions["Familiarization"], lockWait = True)
    run_block(block = 'Familiarization', group = group, participant_info = participant_info, df = df['Data'])

    # Break, study investigator swaps glasses/goggles/prisms
    show_message(instructions["get_study_investigator"], lockWait = True)

    # Baseline block
    show_message(instructions["Baseline"], lockWait = True)
    run_block(block = 'Baseline', group = group, participant_info = participant_info, df = df['Data'])

    # Break, study investigator swaps glasses/goggles/prisms
    show_message(instructions["get_study_investigator"], lockWait = True)

    # PP Exposure block
    if group in ("PP-None", "PP-MI", "PP-CTRL"): # Completing 20 PP trials
        show_message(instructions["Exposure_PP"], lockWait = True)
        run_block(block = 'PPExposure', group = group, participant_info = participant_info, df = df['Data'])
    else: # Completing 250 PP trials
        show_message(instructions["Exposure_PP"], lockWait = True)
        numTestingBlocks = 10
        for blockNum in range(numTestingBlocks):
            run_block(block = 'PP50Exposure', group = group, participant_info = participant_info, df = df['Data'])
            if blockNum < (numTestingBlocks- 1 ):
                show_message('Take a break!\nTo resume, press enter.', lockWait = True)

    # Break, study investigator swaps glasses/goggles/prisms
    show_message(instructions["get_study_investigator"], lockWait = True)

    # Exposure block
    if group in ("PP-None", "PP50"):
            show_message(instructions["PostTest"], lockWait = True)
    elif group == 'PP-MI':
        show_message(instructions["Exposure_MI"], lockWait = True)
    elif group == 'PP-CTRL':
        show_message(instructions["Exposure_CTRL"], lockWait = True)

    if group in ['PP-MI', 'PP-CTRL']: # Completing 230 trials of either MI or CTRL
        numTestingBlocks = 10
        for blockNum in range(numTestingBlocks):
            run_block(block = 'Exposure', group = group, participant_info = participant_info, df = df['Data'])
            if blockNum < (numTestingBlocks- 1 ):
                show_message('Take a break!\nTo resume, press enter.', lockWait = True)
    else: # Going straight to Post-Test
        run_block(block = 'PostTest', group = group, participant_info = participant_info, df = df['Data'])
        show_message(instructions["done"], lockWait = True)
        sys.exit()
    
    # Break, study investigator swaps glasses/goggles/prisms
    show_message(instructions["get_study_investigator"], lockWait = True)

    # PostTest block
    show_message(instructions["PostTest"], lockWait = True)
    run_block(block = 'PostTest', group = group, participant_info = participant_info, df = df['Data'])

    # Study complete!
    show_message(instructions["done"], lockWait = True)

   
if __name__ == "__main__":
    sys.exit(run())

# Things to do:
# TTL with goggles
# Add block num into exposure blocks # Do I need to do this? When divisible by 25, add an extra line that says block A
