# Python code to convert an image to ASCII image.
import argparse
import numpy as np
from PIL import Image
import colorsys
import time
import os
import cv2
import re
import shutil

gscale2 = "{=+^"#'@&#%_'

def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval

def natural_keys(text):
    return [ atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text) ]

def closest_color(target, color_palette):
    closest_color = None
    closest_distance = 10.0**301
    for color in color_palette:
        distance = (color[0] ^ target[0]) + (color[1] ^ target[1]) + (color[2] ^ target[2])
        if distance < closest_distance:
            closest_color = color
            closest_distance = distance
    return closest_color

def covertImageToAscii(fileName, columns, scale, colors, color_palette=[], can_print=True):
    # declare globals
    global gscale1, gscale2
    to_print = ""
 
    # open image and convert to grayscale
    image = Image.open(fileName)
    image.thumbnail((columns,columns), Image.Resampling.NEAREST)
    image_rgb = image.convert('RGB')
    image_gray = image.convert('L', dither=Image.Dither.RASTERIZE)

    # Get the color palette
    if color_palette == []:
        paletteimage = image_rgb.quantize(colors=colors)
        color_palette = paletteimage.getpalette()
        color_palette = [tuple(color_palette[i:i+3]) for i in range(0, len(color_palette), 3)]
        color_palette = [color for color in color_palette if any(c >= 16 for c in color)] # removes a color if all of the color channels are under 16
    
    color_palette += [(0, 0, 0)]
    if can_print: to_print = to_print + "\x1b[1mpalette:\x1b[22m "+str(color_palette)+"\n"
 
    # store dimensions
    W, H = image_gray.size[0], image_gray.size[1]
    # print("input image dims: %d x %d" % (W, H))
    w = W/columns
    h = w/scale
    rows = int(H/h)
     
    # print("tile dims: %d x %d" % (w, h))
    if can_print: to_print = to_print + "\x1b[1mcolumns:\x1b[22m %d, rows: %d" % (columns, rows)
 
    # check if image size is too small, dont think its needed tho
    if columns > W or rows > H:
        print("Image too small for specified columns!")
        exit(0)

    is_full_black = True
    # ascii image is a list of character strings
    aimg = {color: [] for color in color_palette}
    # generate list of dimensions
    for j in range(rows):
        y1 = int(j*h)
        
        # append an empty string
        for key in aimg.keys():
            aimg[key].append("")
        
        for i in range(columns):
 
            # crop image to ~~tile~~pixel
            x1 = int(i*w)
 
            # get pixel and name it avg cause im too lazy to change name
            avg = image_gray.getpixel((x1, y1))
            
            # look up ascii char
            gsval = gscale2[int((avg*(len(gscale2)-1))/255)]
            
            # append ascii char to string
            for key in aimg.keys():
                closest = closest_color(image_rgb.getpixel((x1, y1)), color_palette)
                if key == closest:
                    if closest != (0, 0, 0):
                        aimg[key][j] += gsval
                        is_full_black = False
                else:
                    aimg[key][j] += " "
    if can_print:
        print(to_print)
    # return txt image
    if is_full_black:
        return {(0,0,0):[]}
    return aimg

def get_frames(video, framerate):
    vidcap = cv2.VideoCapture(video)
    if not os.path.exists("converted/"):
        os.makedirs("converted/")
    else:
        for filename in os.listdir("converted/"):
            file_path = os.path.join("converted/", filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    def getFrame(sec):
        vidcap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
        hasFrames,image = vidcap.read()
        if hasFrames:
            cv2.imwrite("converted/"+str(count)+".png", image)
        return hasFrames
    sec = 0
    count=1
    cap = 1000
    success = getFrame(sec)
    while success and count < cap:
        count = count + 1
        sec = sec + 1/framerate
        sec = round(sec, 2)
        success = getFrame(sec)

# main() function
def main():
    # create parser
    descStr = "This program converts an image into ASCII art."
    parser = argparse.ArgumentParser(description=descStr)
    # add expected arguments
    parser.add_argument('--file', dest='imgFile', required=True)
    parser.add_argument('--scale', dest='scale', required=False)
    parser.add_argument('--out', dest='outFile', required=False)
    parser.add_argument('--columns', dest='columns', required=False)
    parser.add_argument('--framerate', dest='framerate', required=False)
    parser.add_argument('--colors', dest='colors', required=False)
 
    # parse args
    args = parser.parse_args()
   
    imgFile = args.imgFile
 
    # set output file
    outFile = 'out.txt'
    if args.outFile:
        outFile = args.outFile
 
    # set scale default as 0.43 which suits
    # a Courier font
    scale = 0.43
    if args.scale:
        scale = float(args.scale)
 
    # set columns
    columns = 50
    if args.columns:
        columns = int(args.columns)       

    # set framerate
    framerate = 5
    if args.framerate:
        framerate = int(args.framerate)       
 
    # set framerate
    colors = 8
    if args.colors:
        colors = int(args.colors)
    
    print('\x1b[1mgenerating ASCII art...\x1b[0m')

    output = ""
    chars = 0
    nr_frames = 0   
    frames = []
    # convert image to ascii txt
    timer = time.time()
    _,ext = os.path.splitext(imgFile)
    if ext in [".mp4",".mov",".webm",".avi"]:
        print("\x1b[1mconverting video to images...\x1b[22m")
        get_frames(imgFile, framerate)
        imgFile = "converted"

    if os.path.isdir(imgFile):
        print()
        for subdir, dirs, files in os.walk(imgFile):
            for ff in range(0, len(sorted(files, key=natural_keys))):
                nr_frames+=1
                can_print = False
                if ff % 5 == 0:
                    print("\x1b[1;34mframe", nr_frames, "\x1b[22;0m")
                    can_print = True
                aimg = covertImageToAscii(os.path.join(imgFile, sorted(files, key=natural_keys)[ff]), columns, scale, colors=colors, color_palette=[(255,255,255)], can_print=can_print)
                if can_print:
                    print()
                can_print = False
                del aimg[(0, 0, 0)]
                frames.append(aimg)
        
        nr_frames = 0
        last_char_is_line = False
        total_chars = 0
        for frame in frames:
            chars = 0
            nr_frames+=1
            for key, value in frame.items():
                color = colorsys.rgb_to_hsv(*key)
                output += (";" if not last_char_is_line else "")+"\n"+str(round(color[0]*360))+","+str(color[1])+","+str(color[2]/255)+";"
                last_char_is_line = False
                i=0
                for row in value:
                    modded_row = None
                    if i != 0 and i != len(value)-1:
                        modded_row = row.rstrip()
                    elif i == len(value)-1:
                        modded_row = row[0]
                    else:
                        modded_row = row
                    output += "\n"+modded_row
                    for _ in modded_row:
                        chars+=1
                        total_chars+=1
                    i+=1
            output += "|"
            last_char_is_line = True
            print("\x1b[34;1mframe", str(nr_frames) + ":\x1b[" + ("32m" if chars < 16384 else "31m"), str(chars)+" characters\x1b[0m")
        print("\x1b[34;1mtotal characters:", str(total_chars)+"\x1b[0m")
        meta = str(1/framerate)+"|"
        output = output[2:]
        output = (output[::-1]+meta[::-1])[::-1] # append metadata to the start

        # write to file
        with open(outFile, 'w') as f:
            f.write(output)   
    else:
        print()
        aimg = covertImageToAscii(imgFile, columns, scale, colors=colors, color_palette=[(238,23,231),(2,209,144),(255,255,255),(194,23,21)])
        del aimg[(0, 0, 0)]

        last_char_is_line = False
        for key, value in aimg.items():
            color = colorsys.rgb_to_hsv(*key)
            output += (";" if not last_char_is_line else "")+"\n"+str(round(color[0]*360))+","+str(color[1])+","+str(color[2]/255)+";"
            last_char_is_line = False
            i=0
            for row in value:
                modded_row = None
                if i != 0 and i != len(value)-1:
                    modded_row = row.rstrip()
                elif i == len(value)-1:
                    modded_row = row[0]
                else:
                    modded_row = row
                output += "\n"+modded_row
                for _ in modded_row:
                    chars+=1
                i+=1
            output += "|"
            last_char_is_line = True
        output = output[2:]
        output = (output[::-1]+"|0")[::-1] # append metadata to the start
        print("\x1b[1;" + ("32m" if chars < 16384 else "31m") + str(chars)+" characters\x1b[0m")

        # write to file
        with open(outFile, 'w') as f:
            f.write(output)
    print("\n\x1b[1melapsed time:\x1b[22m", round(time.time() - timer, 5))
    
    print("\n\x1b[1mASCII art written to %s" % outFile+"\x1b[0m")
 
# call main
if __name__ == '__main__':
    main()