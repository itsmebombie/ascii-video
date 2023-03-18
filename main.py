_EXTRA_SETTINGS = {
    "FASTER_COLOR_DISTANCE_FORMULA": True, # uses manhattan distance formula instead of euclidean distance formula when calculating the color palette of a frame
    # it may give slightly less accurate results (not that noticeable) and it can use more characters but it's a bit faster 
    "AUTO_PALETTE": True,  # enable auto palette generation
    "CUSTOM_PALETTE": [
        (255, 255, 255),
    ],  # only applied when AUTO_PALETTE is set to False
}

# heavily modified version of https://www.geeksforgeeks.org/converting-image-ascii-image-python/

import argparse
import colorsys
import math
import os
import re
import shutil
import time

import cv2
import moviepy.editor as mp
from PIL import Image

ascii_characters = "^+={"
palette = []

os.system("")


def natural_keys(text):
    return [float(c) for c in re.findall(r"[+-]?\d+(?:\.\d+)?", text)]


if not _EXTRA_SETTINGS["FASTER_COLOR_DISTANCE_FORMULA"]:
    square_8bit = tuple([i**2 for i in range(257)]) + tuple([(255-i)**2 for i in range(256)]) # (0,1,4,9,16,...65025,65536,65025,...9,4,1,0)
    # square_sub_8bit = tuple([tuple([(i-j)**2 for j in range(i)] + [j**2 for j in range(257-i)]) for i in range(257)]) # ((0,1,4,9,...65025,65536),(1,0,1,4,9,...64516,65025),...(65536,65025,...9,4,1,0))
    sqrt_20bit = tuple([math.sqrt(i) for i in range(2**18+1)]) # (sqrt(0),sqrt(1),sqrt(2),...sqrt(262144))
else:
    abs_8bit = tuple([i for i in range(257)] + [255-i for i in range(256)]) # (0,1,2,3,...255,256,255,...3,2,1,0)


def closest_color(target):
    closest_color = None
    closest_distance = 10.0**301
    for color in palette:
        if color == target:
            return color
        
        r, g, b = color
        tr, tg, tb = target

        if _EXTRA_SETTINGS["FASTER_COLOR_DISTANCE_FORMULA"]:
            distance = abs_8bit[r - tr]
            + abs_8bit[g - tg]
            + abs_8bit[b - tb]
        else:
            distance = sqrt_20bit[
                square_8bit[r - tr]
                + square_8bit[g - tg]
                + square_8bit[b - tb]
            ]

        if distance < closest_distance:
            closest_color = color
            closest_distance = distance

    return closest_color


def gen_palette(fileName, colors, image_rgb):
    color_palette = image_rgb.quantize(colors=colors).getpalette()
    return tuple([tuple(color_palette[i : i + 3]) for i in range(0, len(color_palette), 3)][:colors])


last_frame = {}
def covertImageToAscii(fileName, columns, scale, colors, nr_frames, ascii_multi, color_palette=[], can_print=True):
    # declare globals
    global ascii_characters, palette, last_frame
    if can_print:
        to_print = "\x1b[1;34mframe " + str(nr_frames) + " \x1b[22;0m\n"

    # open image and convert to grayscale
    img_cv = cv2.imread(fileName)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    image_rgb = Image.fromarray(img_rgb)
    image_rgb.thumbnail((columns, columns), Image.Resampling.NEAREST)
    image_gray = image_rgb.convert("L")

    # Get the color palette
    if color_palette == []:
        color_palette = gen_palette(fileName, colors, image_rgb)
        color_palette = [color for color in color_palette if any(c >= 16 for c in color)]
        color_palette += [(0, 0, 0)]

    # if can_print: to_print = to_print + "\x1b[1mpalette:\x1b[22m "+str(color_palette)+"\n" # debug
    
    palette = color_palette

    # store dimensions
    W, H = image_gray.size
    # print("input image dims: %d x %d" % (W, H))
    w = W / columns
    h = w / scale
    rows = int(H / h)

    # print("tile dims: %d x %d" % (w, h))
    if can_print:
        to_print += "\x1b[1mcolumns:\x1b[22m %d, rows: %d" % (columns, rows)

    # check if image size is too small, dont think its needed tho
    if columns > W or rows > H:
        image_gray.thumbnail((columns, columns), Image.NEAREST)
        image_rgb.thumbnail((columns, columns), Image.NEAREST)

    is_full_black = True
    # ascii image is a list of character strings
    aimg = {color: [] for color in color_palette}
    chars = 0

    image_gray_loaded = image_gray.load()
    image_rgb_loaded = image_rgb.load()
    # generate list of dimensions
    for j in range(rows):
        y1 = int(j * h)
        # last character that isnt empty/a space
        last_character = {key: None for key in aimg.keys()}
        # append an empty string
        for key in aimg.keys():
            aimg[key].append("")

        for i in range(columns):
            # crop image to ~~tile~~pixel
            x1 = int(i * w)
            # get pixel and name it avg cause im too lazy to change name
            avg = image_gray_loaded[x1, y1] * ascii_multi
            # look up ascii char
            ascii_char = ascii_characters[
                max(0, min(int((avg * (len(ascii_characters) - 1)) / 255), len(ascii_characters) - 1))
            ]  # very readable

            # append ascii char to string
            for key in aimg.keys():
                closest = closest_color(image_rgb_loaded[x1, y1])
                if key == closest:
                    if closest != (0, 0, 0):
                        aimg[key][j] += ascii_char
                        is_full_black = False
                        last_character[key] = i
                else:
                    aimg[key][j] += " "

        for key in aimg.keys():
            if last_character[key] == None:
                if j == rows - 1:
                    aimg[key][j] = " "
                elif j != 0:
                    aimg[key][j] = ""
            else:
                if j != 0:
                    aimg[key][j] = aimg[key][j][: last_character[key] + 1]

            for _ in aimg[key][j]:
                chars += 1

    if last_frame == aimg:
        chars = 0
    last_frame = aimg

    if is_full_black:
        if can_print:
            to_print += "\n\x1b[32m0 characters\x1b[0m"
            print("\x1b[" + str(to_print.count("\n") + 1) + "A" + to_print)
        return {(0, 0, 0): []}, 0, rows
    
    if can_print:
        to_print += (
            "\n\x1b["
            + ("32m" if chars < 16384+1 else "31m")
            + str(chars)
            + " characters\x1b[0m"
        )
        print("\x1b[" + str(to_print.count("\n") + 1) + "A" + to_print)
    
    # return txt image
    return aimg, chars, rows


def get_frames(video, framerate, columns, cap):
    clip = mp.VideoFileClip(video).without_audio()
    clip = clip.set_fps(framerate).subclip(0, min(cap/clip.fps, clip.duration))
    clip_r = clip.resize(width=columns)
    clip_r.write_videofile("temp.mp4")

    vidcap = cv2.VideoCapture("temp.mp4")
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
                print("Failed to delete %s. Reason: %s" % (file_path, e))

    count = 1
    success, image = vidcap.read()
    while success and count < cap:
        cv2.imwrite("converted/" + str(count) + ".png", image)
        success, image = vidcap.read()
        count += 1
        if count % 6 == 0:
            print("frame", count, "\x1b[1A")


# main() function
def main():
    # create parser
    descStr = "This program converts a video / image into ASCII art. The SPWN program will then append the output to GD."
    parser = argparse.ArgumentParser(description=descStr)

    # add expected arguments
    parser.add_argument("--file", dest="imgFile", required=True)
    parser.add_argument("--columns", dest="columns", required=False)
    parser.add_argument("--framerate", dest="framerate", required=False)
    parser.add_argument("--colors", dest="colors", required=False)
    parser.add_argument("--frame-cap", dest="cap", required=False)
    parser.add_argument("--ascii-multi", dest="ascii_multi", required=False)

    # parse args
    args = parser.parse_args()

    # image
    imgFile = args.imgFile

    # set output file
    outFile = "out.txt"

    # literally the ratio between the height and the width or something
    scale = 0.4

    # set columns
    columns = 50
    if args.columns:
        columns = int(args.columns)

    # set framerate
    framerate = 12
    if args.framerate:
        framerate = float(args.framerate)

    # set colors
    colors = 8
    if args.colors:
        colors = int(args.colors)

    # set cap
    cap = 2500
    if args.cap:
        cap = int(args.cap)
    
    # set ascii char multiplier
    ascii_multi = 1.25
    if args.ascii_multi:
        ascii_multi = int(args.ascii_multi)

    print("\x1b[1mgenerating...\x1b[0m")

    output = ""
    nr_frames = 0
    total_chars = 0
    frames = []
    # convert image to ascii txt
    timer = time.time()
    _, ext = os.path.splitext(imgFile)
    if ext in [".mp4", ".mov", ".mkv", ".webm", ".avi"]:
        print("\x1b[1mconverting video to images...\x1b[0m")
        get_frames(imgFile, framerate, columns, cap)
        print()
        imgFile = "converted"

    print("\n\n")
    if os.path.isdir(imgFile):
        print()
        rows = 0
        for _, _, files in os.walk(imgFile):
            sorted_files = sorted(files, key=natural_keys)
            for ff in range(0, len(sorted_files)):
                nr_frames += 1
                can_print = False
                if ff % 6 == 0:
                    can_print = True

                aimg, chars, rows = covertImageToAscii(
                    os.path.join(imgFile, sorted_files[ff]),
                    columns,
                    scale,
                    colors,
                    nr_frames,
                    ascii_multi,
                    color_palette=([] if _EXTRA_SETTINGS["AUTO_PALETTE"] else (_EXTRA_SETTINGS["CUSTOM_PALETTE"] + [(0, 0, 0)])),
                    can_print=can_print,
                )
                total_chars += chars
                rows = rows

                can_print = False
                del aimg[(0, 0, 0)]
                frames.append(aimg)

        nr_frames = 0
        last_char_is_line = False
        for frame in frames:
            nr_frames += 1
            for key, value in frame.items():
                color = colorsys.rgb_to_hsv(*key)
                output += (
                    (";" if not last_char_is_line else "")
                    + "\n"
                    + str(round(color[0] * 360))
                    + ","
                    + str(color[1])
                    + ","
                    + str(color[2] / 255)
                    + ";"
                )
                last_char_is_line = False
                for row in value:
                    output += "\n" + row
            output += "|"
            last_char_is_line = True
        print("\x1b[3A\x1b[34;1mtotal characters:", str(total_chars) + "\x1b[0m")
        meta = ";".join([str(1 / framerate), str(columns), str(rows)]) + "|"
        output = output[2:]
        output = (output[::-1] + meta[::-1])[::-1]  # append metadata to the start

        # write to file
        with open(outFile, "w") as f:
            f.write(output)
    else:
        aimg, _, rows = covertImageToAscii(
            imgFile,
            columns,
            scale,
            colors,
            1,
            ascii_multi,
            color_palette=([] if _EXTRA_SETTINGS["AUTO_PALETTE"] else (_EXTRA_SETTINGS["CUSTOM_PALETTE"] + [(0, 0, 0)])),
        )
        rows = rows
        del aimg[(0, 0, 0)]

        last_char_is_line = False
        for key, value in aimg.items():
            color = colorsys.rgb_to_hsv(*key)
            output += (
                (";" if not last_char_is_line else "")
                + "\n"
                + str(round(color[0] * 360))
                + ","
                + str(color[1])
                + ","
                + str(color[2] / 255)
                + ";"
            )
            last_char_is_line = False
            for row in value:
                output += "\n" + row
        meta = ";".join(["0", str(columns), str(rows)]) + "|"
        output = output[2:]
        output = (output[::-1] + meta[::-1])[::-1] + "|"  # append metadata to the start

        # write to file
        with open(outFile, "w") as f:
            f.write(output)

    print("\x1b[1melapsed time:\x1b[0m", round(time.time() - timer, 5))
    print("\x1b[2K\n\x1b[1moutput written to %s" % outFile + "\x1b[0m")


# call main
if __name__ == "__main__":
    main()
