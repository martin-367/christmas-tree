import numpy as np
import json
import os

save_dir = "coordinates"
os.makedirs(save_dir, exist_ok=True)


with open((os.path.join(save_dir, "savedata.json")), "r") as json_File :
    sample_load_file = json.load(json_File)

print(sample_load_file)
NUM_LEDS = np.size(sample_load_file, 0)

max = sample_load_file.index(max(sample_load_file))


min = sample_load_file.index(min(sample_load_file))
minValue = sample_load_file[min][1]

sample_load_file[max][1] = sample_load_file[max][1] - minValue
sample_load_file[max][1] = sample_load_file[max][1] * 100 / sample_load_file[max][1]
print(max)


count = 0
while(count < NUM_LEDS):
    if count != max:
        sample_load_file[count][1] = sample_load_file[count][1] - minValue
        sample_load_file[count][1] = sample_load_file[count][1] * 100 / sample_load_file[max][1]
    count += 1
count = 0
print(sample_load_file)

#print(sample_load_file.index(max(sample_load_file)))



