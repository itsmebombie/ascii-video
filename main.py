_EXTRA_SETTINGS = {
    "AUTO_PALETTE": True,  # enable auto palette generation
    "FASTER_AUTO_PALETTE": True,  # faster, less precise color palette generation
    # i would say it looks better on videos that have many colors but you used --colors 4 or something
    "CUSTOM_PALETTE": [
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    ],  # only applied when AUTO_PALETTE is set to False
}

# heavily modified version of https://www.geeksforgeeks.org/converting-image-ascii-image-python/
from PIL import Image
import moviepy.editor as mp
import argparse
import colorsys
import time
import os
import cv2
import re
import shutil
import extcolors

gscale2 = "^+={"  #'@&#%_'
palette = []

os.system("")


def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text):
    return [atof(c) for c in re.split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", text)]


def closest_color(target):
    global palette

    closest_color = None
    closest_distance = 10.0**301
    for color in palette:
        distance = (
            (color[0] ^ target[0]) + (color[1] ^ target[1]) + (color[2] ^ target[2])
        )
        if distance < closest_distance:
            closest_color = color
            closest_distance = distance
    return closest_color


def gen_palette(fileName, colors, image_rgb):
    if _EXTRA_SETTINGS["FASTER_AUTO_PALETTE"]:
        color_palette = image_rgb.quantize(colors=colors).getpalette()
        return [
            tuple(color_palette[i : i + 3]) for i in range(0, len(color_palette), 3)
        ][:colors]
    else:
        color_palette = extcolors.extract_from_path(
            fileName, tolerance=colors, limit=colors
        )[0]
        return [color_palette[i][0] for i in range(0, len(color_palette))]


def covertImageToAscii(
    fileName, columns, scale, colors, nr_frames, color_palette=[], can_print=True
):
    # declare globals
    global gscale2, palette
    if can_print:
        to_print = "\x1b[1;34mframe " + str(nr_frames) + " \x1b[22;0m\n"

    # open image and convert to grayscale
    image = Image.open(fileName)
    image.thumbnail((columns, columns), Image.Resampling.NEAREST)
    image_rgb = image.convert("RGB")
    image_gray = image.convert("L")

    # Get the color palette
    if color_palette == []:
        color_palette = gen_palette(fileName, colors, image_rgb)
        color_palette = [
            color for color in color_palette if any(c >= 16 for c in color)
        ]
        # if can_print: to_print = to_print + "\x1b[1mpalette:\x1b[22m "+str(color_palette)+"\n" # this breaks some things and im too lazy to patch it up so imma leave it like this

    color_palette += [(0, 0, 0)]
    palette = color_palette

    # store dimensions
    W, H = image_gray.size[0], image_gray.size[1]
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
            avg = image_gray.getpixel((x1, y1)) * 1.5
            # look up ascii char
            gsval = gscale2[
                max(0, min(int((avg * (len(gscale2) - 1)) / 255), len(gscale2) - 1))
            ]  # very readable

            # append ascii char to string
            for key in aimg.keys():
                closest = closest_color(image_rgb.getpixel((x1, y1)))
                if key == closest:
                    if closest != (0, 0, 0):
                        aimg[key][j] += gsval
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

    if is_full_black:
        return {(0, 0, 0): []}, 0
    if can_print:
        to_print += (
            "\n\x1b["
            + ("32m" if chars < 16384 else "31m")
            + str(chars)
            + " characters\x1b[0m"
        )
        print("\x1b[" + str(to_print.count("\n") + 1) + "A" + to_print)
    # return txt image
    return aimg, chars, rows


def get_frames(video, framerate, columns, cap):
    clip = mp.VideoFileClip(video)
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

    def getFrame(sec):
        vidcap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        hasFrames, image = vidcap.read()
        if hasFrames:
            cv2.imwrite("converted/" + str(count) + ".png", image)
        return hasFrames

    sec = 0
    count = 1
    success = getFrame(sec)
    while success and count < cap:
        count = count + 1
        sec = sec + 1 / framerate
        sec = round(sec, 2)
        success = getFrame(sec)
        if count % 6 == 0:
            print("frame", count, "\x1b[1A")


# main() function
def main():
    # create parser
    descStr = "This program converts an image into ASCII art."
    parser = argparse.ArgumentParser(description=descStr)

    # add expected arguments
    parser.add_argument("--file", dest="imgFile", required=True)
    parser.add_argument("--columns", dest="columns", required=False)
    parser.add_argument("--framerate", dest="framerate", required=False)
    parser.add_argument("--colors", dest="colors", required=False)
    parser.add_argument("--frame-cap", dest="cap", required=False)

    # parse args
    args = parser.parse_args()

    # image
    imgFile = args.imgFile

    # set output file
    outFile = "out.txt"

    # literally the ratio between height and width or something
    scale = 0.4

    # set columns
    columns = 50
    if args.columns:
        columns = int(args.columns)

    # set framerate
    framerate = 12
    if args.framerate:
        framerate = int(args.framerate)

    # set colors
    colors = 8
    if args.colors:
        colors = int(args.colors)

    # set colors
    cap = 2500
    if args.cap:
        colors = int(args.cap)

    print("\x1b[1mgenerating video...\x1b[0m")

    output = ""
    nr_frames = 0
    total_chars = 0
    frames = []
    # convert image to ascii txt
    timer = time.time()
    _, ext = os.path.splitext(imgFile)
    if ext in [".mp4", ".mov", ".webm", ".avi"]:
        print("\x1b[1mconverting video to images...\x1b[0m")
        get_frames(imgFile, framerate, columns, cap)
        print()
        imgFile = "converted"

    print("\n\n")
    if os.path.isdir(imgFile):
        print()
        rows = 0
        for _, _, files in os.walk(imgFile):
            for ff in range(0, len(sorted(files, key=natural_keys))):
                nr_frames += 1
                can_print = False
                if ff % 3 == 0:
                    can_print = True

                aimg, chars, rows = covertImageToAscii(
                    os.path.join(imgFile, sorted(files, key=natural_keys)[ff]),
                    columns,
                    scale,
                    colors,
                    nr_frames,
                    color_palette=(
                        []
                        if _EXTRA_SETTINGS["AUTO_PALETTE"]
                        else _EXTRA_SETTINGS["CUSTOM_PALETTE"]
                    ),
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
            color_palette=(
                [] if _EXTRA_SETTINGS["AUTO_PALETTE"] else _EXTRA_SETTINGS["CUSTOM_PALETTE"]
            ),
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
            output += "|"
            last_char_is_line = True
        meta = ";".join([0, str(columns), str(rows)]) + "|"
        output = output[2:]
        output = (output[::-1] + meta[::-1])[::-1]  # append metadata to the start

        # write to file
        with open(outFile, "w") as f:
            f.write(output)

    print("\x1b[1melapsed time:\x1b[0m", round(time.time() - timer, 5))
    print("\x1b[2K\n\x1b[1moutput written to %s" % outFile + "\x1b[0m")


# call main
if __name__ == "__main__":
    main()
