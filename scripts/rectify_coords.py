from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
import math as maths
import numpy as np
import json
import os

save_dir = "coordinates"
os.makedirs(save_dir, exist_ok=True)


with open((os.path.join(save_dir, "savedata.json")), "r") as json_File :
    sample_load_file = json.load(json_File)

NUM_LEDS = np.size(sample_load_file, 0)

coords = sample_load_file

# what percentage of the lights do we think are likely correct?
correct_percent = 0.5

# average distance in a ball
circ_avg = 0.75

# pythagoras distance in any dimension
def dist(a,b):
    #assumes a and b are lists of the same length
    total = 0
    for i,j in zip(a,b):
        total += (i-j)**2
    return total**0.5

# find gap distances between all adjacent LEDs
gaps = []
scan = 0
for i in range(num_leds):
    gaps.append(dist(coords[scan],coords[scan+1]))

gaps_sorted = [i for i in gaps]
gaps_sorted.sort()

#  find the average of the bottom percent we think are correct
scan = 0
average_dist = 0
while scan < len(gaps_sorted)*correct_percent:
    average_dist += gaps_sorted[scan]
    scan += 1
average_dist /= scan
print(average_dist)
# scale average to match radius sphere
max_dist = average_dist/circ_avg

# find all the gaps below the max_distance
# 1 means needs fixing; 0 means no need to fix
track = []
for i in gaps:
    if i < max_dist:
        track.append(0)
    else:
        track.append(1)

# NOW REMOVE SINGLE OK GAPS
scan = 1
while scan < len(track)-1:
    if track[scan-1] + track[scan+1] == 2:
        track[scan] = 1
    scan += 1

# which LEDs are fine?
correct_LEDS = []
# start and end don't have a pair
correct_LEDS.append(track[0])
scan = 0
while scan < len(track)-1:
    correct_LEDS.append(track[scan]*track[scan+1])
    scan += 1
correct_LEDS.append(track[-1])

# NOW WE FIX

next_good = 0
# check if the starting LEDS are wrong:
if correct_LEDS[0] == 1:
    while correct_LEDS[next_good] == 1:
        next_good += 1
    scan = 0
    while scan < next_good:
        coords[scan] = coords[next_good]
        scan += 1

# use finished as an escape variable
finished = False
while not finished:
    try:
        # move next good to end of current good run
        while correct_LEDS[next_good] == 0:
            next_good += 1
        # save that as the last good
        previous_good = next_good-1
        # move up to next working ont
        while correct_LEDS[next_good] == 1:
            next_good += 1
    except:
        # this fails safe when we reach the end of the wire
        finished = True

    if finished:
        # check if we have a loose end of wrong LEDs make them all the same as the previous correct one
        if correct_LEDS[-1] == 1:
            # find the last one which was correct
            last_good = len(coords)-1
            while correct_LEDS[last_good] == 1:
                last_good -= 1
            # make the rest the same as that
            scan = last_good + 1
            while scan < len(coords):
                coords[scan] = coords[last_good]
                scan += 1
    else:
        # work out the difference vector
        differs = [j-i for i,j in zip(coords[previous_good], coords[next_good])]
        # split scan into scan and step which makes scaling the difference vector easier
        scan = previous_good
        step = 1
        while scan + step != next_good:
            coords[scan+step] = [int(i+j) for i,j in zip(coords[previous_good],[k*step/(next_good-previous_good) for k in differs])]
            step += 1

# Now need to convert to GIFT