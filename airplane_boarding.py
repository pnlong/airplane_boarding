# README
# Phillip Long
# January 6, 2023

# Sitting in the Montreal airport (YUL) waiting to board my return flight on January 4th,
# I thought to myself, "Holy this is taking a long time!"
# It was. On a flight supposed to board at 5:40 PM, we didn't even begin boarding until 6:30 PM.
# The flight didn't take off until 7:15 PM.
# 45-minute boarding time felt a bit much. I wondered: "Was there a faster way to board a plane?"
# This thought brought me back to a CGP Grey Video, "The Better Boarding Method Airlines Won't Use"
#                                                    (https://www.youtube.com/watch?v=oAHbLRjF0vo)
# I remarked to my dad,
# "I bet I could make a simulation out of this to find out which boarding method is the fastest!"
# And so, here I am.


# python ~/airplane_boarding/airplane_boarding.py window_width window_height

# sys.argv[1] = width of window (in pixels) [integer, NOT REQUIRED]
# sys.argv[2] = height of window (in pixels) [integer, NOT REQUIRED]
# if no arguments provided, resort to defaults

# ~~~~~~~~~~~~~~~~ Introduction ~~~~~~~~~~~~~~~~~~

# IMPORTS
##################################################

# IMPORTS
import tkinter # for User Interface (UI)
from tkinter import ttk # for scrollbars
from time import sleep
from pandas import DataFrame # for seat_layouts
from pandas import concat
import numpy # for seating array
from string import ascii_uppercase # to help with seats
from random import sample # for skintones
from random import randint # for spawning
from itertools import product # for seat combinations
from itertools import chain # for seat_list
import sys # for window_width and window_height

##################################################

# SEAT LAYOUTS
##################################################
# seat variables
n_exits = 1 # including entrance door
seat_layouts = DataFrame.from_dict( # number of walkways must remain constant, seat_depth and leg_room in terms of passenger diameters
    columns =          ("seat_layout",  "n_rows","leg_room", "seat_depth"),
    data = {
    "first"           :(     "A BC D" ,        5,      2.00,         2.00),
    "business"        :(     "A BC D" ,        5,      1.80,         1.80),
    "premium economy" :(    "AB CD EF",        5,      1.80,         1.60),
    "economy"         :(    "AB CD EF",       20,      1.60,         1.60)
    },
    orient = "index").astype({
        "seat_layout": "string",
        "n_rows"     : "int64",
        "leg_room"   : "float64",
        "seat_depth" : "float64"
    }
)
##################################################

# IMPORTANT VARIABLES
##################################################
# VARIABLES

# window
try:
    window_width = int(sys.argv[1])
    window_height = int(sys.argv[2])
except:
    window_width = 1350 # integer
    window_height = 350 # integer

# the distance from the edge of the window the plane's cockpit wall will sit (margin size)
plane_body_margin_fraction = 1.01

# colors
canvas_background_color = "#F0F0F0" # grey
plane_color = "#E5FFFB"
top_tail_wing_color = "#D4E9E6"
wall_color = "#B3C4C1"
stairs_color = "#FCF9D8"
stairs_outline_color = "#CCAA60"
seat_color = "#000080" # navy
seat_outline_color = "#99A3F2" # darker navy
exit_color = "#FF0000" # red
passenger_color = ("#FFDBAC", "#F1C27D", "#E0AC69", "#C68642", "#8D5524") # for various skintones, choose at random
passenger_outline_color = "#693F1A" # dark brown

# line widths
wall_width = 2 # default wall width
seat_outline_width = 2
passenger_outline_width = 2 # in pixels


# VARIABLES BY CATEGORY
# wall variables
dash_pattern = (10, 5)
display_line_between_wings_and_body = True
display_exits = True

# passenger variables
# passenger size is determined by number of rows
ts = 0.02 # tickspeed (in seconds)

n_row_min, n_row_max = 5, 50 # minimum and maximum number of rows (inclusive)
n_row_section_min, n_row_section_max = 3, n_row_max
gateway_size = 1.50 # in terms of passenger diameters, MUST BE GREATER THAN 1.00, or passengers wont fit; how big the gateway is, and thus the aisles on the plane
gate_offset = 0.75 # if there is no first class, then this is the amount the gate is offset (in passenger diameters)

##################################################

# MANIPULATE VARIABLES, HELPER FUNCTIONS
##################################################

# save copy of seat_layouts as is now so I can see if it's changed later
seat_layouts_original = seat_layouts[["seat_layout", "n_rows"]]

# trim seat layouts to make sure it is formatted well
seat_layouts["seat_layout"] = seat_layouts["seat_layout"].transform(lambda seat_layout: seat_layout.strip().upper())

# number of seats per row in a section and number of walkways per section
seat_layouts["n_seats_per_row"] = numpy.array(tuple(len("".join(row.split())) for row in seat_layouts["seat_layout"]), dtype = "int64")
seat_layouts["n_walkways"] = numpy.array(tuple(len(row.split()) - 1 for row in seat_layouts["seat_layout"]), dtype = "int64")

# if n_walkways is not the same across sections where there is rows, then cancel
if not all((n_walkways == numpy.mean(a = seat_layouts.loc[seat_layouts["n_rows"] != 0, "n_walkways"], axis = 0) for n_walkways in seat_layouts.loc[seat_layouts["n_rows"] != 0, "n_walkways"])):
    raise Exception("n_walkways exception: In the sections for which there are rows, the number of walkways is not equal.")

# at this point, we've already established that the number of walkways is the same, since the program would have been terminated by the previous line
n_walkways = int(numpy.mean(a = seat_layouts.loc[seat_layouts["n_rows"] != 0, "n_walkways"], axis = 0)) # the mean will be a whole number, since all of the walkway counts are the same
if not 1 <= n_walkways <= 2:
    raise Exception("n_walkways exception: Number of walkways is invalid. The MINIMUM number of walkways is 1; the MAXIMUM is TWO.")

# calculate plane chasse dimensions from window dimensions
plane_length = window_width / plane_body_margin_fraction # in pixels
# plane_width calculated later using row and seat information

# booleans for seat sections
has_first_class = (seat_layouts.loc["first", "n_rows"] != 0)

# tkinter's canvas requires I state a coordinate twice for a straight, not smoothed, line
# this lambda will help with that
straight_lines = lambda x : sum([(element, element) for element in x], ())

# reset indicies of a pandas dataframe after inserting a row somewhere
reset_indicies = lambda df: df.sort_index().reset_index(drop = True)

# get midpoint of two points
midpoint = lambda a, b: (a + b) / 2

# plot a point (FOR DEBUGGING)
point_radius = 3
plot_point = lambda canvas, coords: canvas.create_oval(tuple(numpy.array(coords) - point_radius), tuple(numpy.array(coords) + point_radius), fill = "red", outline = "black", width = 1)

##################################################

# DEFINE BASIC POINTS FOR PLANE
##################################################

# walls and points of airplane diagram
# note that in tkinter, (0,0) is always the top left corner, (1,1) is down and to the right

#                                                             ^
#                                                  x5         | wfhe
#                                                             v
#         (x0, y0)-----------------------x3-----x4-----------------(x1, y0)
#            |                                                        |
#            |                                                        |
# <--wfve--> |                                                        |
#            |                                                        |
#            |                                                        |
#         (x0, y1)-x0_os  x2 x2_os-------x3-----x4-----------------(x1, y1)
#                    |         |
#                    |         |                   x5
#                 (x8, y3)     |
#                   /     (x2_os,y2)
#                 /           /  
#               /            /  <---- (x_spawn, y_spawn)
#              x6-----------x7

# wall constants
# wall_fraction_from_(horizontal/vertical)_edge
wfve = 1/7 # fraction of the screen width from the vertical edge, MUST BE LESS THAN 1/2
wfve_tail = 1.07 * wfve # the tail is slightly longer than wfve, so this variable reflects this fact
canvas_width = plane_length / (1 - (2 * wfve)) # calculate canvas width

# define points
x0 = wfve * canvas_width
x1 = (1 - wfve_tail) * canvas_width

# redefine plane length, since the chasse is a little bit shorter due to the longer tail section
plane_length = x1 - x0

##################################################


# ~~~~~~~~~~~~~~~~~~~~ Seats ~~~~~~~~~~~~~~~~~~~~~

# CLEAR UP VARIABLES
##################################################

# maximum number of exits is 3; minimum is 1 (the front door)
if n_exits > 3:
    n_exits = 3
elif n_exits < 1:
    n_exits = 1

# adjust if number of rows exceed the defined maximum and minimum amounts
n_row = sum(seat_layouts["n_rows"])
while (not n_row_min <= n_row <= n_row_max): # while n_row continues to be more or less than maximum/minimum
    for section in seat_layouts.index[::-1]:
        if n_row > n_row_max: # if more seats than the maximum
            if (seat_layouts.loc[section, "n_rows"] <= n_row_section_min): # we don't want a single row in a section
                continue
            seat_layouts.loc[section, "n_rows"] -= 1 # subtract one row from this section 
            n_row = sum(seat_layouts["n_rows"]) # update n_row
            print(f"1 row subtracted from {section} class. There are now {seat_layouts.loc[section, 'n_rows']} rows in {section}, and {n_row} rows total.", end = "\n")
            if n_row_min <= n_row <= n_row_max: # break out of for loop, and thus while loop
                break
        
        elif n_row < n_row_min:
            if (seat_layouts.loc[section, "n_rows"] >= n_row_section_max) or (seat_layouts.loc[section, "n_rows"] == 0): # we don't want a bunch of rows in a section, and if there's 0 rows, that's for a reason
                continue
            seat_layouts.loc[section, "n_rows"] += 1 # add one row from this section 
            n_row = sum(seat_layouts["n_rows"]) # update n_row
            print(f"1 row added to {section} class. There are now {seat_layouts.loc[section, 'n_rows']} rows in {section}, and {n_row} rows total.", end = "\n")
            if n_row_min <= n_row <= n_row_max: # break out of for loop, and thus while loop
                break


##################################################

# FIGURE OUT THE ROWS
##################################################

# I will first just use ratios to figure out where everything goes, then I will scale to the plane's size
row_lines = DataFrame.from_dict(
    data = {
    "line"       : numpy.zeros(shape = 2 * n_row, dtype = "float64"), # eventually will contain pixel values of where the row_lines will god
    "type"       : ["",] * (2 * n_row), # what type of line is TO THE LEFT of the line; # "seat", "floor", "exit" (special type of floor), "os" [OFFSET] (special type of floor)
    "section"    : ["",] * (2 * n_row), # what section of the plane does this row belong to
    "row_number" : numpy.zeros(shape = 2 * n_row, dtype = "int64") # what is the row number of this row
    },
    orient = "columns")

i = 0 # indexer to fill row_lines
exit_row_number_value = 0
for section in seat_layouts.index:
    leg_room = seat_layouts.loc[section, "leg_room"]
    seat_depth = seat_layouts.loc[section, "seat_depth"]
    # fill each row with leg room and a seat
    for k in range(int(seat_layouts.loc[section, "n_rows"])):
        row_lines.loc[i]     = (leg_room,   "floor", section, int((i / 2) + 1))
        row_lines.loc[i + 1] = (seat_depth,  "seat", section, int((i / 2) + 1))
        i += 2
del i

# add the exits to make calculations easier
for i in range(n_exits):
    row_lines.loc[len(row_lines)] = (gateway_size, "exit", "exit", exit_row_number_value)
if not has_first_class: # add the small gate offset if there is no first class
    row_lines = concat((DataFrame(data = [[gate_offset, "os", "", -1]], columns = row_lines.columns), row_lines), axis = 0) # insert gate offset at the top of row_lines
    row_lines = reset_indicies(row_lines) # reset indicies
# turn into fractions
row_lines["line"] = row_lines["line"] / sum(row_lines["line"])
gateway_width = row_lines.loc[len(row_lines) - 1, "line"] # I will reuse this name later, but for now, it refers to the fraction that each exit takes up
# remove the exits so I can calculate where they are placed
row_lines = row_lines.drop(index = range(len(row_lines) - n_exits, len(row_lines)), axis = 0)

##################################################

# FIGURE OUT EXITS
##################################################

# regardless of number of exits, there will always be one where the plane connects with the gate
if has_first_class:
    # add row for front line of chasse, don't need if there isn't a first class, since the offset is the frontmost line
    row_lines = concat((DataFrame(data = [[0.0, "", "", exit_row_number_value]], columns = row_lines.columns), row_lines), axis = 0) # note "" value because there's cockpit to the left (nothing)
    row_lines = reset_indicies(row_lines)
    gate_index = (seat_layouts.loc["first", "n_rows"] * 2) + 1 # + 1 because of the front of chasse line
else: # no first class
    gate_index = 1 # accounting for the extra row for the gate offset
row_lines.loc[gate_index - 0.5] = (gateway_width,  "exit", "exit", exit_row_number_value)
row_lines = reset_indicies(row_lines)

# in addition to the exit at the front, there will be one in the back
if n_exits >= 2:
    row_lines.loc[len(row_lines)] = (gateway_width, "exit", "exit", exit_row_number_value)
    row_lines = reset_indicies(row_lines)
    
    # in addition to the two exits mentioned previously, one exit on the wing (a little before halfway)
    if n_exits >= 3:
        k = 0
        for i in range(len(row_lines["line"])):
            if sum(row_lines.loc[range(i + 1), "line"]) < 0.5: # i is the index right before the cumulative sum becomes greater than 0.50; that is, right before halfway, I want the i-value that when I add to the cumsum, the cumsum will cross half
                k = i
                continue
            else:
                break
        
        if row_lines.at[k, "type"] == "seat": # we want the exit to insert in front a floor, not a seat
            k -= 1 # we want the exit to change evenness if any of these conditions are true by pushing it forward
        row_lines.loc[k - 0.5] = (gateway_width, "exit", "exit", exit_row_number_value)
        row_lines = reset_indicies(row_lines)
        del k, i

# get cumulative sum of row_lines
row_lines["line"] = numpy.cumsum(a = row_lines["line"], axis = 0)
# convert to pixel values
# manipulate with wall width so the outlines won't overlap the plane walls
row_lines["line"] = (row_lines["line"] * (plane_length - (wall_width / 2))) + x0 + (wall_width / 2)
# shift so that "type" and "section" show the value TO THE LEFT (after) of the line
row_lines["type"] = list(row_lines["type"][1:len(row_lines)]) + [""]
row_lines["section"] = list(row_lines["section"][1:len(row_lines)]) + [""]
row_lines["row_number"] = list(row_lines["row_number"][1:len(row_lines)]) + [-1]


# determine passenger dimensions, redefine gateway_width
gate_index = row_lines.loc[row_lines["type"] == "exit"].index[0] # look for exits, take the index of the first exit
x0_os, x2_os = row_lines.at[gate_index, "line"], row_lines.at[gate_index + 1, "line"] # x-values for where the gate intersect the body of the plane, os stands for offset, since they are offset from x0 and x2
gateway_width = x2_os - x0_os  # size of stairs and walkway and main aisles
passenger_diameter = gateway_width / gateway_size # in pixels
passenger_radius = passenger_diameter / 2

##################################################

# CLEAR UP SEAT LAYOUTS
##################################################

# the sections where n_rows != 0
sections = seat_layouts.loc[seat_layouts["n_rows"] != 0].index


# make sure the seats are in alphabetical order from left to right
for section in sections:
    seat_layout_trimmed = "".join(seat_layouts.at[section, "seat_layout"].split())
    if list(seat_layout_trimmed) != sorted(seat_layout_trimmed):
        seat_layout_correct = []
        i = 0
        for character in seat_layouts.at[section, "seat_layout"]:
            if character == " ": # if the character is white space
                seat_layout_correct.append(" ")
            else: # list out characters in alphabetical order
                seat_layout_correct.append(ascii_uppercase[i])
                i += 1
        seat_layouts.at[section, "seat_layout"] = "".join(seat_layout_correct)
        del seat_layout_correct, i, character
del section, seat_layout_trimmed

# we assume that the section with the most seats per row with the most seats will be economy
# so, we will make this the case
if seat_layouts.sort_values(by = "n_seats_per_row", axis = 0, ascending = False).iloc[0]["n_seats_per_row"] != seat_layouts.at["economy", "n_seats_per_row"]:
    # determine the smallest ideal seat layout
    smallest_ideal_seat_layout = seat_layouts.loc[sections].sort_values(by = "n_seats_per_row", axis = 0, ascending = True).iloc[0]["seat_layout"]
    print(f"Changing seat layouts in the following classes: {list(seat_layouts.loc[seat_layouts['n_seats_per_row'] > seat_layouts.at['economy', 'n_seats_per_row']].index)}")
    # if the number of seats per row is greater than economy in any section, the seat_layout is replaced by the smallest ideal seat layout
    seat_layouts.loc[seat_layouts["n_seats_per_row"] > seat_layouts.at["economy", "n_seats_per_row"], "seat_layout"] = smallest_ideal_seat_layout
    del smallest_ideal_seat_layout
    
# each successive section should have greater than equal to number of seats per row than than the row before it
for i in range(1, len(sections)):
    # if this section has less seats per row than the section before it
    if seat_layouts.at[sections[i], "n_seats_per_row"] < seat_layouts.at[sections[i - 1], "n_seats_per_row"]:
        seat_layouts.at[sections[i - 1], "seat_layout"] = seat_layouts.at[sections[i], "seat_layout"] # set the seat layout of the previous row to the same as this one, so that the number of seats per row gets bigger each new section
        print(f"Seat layout of {sections[i - 1]} class has been altered.")

seat_layouts["n_seats_per_row"] = numpy.array(tuple(len("".join(row.split())) for row in seat_layouts["seat_layout"]), dtype = "int64")


# compare and see if seat_layouts or rows have changed
print("**********")
if len(seat_layouts_original.compare(seat_layouts[["seat_layout", "n_rows"]])) == 0: # seat_layouts didn't change
    print(seat_layouts.loc[sections, ["seat_layout", "n_rows"]], "No changes to number of rows per section or seat layout!", sep = "\n")
else: # something has changed
    print("\nOriginal sections:\n", seat_layouts_original.loc[sections, ["seat_layout", "n_rows"]], sep = "")
    print("\nNew sections:\n", seat_layouts.loc[sections, ["seat_layout", "n_rows"]], sep = "")
print("**********")
del seat_layouts_original

##################################################

# DETERMINE PLANE WIDTH BY USING ECONOMY SEATS
##################################################

# calculate plane_width in terms of passenger diameters, then multiply by passenger_diameter
# the economy seats will always be square
last_section_with_rows = sections[len(sections) - 1]
plane_width_diameters = (n_walkways * gateway_size) + (seat_layouts.loc[last_section_with_rows, "n_seats_per_row"] * seat_layouts.loc[last_section_with_rows, "seat_depth"])
plane_width = plane_width_diameters * passenger_diameter
del plane_width_diameters

##################################################

# DEFINE BASIC POINTS FOR PLANE
##################################################

# walls and points of airplane diagram
#                                                             ^
#                                                  x5         | wfhe
#                                                             v
#         (x0, y0)-----------------------x3-----x4-----------------(x1, y0)
#            |                                                        |
#            |                                                        |
# <--wfve--> |                                                        |
#            |                                                        |
#            |                                                        |
#         (x0, y1)-x0_os  x2 x2_os-------x3-----x4-----------------(x1, y1)
#                    |         |
#                    |         |                   x5
#                 (x8, y3)     |
#                   /     (x2_os,y2)
#                 /           /  
#               /            /  <---- (x_spawn, y_spawn)
#              x6-----------x7

# wall constants
# wall_fraction_from_(horizontal/vertical)_edge
wfhe = 4/10 # fraction of the screen height from the horizontal edge, MUST BE LESS THAN 1/2
canvas_height = plane_width / (1 - (2 * wfhe)) # calculate canvas height
plane_width_halved = (1/2 - wfhe) * canvas_height # plane width divided by 2...duh
tail_length = wfve_tail * canvas_width # tail length

# define points
x_mid, y_mid = canvas_width / 2, canvas_height / 2
y0, y1 = wfhe * canvas_height, (1 - wfhe) * canvas_height
y0_inner, y1_inner = y0 + (wall_width), y1 - (wall_width)
x3 = x_mid - ((1/8) * canvas_width) # x-coordinate of the shoulder of wings
x4 = x_mid + ((1/32) * canvas_width) # x-coordinate of the armpit of wings
x5 = x_mid + ((1/10) * canvas_width) # x-coordinate of the tip of wings

##################################################

# FIGURE OUT THE COLUMNS
##################################################

# width of plane where I won't overlap the walls
plane_width_fillable = y1_inner - y0_inner

# initialize this dictionary where the keys are the section names, the values will be the pixels where lines are placed
col_lines = dict(zip(sections,
                     map(
                         lambda n_seats: DataFrame.from_dict(data = {
                             "line"    : numpy.concatenate(([y0_inner], numpy.zeros(shape = n_seats + n_walkways, dtype = "float64")), axis = None),
                             "type"    : ["",] * (1 + n_seats + n_walkways) # what type of line is ABOVE the line; # "seat", "floor"
                             },
                                                             orient = "columns"),
                         tuple(seat_layouts.loc[sections, "n_seats_per_row"])
                         )
                     ))

# calculate column lines for each section
for section in tuple(col_lines.keys())[::-1]:
    # some variables
    seat_layout = seat_layouts.loc[section, "seat_layout"][::-1] # because seat layouts are meant to be laid out left-to-right
    seat_width = (plane_width_fillable - (n_walkways * gateway_width)) / seat_layouts.loc[section, "n_seats_per_row"]
    # fill the col_lines section
    for i in range(1, len(col_lines[section])): # 0th value is already filled with starting position
        if seat_layout[i - 1] == " ": # if this is a walkway, denoted by a space on seat_layout
            col_lines[section].at[i, "line"] = col_lines[section].at[i - 1, "line"] + gateway_width
            col_lines[section].at[i, "type"] = "floor"
        else: # if this is not a walkway -- if this IS a seat
            col_lines[section].at[i, "line"] = col_lines[section].at[i - 1, "line"] + seat_width
            col_lines[section].at[i, "type"] = "seat"
    # shift so that "type" shows the value BELOW the line
    col_lines[section]["type"] = list(col_lines[section]["type"][1:len(col_lines[section])]) + [""]
    
##################################################


# ~~~~ Building the Tkinter Window and Canvas ~~~~

# CONSTRUCT TKINTER WINDOW
##################################################

# create tkinter root window
root = tkinter.Tk()
root.title("Boarding an Airplane")
mn = 13 # magic number to add to the window_width and widow_height to account for scroll bar
root.geometry(f"{window_width + mn}x{window_height + mn}+0+0") # widthxheight+xdistancefromleftcorner+ydistancefromleftcorner
root.resizable(width = False, height = False) # make the window unresizable

# create the base frame
base_frame = tkinter.Frame(root) # create frame
base_frame.pack(fill = "both", expand = True) # pack onto screen

# create the base canvas
base_canvas = tkinter.Canvas(
    master = base_frame,
    bg = canvas_background_color,
    scrollregion = f"{x_mid - (window_width / 2)} {y_mid - (window_height / 2)} {x_mid + (window_width / 2)} {y_mid + (window_height / 2)}",
    bd = 0, relief = "raised", highlightthickness = 0) # remove border

# add scroll bars to the base canvas
scrollbar_v = ttk.Scrollbar( # vertical scrollbar
    base_frame,
    orient = "vertical",
    command = base_canvas.yview)
scrollbar_h = ttk.Scrollbar( # horizontal scrollbar
    base_frame,
    orient = "horizontal",
    command = base_canvas.xview)

# pack scrollbars, then the canvas after the scrollbars so the scrollbars align and fill correctly (https://stackoverflow.com/questions/59642378/tkinter-scrollbars-not-filling-or-aligning-correctly)
scrollbar_v.grid(row = 0, column = 1, sticky = "ns")
scrollbar_h.grid(row = 1, column = 0, sticky = "ew")
base_canvas.grid(row = 0, column = 0, sticky = "ewns")
base_frame.columnconfigure(0, weight = 1) # properly resizes the interface
base_frame.rowconfigure(0, weight = 1) # properly resizes the interface
# Alternative Method using .pack(), though it is not as scalable with more complex interfaces
# scrollbar_v.pack(side = "right", fill = "y") # pack to right side of screen
# scrollbar_h.pack(side = "bottom", fill = "x") # pack to bottom of screen
# base_canvas.pack(side = "left", fill = "both", expand = True)

# configure the base canvas to allow for scrolling
base_canvas.configure(
    xscrollcommand = scrollbar_h.set,
    yscrollcommand = scrollbar_v.set)
base_canvas.bind("<Configure>", lambda event: base_canvas.configure(scrollregion = base_canvas.bbox("all")))

# create another frame on top of the base canvas
frame = tkinter.Frame(base_canvas)

# add the subframe to a window in the canvas
base_canvas.create_window((0, 0), window = frame, anchor = "nw")
# base_canvas.create_window((x_mid, y_mid), window = frame, anchor = "center")

# create canvas to build the plane on
canvas = tkinter.Canvas(
    master = frame,
    width = canvas_width, height = canvas_height,
    bg = canvas_background_color,
    bd = 0, relief = "raised", highlightthickness = 0)
##################################################

# BUILD THE PLANE
##################################################

# body of plane
canvas.create_polygon(
    straight_lines(((x0, y0), (x3, y0), (x5, 0), (x4, y0), (x1, y0))), # upper wall and wing
    (x1 + ((5/6) * (wfve * canvas_width)), y0 + ((1/2) * plane_width_halved)), (canvas_width, y_mid), (x1 + ((5/6) * (wfve * canvas_width)), y1 - ((1/2) * plane_width_halved)), # tail
    straight_lines(((x1, y1), (x4, y1), (x5, canvas_height), (x3, y1), (x0, y1))), # lower wall and wing
    (x0 - ((3/4) * (wfve * canvas_width)), y1 - ((1/4) * plane_width_halved)), (0, y_mid), (x0 - ((3/4) * (wfve * canvas_width)), y0 + ((1/4) * plane_width_halved)), # nose
    outline = wall_color, fill = plane_color, width = wall_width, smooth = True, tags = "body removable") # options

# (optional) lines separating the wings and body of the plane
if display_line_between_wings_and_body:
    canvas.create_line( # cockpit
        (x3, y0), (x4, y0),
        fill = wall_color, width = wall_width, tags = "wingwall") # upper
    canvas.create_line( # tail
        (x3, y1), (x4, y1),
        fill = wall_color, width = wall_width, tags = "wingwall") # lower

# impression of top tail wing
canvas.create_oval(
    (x1 + ((3/16) * tail_length), y_mid - ((5/64) * tail_length)), # top left of oval
    (x1 + ((13/16) * tail_length), y_mid + ((5/64) * tail_length)), # bottom right of oval
    outline = wall_color, fill = top_tail_wing_color, width = wall_width, tags = "toptailwing") # options

# wall to cockpit and tail, where passengers cannot go
for x in (x0, x1): # cockpit, tail
    canvas.create_line(
        (x, y0), (x, y1),
        fill = wall_color, width = wall_width, dash = dash_pattern, tags = "ctwall") # cockpit
del x

# update canvas
canvas.pack()

##################################################


# ~~~~~~~~ Build the Gate and Interior ~~~~~~~~~~~

# CONSTANTS
##################################################

# # define points to create gate
# see x0_os, x2_os defined in the FIGURE OUT EXITS section of "Seats"
x2 = x0 + gateway_width
x7 = x2_os # x2_os - gateway_width
x6 = x7 - (6 * gateway_width)
x8 = x0_os # x0_os - ((x7 - x6) / 4)
x9 = wall_width / 2
y2 = (1 - ((1/3) * wfhe)) * canvas_height
y3 = y2 - ((3/4) * passenger_diameter)

# define points for interior of plane
x0_inner = row_lines.at[0, "line"] + (wall_width / 2)
x1_inner = row_lines.at[len(row_lines) - 1, "line"] - (wall_width / 2)

##################################################

# ADD GATE AND FLOOR
##################################################

gate_and_walkway_vertices = ((x2_os, y1_inner), (x2_os, y2), (x7, canvas_height), (x9, canvas_height), (x9, y3), (x8, y3), (x0_os, y1_inner))
# gate and walkway to plane
canvas.create_polygon(gate_and_walkway_vertices, fill = stairs_color, outline = "", width = 0, smooth = False, tags = "floor removable")
# walls for gate and walkway to plane
canvas.create_line(gate_and_walkway_vertices, fill = stairs_outline_color, width = wall_width, smooth = False, tags = "wall")

# slightly adjust floor frontline when there is no first class
x0_inner_temp  = x0_os if (not has_first_class) else x0_inner
# create rectange for plane floor
canvas.create_rectangle(
    (x0_inner_temp, y0_inner), (x1_inner, y1_inner),
    fill = stairs_color, outline = "", width = 0, tags = "floor removable")
# add floor borders
canvas.create_line(
    (x0_os, y1_inner), (x0_inner_temp, y1_inner), (x0_inner_temp, y0_inner), (x1_inner, y0_inner), (x1_inner, y1_inner), (x2_os, y1_inner),
    fill = stairs_outline_color, width = wall_width, tags = "wall")
del x0_inner_temp

##################################################

# ADD SEATS AND AISLES
##################################################

# get indicies for when new sections begin (adding the first line)
section_indicies = [0, ] + [i for i in range(1, len(row_lines)) if row_lines.loc[i, "section"] != row_lines.loc[i - 1, "section"]]

# loop through each section and draw to canvas
for i in range(len(section_indicies) - 1): # the last line will always be blank, so we can ignore it
    section = row_lines.at[section_indicies[i], "section"]
    
    if section != "exit": # this is a normal aisle/seating section
        
        # figure out where walkway is
        walkway_indicies = list(col_lines[section].loc[col_lines[section]["type"] == "floor"].index)
        walkway_indicies = sorted(walkway_indicies + list([k + 1 for k in walkway_indicies]) + [0, len(col_lines[section]) - 1])
        walkway_lines = list(col_lines[section].loc[walkway_indicies, "line"])
        
        # iterate through each row
        for k in range(section_indicies[i] + 1, section_indicies[i + 1] + 1, 2): # + 1 because we start on a seat
                    
            # create seat cushions and arm/backrests
            for l in range(0, len(walkway_lines) - 1, 2): # draw the front edge of leg room
                # create rectangle for seat cushions
                canvas.create_rectangle(
                    (row_lines.at[k, "line"], walkway_lines[l]), (row_lines.at[k + 1, "line"], walkway_lines[l + 1]),
                    fill = seat_color, outline = "", width = 0, tags = "seat removable")
                
                # create arm/backrests algorithmically
                x_seatfront = row_lines.at[k, "line"]
                x_seatback = row_lines.at[k + 1, "line"] - (wall_width / 2)
                armrests = [(x_seatfront, walkway_lines[l]), (x_seatback, walkway_lines[l])]
                for y in list(col_lines[section].loc[range(walkway_indicies[l] + 1, walkway_indicies[l + 1]), "line"]):
                    armrests += [(x_seatback, y), (x_seatfront, y), (x_seatback, y)]
                armrests += [(x_seatback, walkway_lines[l + 1]), (x_seatfront, walkway_lines[l + 1])]
                
                # draw line for arm/backrests
                canvas.create_line(armrests, fill = seat_outline_color, width = wall_width, tags = "seat_outline")
                
                del x_seatfront, x_seatback, armrests
                 
            # draw floor outline behind seat
            x = row_lines.at[k + 1, "line"] + (wall_width / 2)
            for l in range(0, len(walkway_lines) - 1, 2): # draw the front edge of leg room
                canvas.create_line(
                    (x, walkway_lines[l]), (x, walkway_lines[l + 1]),
                    fill = stairs_outline_color, width = wall_width, tags = "floor_outline")
            del x
                        
        del walkway_indicies, walkway_lines, section
        
##################################################

# ADD EXIT DOORS
##################################################

if display_exits:
    # get indicies for the front end of the exits
    exit_indicies = row_lines.loc[row_lines["type"] == "exit"].index

    for i in list(exit_indicies):
        for y in (y0_inner, y1_inner): # top and bottom walls, subtract wall_width from y1, since line width is added downwards
            canvas.create_line(
                (row_lines.at[i, "line"], y), (row_lines.at[i + 1, "line"], y),
                fill = exit_color, width = wall_width * 2, tags = "exit_door removable")
        del y
    del i

##################################################

# SORT OUT LAYERINGS
##################################################

# raise floor over body, floor outlines over the floor
canvas.tag_raise("floor", "body")
canvas.tag_raise("floor_outline", "floor")
canvas.tag_raise("wall", "floor_outline")

# raise seats over floor, seat outlines over the seats
canvas.tag_raise("seat", "wall")
canvas.tag_raise("seat_outline", "seat")

# raise exits over everything
canvas.tag_raise("exit_door")

canvas.pack()

collidable_tags = sorted(canvas.find_withtag("wall") + canvas.find_withtag("seat_outline"))
removable_tags = canvas.find_withtag("removable") # object IDs that I can ignore when collision-checking

##################################################


# ~~~~~~~~~~~~~~~~~ Passengers ~~~~~~~~~~~~~~~~~~~

# DEFINE VARIABLES
##################################################

# define variables not yet defined
step = passenger_radius / 2 # step size of passengers (in pixels)
bounding_box_margin = - passenger_outline_width / 10

##################################################

# FIGURE OUT COORDINATES OF SEATS
##################################################

seat_coordinate_method = 2
# methods:
#    1 = midpoint
#    2 = some distance from the back of the seat

# to be used with map function
def get_seat_coordinates(section):
    seat_column_names = [*"".join(seat_layouts.at[section, "seat_layout"].split())] # column names (A, B, C, D, etc.) of resulting data frame
    seat_row_names = sorted(list(set(row_lines.loc[row_lines["section"] == section, "row_number"])))

    # figure out row midpoints
    section_indicies_rows = row_lines.index[row_lines["section"] == section] + 1 # + 1 because i want the seat, not floor, midpoints
    row_midpoints = [None, ] * (len(section_indicies_rows) // 2)
    j = 0 # indexer to fill row_midpoints
    if seat_coordinate_method == 1:
        for i in range(0, len(section_indicies_rows) - 1, 2):
            row_midpoints[j] = midpoint(row_lines.at[section_indicies_rows[i], "line"], row_lines.at[section_indicies_rows[i + 1], "line"])
            j += 1
    elif seat_coordinate_method == 2:
        for i in range(1, len(section_indicies_rows), 2):
            row_midpoints[j] = row_lines.at[section_indicies_rows[i], "line"] - (passenger_radius + passenger_outline_width)
            j += 1
    del i, j
    row_midpoints = list((row_midpoint - wall_width for row_midpoint in row_midpoints))
    
    # figure out column midpoints
    col_midpoints = [None, ] * len(seat_column_names)
    j = len(col_midpoints) - 1 # indexer to fill col_midpoints
    for i in range(len(col_lines[section]) - 1):
        if col_lines[section].loc[i, "type"] == "floor": # if this is a walkway
            continue
        col_midpoints[j] = midpoint(col_lines[section].at[i, "line"], col_lines[section].at[i + 1, "line"])
        j -= 1
    del i, j
    
    # combine row and column midpoints
    seat_coordinates_section_matrix = numpy.reshape(a = list(product(row_midpoints, col_midpoints)), newshape = (len(row_midpoints), len(col_midpoints), 2))
    seat_coordinates_section = DataFrame.from_dict(data = dict(zip(seat_column_names, (tuple((0, 0) for i in range(seat_coordinates_section_matrix.shape[0])), ) * seat_coordinates_section_matrix.shape[1])), # create empty 3d array
                                                   orient = "columns")
    seat_coordinates_section.index = seat_row_names # set row names
    
    # fill seat_coordinates_section
    for i in range(len(seat_row_names)): # row
        for j in range(len(seat_column_names)): # column
            seat_coordinates_section.at[seat_row_names[i], seat_column_names[j]] = tuple(seat_coordinates_section_matrix[i, j, :])
    del i, j, seat_coordinates_section_matrix
    
    return(seat_coordinates_section)

seat_coordinates = dict(zip(sections, map(get_seat_coordinates, sections)))

del seat_coordinate_method, get_seat_coordinates
##################################################

# OTHER HELPER FUNCTIONS
##################################################

# figure out which section a passenger is in
section_row_numbers = numpy.cumsum(a = seat_layouts.loc[sections, "n_rows"], axis = 0)
def which_section(row_number):
    for i in range(len(sections)):
        if row_number <= section_row_numbers.at[sections[i]]:
            return(sections[i])

##################################################
        
# SEAT LIST
##################################################

seat_list = map(lambda section:
                map(lambda row_seat:
                    str(row_seat[0]) + row_seat[1],
                    product(seat_coordinates[section].index, seat_coordinates[section].columns)),
                sections)
seat_list = list(chain.from_iterable(seat_list)) # flatten seat_list

##################################################

# KEY TARGET POINTS
##################################################

# where each section starts
x_walkways = dict(zip(sections, [0.0, ] * len(sections)))
y_walkways = dict(zip(sections, [[0.0, ] * n_walkways, ] * len(sections)))

for section in sections:
    
    # x coordinates
    x_walkways[section] = midpoint(row_lines.loc[row_lines["section"] == section].iat[0, 0], row_lines.loc[row_lines["section"] == section].iat[1, 0])
    
    # y coordinates
    y_walkways_section = [0.0, ] * n_walkways
    for i, ywi in enumerate(col_lines[section].loc[col_lines[section]["type"] == "floor"].index[::-1]): # ywi: y_walkway_index, reverse because A-F starts at bottom side
        y_walkways_section[i] = midpoint(col_lines[section].at[ywi, "line"], col_lines[section].at[ywi + 1, "line"])
    y_walkways[section] = y_walkways_section
    del y_walkways_section
    
del section

##################################################

# SPAWNING MECHANICS
##################################################

# possible spawning locations
x_spawn = midpoint(x0_os, x2_os)
spawning_loc_step = 2 * passenger_diameter
y_spawn = y3 + (spawning_loc_step / 2)
x_spawnpoints = numpy.arange(start = x_spawn - (((x_spawn - (x9 + (spawning_loc_step / 2))) // spawning_loc_step) * spawning_loc_step),
                             stop = x_spawn + (spawning_loc_step / 2),
                             step = spawning_loc_step)[::-1]
y_spawnpoints = numpy.arange(start = y_spawn,
                             stop = y_spawn + ((((canvas_height - (spawning_loc_step / 2)) - y_spawn) // spawning_loc_step) * spawning_loc_step) + (spawning_loc_step / 2),
                             step = spawning_loc_step)
nrow_spawnpoints = len(y_spawnpoints) # number of rows

# convert into matrix
spawning_locs = numpy.zeros(shape = (len(x_spawnpoints), len(y_spawnpoints), 2))
for i, x_spawnpoint in enumerate(x_spawnpoints):
    for j, y_spawnpoint in enumerate(y_spawnpoints):
        spawning_locs[i, j, :] = (x_spawnpoint, y_spawnpoint)
del x_spawnpoints, y_spawnpoints, i, j, x_spawnpoint, y_spawnpoint, spawning_loc_step

# make it snake formation by reversing every other column
for i in range(1, len(spawning_locs), 2):
    spawning_locs[i] = spawning_locs[i][::-1]
    
# flatten
spawning_locs = tuple(map(lambda coords: tuple(coords), chain.from_iterable(spawning_locs)))

# for debugging, check spawning locations
# for coords in spawning_locs:
#     plot_point(canvas, self.coords)

##################################################
# DEFINE "passenger" CLASS
##################################################
# ex. # Phil = passenger(zone = 3, seat = "27C", spawn = (0, 0))

class passenger:    
    
    # CREATE INSTANCE OF PASSENGER
    ##############################################
    def __init__(self, zone = 0, seat = "", spawn = (x_spawn, y_spawn)):
                
        # instance variables
        self.zone = int(zone) # needs to be a number, not letter
        self.seat = seat
        self.coords = list(spawn) # coordinates of passenger
        self.row = int(seat[:seat.find("[A-Z]")])
        self.col = seat[seat.find("[A-Z]"):] # get seat column value from the seat
        self.section = which_section(row_number = self.row)
        self.seat_coords = seat_coordinates[self.section].at[self.row, self.col] # coordinates of seat
        
        # instance variables
        self.spawned = False
        self.reached_current_target = False # has passenger reached current target
        self.tpi = 0 # target point index
        self.in_seat = False # has the passenger reached their final target (their seat)
        
    ##############################################
       
    # COLLISION FUNCTIONS
    ##############################################
    
    # calculate bounding box
    def get_bounding_box(self, x_os = 0, y_os = 0, center_points_provided = ()): # x_os and y_os are x and y offsets, respectively; center points provided if we want a bounding box from the center points
        # bounding_box = [x_topleft, y_topleft, x_bottomright, y_bottomright]
        if len(center_points_provided) == 0: # the default, no center points provided
            bounding_box = canvas.coords(self.agent) # obtains bounding box (bb) of agent
        else:
            # center_points_provided = (x_center, y_center)
            center_points_provided = numpy.array(center_points_provided)
            bounding_box = list(center_points_provided - passenger_radius) + list(center_points_provided + passenger_radius)
        del center_points_provided
        
        # note that as the bouncing_box_margin is increased, it become harder to fit through things
        global bounding_box_margin
        bounding_box[0] -= bounding_box_margin # left side
        bounding_box[1] -= bounding_box_margin # top side
        bounding_box[2] += bounding_box_margin # right side
        bounding_box[3] += bounding_box_margin # bottom side
        
        # alter according to x and y offsets
        bounding_box[0], bounding_box[2] = bounding_box[0] + x_os, bounding_box[2] + x_os # x values
        bounding_box[1], bounding_box[3] = bounding_box[1] + y_os, bounding_box[3] + y_os # y values
        
        # print(bounding_box) # for debugging
        return(bounding_box)
    
        
    # find overlapping objects
    def collision_detected(self, bounding_box):
        overlapping_tags = list((i for i in canvas.find_overlapping(*bounding_box) if (i not in removable_tags)))
        if hasattr(self, "agent"): # if self.agent exists
            if self.agent in overlapping_tags: # remove this passenger from overlap
                overlapping_tags.remove(self.agent) 
        # print(overlapping_tags) # for debugging
        if any(((i in collidable_tags + list(canvas.find_withtag("passenger"))) for i in overlapping_tags)):
            # print(True) # for debugging
            return(True) # collision was detected
        else:
            # print("") # for debugging
            return(False) # no collision was detected
        
    ##############################################
    
    # MOTION FUNCTIONS
    ##############################################
    # if no collision is detected, move the inputted distance (d = distance)
    
    # for motion in y direction
    # up = -d, down = +d
    def move_v(self, d):
        d = (d / abs(d)) * step if abs(d) > step else d # if a large distance is inputted, only travel the maximum amount the passenger can
        if not self.collision_detected(bounding_box = self.get_bounding_box(y_os = d)):
            canvas.move(self.agent, 0, d)
            self.coords[1] += d # update coordinates
            root.update()
        
    # for motion in x direction
    # left = -d, right = +d
    def move_h(self, d):
        d = (d / abs(d)) * step if abs(d) > step else d # if a large distance is inputted, only travel the maximum amount the passenger can
        if not self.collision_detected(bounding_box = self.get_bounding_box(x_os = d)):
            canvas.move(self.agent, d, 0)
            self.coords[0] += d # update coordinates
            root.update()
    
    ##############################################
            
    # SPAWNING
    ##############################################
    
    def spawn(self):
        global spawnpoint_index
        if spawnpoint_index >= len(spawning_locs) - 1 and self.collision_detected(bounding_box = self.get_bounding_box(center_points_provided = spawning_locs[spawnpoint_index])): # if final spawning location is occupied
            self.coords = list(spawning_locs[spawnpoint_index])
            return(None) # wait until next iteration to try to spawn
        
        else:
            # determine spawning location
            while spawnpoint_index < len(spawning_locs) - 1 and self.collision_detected(bounding_box = self.get_bounding_box(center_points_provided = self.coords)): # if spawning location is occupied
                spawnpoint_index += 1
                self.coords = list(spawning_locs[spawnpoint_index]) # update self.coords
        
            # create the passenger
            self.agent = canvas.create_oval(
                tuple(numpy.array(self.coords) - passenger_radius), tuple(numpy.array(self.coords) + passenger_radius),
                fill = sample(passenger_color, 1), outline = passenger_outline_color, width = passenger_outline_width, tags = "passenger") # options
            canvas.tag_raise(self.agent) # layer this agent over the stairs
            canvas.pack()
            
            # update self.spawned to indicate that the passenger has spawned
            self.spawned = True
            
            # determine how passenger will proceed
            self.target_points = self.determine_target_points()
            
            # self.show_path_to_seat() # for debugging, show path to seat
            
    ##############################################
    
    # NAVIGATION METHODS
    ##############################################
    
    # determine list of points the passenger needs to travel to to get to seat
    def determine_target_points(self):
        # create list of points in the line  to get on plane
        target_points = sorted(list(range(0, spawnpoint_index, nrow_spawnpoints)) + list(range(nrow_spawnpoints - 1, spawnpoint_index, nrow_spawnpoints)))
        target_points = list((tuple(spawning_locs[i]) for i in target_points))[::-1]
        
        # add point for first point ON plane
        if n_walkways == 1:
            walkway_index = 0
        else: # if n_walkways == 2
            section_seats = "".join(seat_layouts.at[self.section, "seat_layout"].split())
            seat_proportion = (section_seats.index(self.col) + 1) / len(section_seats)
            walkway_index = int(round(seat_proportion))
            del section_seats, seat_proportion
            
        if self.section != "first" and has_first_class:
            walkway_section_index = 1
        else: # self.section == "first" or not has_first_class
            walkway_section_index = 0

        target_points.append((spawning_locs[0][0], y_walkways[sections[walkway_section_index]][walkway_index])) # add plane entryway point
        if len(target_points) > 1:
            del target_points[len(target_points) - 2] # remove redundant point
            
        
        # maneuvre passenger to their row
        if not has_first_class or (self.section != "first" and has_first_class):
            while walkway_section_index < list(sections).index(self.section):
                walkway_section_index += 1
                target_points.append((x_walkways[sections[walkway_section_index]], y_walkways[sections[walkway_section_index - 1]][walkway_index])) # go to the correct x point of next section
                target_points.append((x_walkways[sections[walkway_section_index]], y_walkways[sections[walkway_section_index]][walkway_index])) # adjust walkway y coordinate   
        row_lines_subset = tuple(row_lines.loc[row_lines["row_number"] == self.row]["line"])
        row_x_coord = midpoint(row_lines_subset[0], row_lines_subset[1])
        target_points.append((row_x_coord, y_walkways[sections[walkway_section_index]][walkway_index]))
        del row_lines_subset, walkway_section_index, walkway_index
        
        # manuevre passenger to their seat
        target_points.append((row_x_coord, self.seat_coords[1]))
        del row_x_coord
        target_points.append(tuple(self.seat_coords))

        return(tuple(target_points))
    
    # figure out which way to move
    def move_to_target(self, target):

        distance = [target[0] - self.coords[0], target[1] - self.coords[1]]

        if abs(distance[1]) >= abs(distance[0]): # if the y distance is farther than x distance
            y_o = self.coords[1] # initial y value
            self.move_v(d = distance[1])
            if y_o == self.coords[1]: # if the passenger didn't move in the y-direction because collision detected
                self.move_h(d = distance[0]) # then move in the x-direction
            del y_o
            
        elif abs(distance[1]) < abs(distance[0]): # if the x distance is farther than y distance
            x_o = self.coords[0] # initial x value
            self.move_h(d = distance[0])
            if x_o == self.coords[0]: # if the passenger didn't move in the x-direction because collision detected
                self.move_v(d = distance[1]) # then move in the y-direction
            del x_o
                            
        # update x and y distances
        distance = [target[0] - self.coords[0], target[1] - self.coords[1]]
        
        if abs(distance[0]) == 0 and abs(distance[1]) == 0:
            self.reached_current_target = True # if the passenger has reached target, update variable
        else:
            self.reached_current_target = False
        
        del distance
        
    ##############################################
      
    # MAIN METHOD
    ##############################################
    
    # the passenger will do some action
    def move(self):
        
        # spawning mechanics
        if not self.spawned:
            self.spawn()
            # self.show_bounding_box() # for debugging, to test bounding box
            # plot_point(canvas, self.seat_coords) # for debugging, plot where seat is located
            return(None)
        
        
        # if the passenger has reached their seat, remain static
        if self.in_seat:
            return(None)
        
        # if the passenger is still working towards their seat
        else:
            # if reached current target
            if self.reached_current_target:
                if self.tpi < len(self.target_points) - 1: # if the passenger is yet to reach his/her seat
                    self.tpi += 1 # update target point index
                    self.reached_current_target = False # reset whether passenger has reached current target
                    self.move_to_target(target = self.target_points[self.tpi]) # begin moving right away
                else: # once the passenger has reached their final target, their seat
                    self.in_seat = True
                return(None)
                
            # if passenger is yet to reach current target
            else:
                self.move_to_target(target = self.target_points[self.tpi])
                return(None)
            
    ##############################################
    
    # DEBUGGING
    ##############################################
    
    # for debugging, show the bounding box
    def show_bounding_box(self):
        canvas.create_rectangle(self.get_bounding_box(), fill = "red", outline = "", width = 0)
        canvas.tag_raise(self.agent)
    
    # for debugging, show path to seat
    def show_path_to_seat(self):
        canvas.create_line(self.target_points, fill = "red", width = 3)
    
    ##############################################
  
##################################################


# ~~~~~~~~~~~~~~~ Load Passengers ~~~~~~~~~~~~~~~~

# KILL SWITCH
##################################################

def kill(event):
    root.destroy()

root.bind("<Escape>", lambda event: kill(event))

##################################################

# SPAWN THE PASSENGERS
##################################################

def board(passengers):
    while not all(map(lambda passenger: passenger.in_seat, passengers)):
        for passenger in passengers:
            passenger.move()
        # sleep(ts)

# BOARD BY SECTION
# section_seat_numbers = numpy.cumsum(a = seat_layouts.loc[sections, "n_rows"] * seat_layouts.loc[sections, "n_seats_per_row"], axis = 0)
# zone_indicies = sorted([0, int(midpoint(section_seat_numbers[-2], section_seat_numbers[-1]))] + list(section_seat_numbers))

# BOARD BY GROUPS OF 20
zone_indicies = list(range(0, len(seat_list), 20)) + [len(seat_list), ]


for i in range(1, len(zone_indicies)):
    # for plotting passengers on the grid
    spawnpoint_index = 0
    print(f"\n**********\nNow boarding Zone {i}.\n**********\n", sep = "", end = "")
    board(passengers = list(map(lambda seat: passenger(zone = i, seat = seat, spawn = spawning_locs[spawnpoint_index]), seat_list[zone_indicies[i - 1]:zone_indicies[i]])))

print("Ready for takeoff!")

# SPAWN PASSENGERS ONE AT A TIME, CONTROL WITH KEYBOARD TOUCHES
# passengers = []
# def spawn_passenger(event):
#     passengers.append(passenger(zone = 1, seat = seat_list.pop(randint(0, len(seat_list) - 1)), spawn = spawning_locs[spawnpoint_index]))
# 
# def next_frame(event):
#     for passenger in passengers:
#         passenger.move()
#     # sleep(ts)
# 
# root.bind("<a>", spawn_passenger)
# root.bind("<space>", next_frame)

##################################################
