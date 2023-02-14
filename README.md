# Info

ascii-video is a program written in Python and SPWN that is designed to convert mostly videos (but images too) to ASCII art and put them in Geometry Dash. 

# Getting Started

First of all, make sure you have [SPWN](https://github.com/Spu7Nix/SPWN-language) and [Python](https://python.org) installed.
Then clone this repository to your computer in an easily accessible place.

Make sure you have a video/image/folder of images that you want to convert. Moving it to your working directory would be a good idea. 
If you don't, you can always use a video from [here.](./examples/)
Copy the path of your video/image/folder.

Open a terminal and make sure it's in the same directory as your working directory.
Type in `py main.py --file {path}` and press enter.
If you get any missing libraries errors, download them using `py -m pip install {library}`
Also if `py` doesn't work for you, try using `python3` or check if Python is downloaded.

After it's done compiling, you can type `spwn build main.spwn --allow readfile` so it gets built to Geometry Dash.
Make sure Geometry Dash is closed before executing that command though, otherwise it won't work.

If everything went according to plan, you should now have an ASCII video/image in your most recent Geometry Dash level!

# Documentation

This Python program has several options that can be changed using command flags or by changing the `_EXTRA_SETTINGS` variable [at the top of the main.py file.](./main.py#L1)

## Flags

These are all the command flags and what they do:

### --file

This flag is a mandatory flag. You can specify the video/image/folder of images you want to convert here.
Example: `py main.py --file examples/cutmeoff.mp4`

### --columns

This flag is an optional flag. You can specify the desired amount of columns (or the desired horizontal resolution) here. More columns = more characters.
Example: `py main.py --file examples/cutmeoff.mp4 --columns 50`

### --framerate

This flag is an optional flag. You can specify the desired framerate (FPS) here. Higher framerate = more frames which is more objects and characters.
Example: `py main.py --file examples/cutmeoff.mp4 --framerate 12`

### --colors

This flag is an optional flag. You can specify the desired amount of colors here. Each color is a text object. More colors = more characters.
Example: `py main.py --file examples/cutmeoff.mp4 --colors 8`

### --frame-cap

This flag is an optional flag. You can specify the desired frame numbers it compiles before it stops here.
Example: `py main.py --file examples/cutmeoff.mp4 --frame-cap 2500`

## Extra Settings

These are all of the extra settings and what they do (they can be changed [at the top of the main.py file.](./main.py#L1)):

### FASTER_COLOR_DISTANCE_FORMULA

This setting determines whether the program uses a faster method of approximating each pixel's color value to the closest target value. If this is set to False, the Python program is going to use the Euclidean distance formula instead of the Manhattan distance formula. Using pre-computed square and square root arrays, setting it to False is going to make the script just a bit slower but the end result may look somewhat different.
This will change the video just ever so slightly so only change the value to False when you really need to (or if you're just playing around).

### AUTO_PALETTE

This setting determines whether the program generates the palettes automatically for each image. If you disable this, you will need to edit the `PALETTE` variable according to your necessities.

### FASTER_AUTO_PALETTE

This setting determines whether the program uses a faster method of auto-generating the palettes for each image. If this is set to True, the Python program is going to be faster and the end result may look better for videos with lots of colors and the `--colors` flag being set to a small amount such as `4`.
For videos with lots of colors and with the `--colors` flag bigger than `8`, disabling this option may result in better color palettes but also a 100% increase in the compilation time.
You can also try this when your video just doesn't look right. And if this doesn't fix it, then you can try increasing the `--colors` flag or try using a custom palette.

### CUSTOM_PALETTE

This setting is only applied when `AUTO_PALETTE` is disabled. With this setting you can configure a custom palette for the video/image. The setting's format must look like this: `[(0, 0, 0), (255, 0, 0)]`, where every tuple is an RGB value.

## SPWN Setup

These are all of the SPWN settings and what they do (they can be changed [at the top of the main.spwn file.](./main.spwn#L3)):

### offset

The amount of editor units the video is offset on the X axis (30 units = 1 grid space).

### groups_in_use

The amount of groups you want to get used. Unless you want to use the groups for something else, you should totally allocate all of the groups to the video, and there are 2 reasons for that.

1. Allocating too little groups to the video can cause multiple frames to be visible at the same time (we are talking less than 100 groups), so you can't do that.
2. There is a weird bug that moves the whole canvas by a visible amount every `n` frames, where `n` is the amount of groups you allocated.

Also, allocating too many groups will probably error since you can only have 999 groups per level.
Sometimes, when allocating to many groups, the frames and the move triggers might go invisible so make sure you don't use too many groups.

### use_1x

Changes the speed from 4x to 1x. This won't change the speed of the video but it will take longer to load and rise the chance of crashing while loading. Only change this if you need to, for example, have gameplay while the video is running in the background.

### size

Changes the height of the video, which changes the whole video's size with it. (in full blocks)

# Limits

Keep in mind that having over 16,384 characters per frame can cause some characters to dissapear due to a limit in Geometry Dash's code. You can see the amount of characters used on every 3rd frame while the Python script is running.
Also, you can't have too many characters in the same place because that will also make the game crash. It's currently unknown how many characters is too much, but once I (or somebody else) finds out, the code along with this file will get updated.

# Misc

If you need more help and the documentations aren't enough, you can always contact me in the [SPWN Discord Server](https://discord.gg/VBFhYemtsZ) by pinging `@bombie` in `#general`. 
Make sure to read the server's rules before though!

Good luck and happy converting!
