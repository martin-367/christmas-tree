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


# find gaps between adjacent LEDs
gaps = []

for i in range(NUM_LEDS - 1):
    deltaX = coords[i+1][0] - coords[i][0]
    deltaY = coords[i+1][1] - coords[i][1]
    distance = maths.sqrt(deltaX**2 + deltaY**2)
    distance = maths.sqrt(deltaX**2 + deltaY**2)
    distance = maths.sqrt(deltaX**2 + deltaY**2)
    distance = maths.sqrt(deltaX**2 + deltaY**2)
    gaps.append(distance)
    average_gap = sum(gaps) / len(gaps)
    gaps_sorted = sorted(gaps)
average_dist = 0
loop_bound = int(len(gaps_sorted) * correct_percent)
for i in range(loop_bound):
    average_dist += gaps_sorted[i]

average_dist /= loop_bound

# scale average to match radius sphere
max_dist = average_dist/0.75

# find all the gaps below the max_distance
# 1 means needs fixing; 0 means no need to fix
track = []
for i in gaps:
    if i < max_dist:
        track.append(0)
    else:
        track.append(1)
# NOW REMOVE SINGLE OK GAPS

for i in range(1, NUM_LEDS - 2):
    if track[i-1] + track[i+1] == 2: # both sides are bad, although middle falsely appears good as is close enough to neighbours
        track[i] = 1


# which LEDs are fine?
correct_LEDS = []

correct_LEDS.append(track[0])
for i in range(NUM_LEDS - 2):
    correct_LEDS.append(track[i] * track[i + 1]) # both sides are bad, so this one is bad
correct_LEDS.append(track[-1])


# NOW WE FIX

x_coords = [c[0] for c in coords]
y_coords = [c[1] for c in coords]


plt.figure(figsize=(8, 8))
# Assign color per LED: green for 1, red for 0
colors = ['green' if val == 1 else 'red' for val in correct_LEDS]
plt.scatter(x_coords, y_coords, c=colors, marker='o')
plt.gca().invert_yaxis()  # Invert Y to match image coordinates
plt.axis('off')  # Remove axis
plt.show()


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
        # move next good to end of current good run
    try:
        # move next good to end of current good run
        while correct_LEDS[next_good] == 0:
            next_good += 1
        # save that as the last good
        previous_good = next_good-1
        # move up to next working ont
        while correct_LEDS[next_good] == 1:
            next_good += 1
    except IndexError:
        # this fails safe when we reach the end of the wire
        finished = True
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
            coords[scan+step] = [i+j for i,j in zip(coords[previous_good],[k*step/(next_good-previous_good) for k in differs])]
            step += 1

# Now need to convert to GIFT

x_coords = [c[0] for c in coords]
y_coords = [c[1] for c in coords]
colors = ['green' if val == 1 else 'red' for val in correct_LEDS]
plt.figure(figsize=(8, 8))
plt.scatter(x_coords, y_coords, c=colors, marker='o')
plt.gca().invert_yaxis()
plt.axis('off')
plt.show()



# sample_load_file[i][j]


#count = 0
#while(count < NUM_LEDS):
 #   if count != max:
  #      sample_load_file[count][1] = sample_load_file[count][1] - minValue
   #     sample_load_file[count][1] = sample_load_file[count][1] * 100 / sample_load_file[max][1]
    #count += 1
#count = 0
#print(sample_load_file)

#print(sample_load_file.index(max(sample_load_file)))



