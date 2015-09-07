import numpy as np
import re
import matplotlib.pyplot as plt
from itertools import izip

def _parse_droprate(file_dir):
	drop_rate_1 = []
	drop_rate_2 = []
	time_1 = []
	time_2 = []
	with open (file_dir, "r") as myfile:
	    current_time_1 = 0
	    current_time_2 = 0
	    for line in myfile:
		#if 'DUP' not in line:
			match2 = re.search("\[\s+(.*?)\]", line)
			if not (match2 is None):
				id = match2.group(1)
				match1 = re.search('\((\d+.\d+|\d+)%\)', line)
				if not (match1 is None):
					if id == "3":
						drop_rate_1.append(float(match1.group(1)))
						time_1.append(current_time_1 * 5)
						current_time_1 += 1
					elif id == "4":
						drop_rate_2.append(float(match1.group(1)))
						time_2.append(current_time_2 * 5)
						current_time_2 += 1
	return time_1, time_2, drop_rate_1, drop_rate_2

time_h1_wo, time_h2_wo, droprate_h1_wo, droprate_h2_wo = _parse_droprate('./iperf/h1-h3/wo-drop/15-15-2.log')
time_h1, time_h2, droprate_h1, droprate_h2  = _parse_droprate('./iperf/h1-h3/drop/15-15-2.log')
droprate_wo = map(sum, izip(droprate_h1_wo, droprate_h2_wo))
droprate = map(sum, izip(droprate_h1, droprate_h2))

	            

fig = plt.figure()
plt.plot(time_h1_wo, droprate_wo, 'r', label='w/o drop')
plt.plot(time_h1, droprate, 'b', label='drop')
fig.suptitle('udp drop rate (2 x 20Mbits/s sending rate)')
#plt.xlim([50, 70])
plt.ylim([0, 0.3])
plt.xticks(np.arange(0, 600, 30))
plt.ylabel('drop rate (%s)')
plt.xlabel('time (s)')
plt.legend(loc='upper right')
plt.show()

    
