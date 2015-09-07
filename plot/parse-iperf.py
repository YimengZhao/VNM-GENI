import numpy as np
import re
import matplotlib.pyplot as plt

w = 12
h = 7
def _parse_droprate(file_dir):
	drop_rate = []
	time = []
	with open (file_dir, "r") as myfile:
	    current_time = 0
	    for line in myfile:
		#if 'DUP' not in line:
			match1 = re.search('\((\d+.\d+|\d+)%\)', line)
			if not (match1 is None):
				print match1.group(1)
				drop_rate.append(match1.group(1))
				time.append(current_time * 5)
				current_time += 1
	return time, drop_rate

time_1, droprate_1 = _parse_droprate('./iperf/h2-h3/1/10m-asyn-1.log')
time_2, droprate_2 = _parse_droprate('./iperf/h2-h3/1/10m-sym-1.log')
time_3, droprate_3 = _parse_droprate('./iperf/h2-h3/1/10m-base-1.log')
	            

fig = plt.figure()
fig.set_size_inches(w,h)
plt.plot(time_1, droprate_1, 'r', label='asymmetric routing')
plt.plot(time_2, droprate_2, 'b', label='symmetric routing')
plt.plot(time_3, droprate_3, 'g', label='baseline')
fig.suptitle('udp drop rate (10Mbits/s sending rate)')
#plt.xlim([50, 70])
plt.ylim([0, 0.3])
plt.xticks(np.arange(0, 600, 30))
plt.ylabel('drop rate (%s)')
plt.xlabel('time (s)')
plt.legend(loc='upper right')
plt.savefig('./iperf/h2-h3/1/10m-1.png')
#plt.show()

    #ping_output=myfile.read().replace('\n', '')
    #print pingparser.parse(ping_output)
