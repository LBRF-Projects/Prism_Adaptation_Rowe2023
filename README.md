# Prism Adaptation & Motor Imagery

This repository contains the experiment code for a study looking at whether or not internal models can be updated when performing motor imagery.
This is tested using a simple reach and point task.

## Overview

In this experiment there are three trial types: physical practice, motor imagery, and control. 

On **physical practice trials**, a target appears randomly on one of three locations on a touchscreen monitor and participants
release the spacebar to reach and point to the target. Upon touching the screen, the target disappears and the pixel coordinates
of the location on the screen are recorded.

On **motor imagery trials**, a target appears randomly on one of three locations on the touchscreen monitor.
Participants keep their finger pressed on the spacebar while imagining reaching and pointing to the target. 
When the spacebar is released, the target disappears from the screen.

On **control trials**, a target appears randomly on one of three locations on the touchscreen monitor.
Participants keep their finger pressed on the spacebar while imagining a line drawing itself from the center of the
target to the participant's dominant index finger. When the spacebar is released, the target disappears from the screen.

The experiment has four blocks: familiarization, baseline testing, prism exposure, and final testing. 
- **Familiarization**: consists of 40 physical practice trials. Participants wear clear, non-prism lenses during this block.
- **Baseline Testing**: consists of 10 physical practice trials. Participants wear [PLATO goggles](https://www.translucent.ca/products/plato-visual-occlusion-spectacles/) during this block. 
- **Prism exposure**: consists of 250 physical practice, motor imagery, or control trials. Participants wear goggles with prism lenses attached during this block.
- **Final Testing**: consists of 10 physical practice trials. Participants wear PLATO goggles during this block.

Distance of the participant's finger from the center of the circular target in the x (horizontal) direction, measured in mm, are recorded during the baseline
and final testing blocks, allowing aftereffects to be measured and compared across groups. 

## Requirements

This experiment was programmed in Python (Version 3.9.13).

To use the task, you will also need a USB or wireless keyboard, a USB or wireless touchscreen tablet, and PLATO goggles. 

## Getting Started

You can clone this repository to your compuyter using Git by opening a terminal in your destination folder and running the following command: 
```

git clone https://github.com/LBRF-Projects/Prism_Adaptation_Rowe2023.git

```

### Pipenv Installation
To install the task and its dependencies in a self-contained Python environment, run the following commands
in a terminal window inside the same folder as this README:

```

pip install pipenv
pipenv install

```

These commands should create a fresh environment for the task with all its dependencies installed.
Note that to run commands using this environment, you will need to prefix them with ```pipenv run```
(e.g. ```pipenv run python prism_adaptation.py```).


### Running the experiment
To run the experiment in the self-contained Pipenv environment, run in the terminal ```pipenv run python prism_adaptation.py```.
