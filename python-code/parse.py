import pingparser
import re
import matplotlib.pyplot as plt

rtt = []
seq = []
with open ("./ping/ping1.txt", "r") as myfile:
    for line in myfile:
	#if 'DUP' not in line:
		match1 = re.search('time=(\d+.\d+)', line)
		if not (match1 is None):
			rtt.append(match1.group(1))
		match2 = re.search('icmp_seq=(\d+)', line)
		if not (match2 is None):
			seq.append(match2.group(1))


plt.scatter(seq, rtt)
plt.plot(seq, rtt)
#plt.xlim([50, 70])
#plt.ylim([0, 50])
plt.ylabel('rtt')
plt.xlabel('time')
plt.show()

    #ping_output=myfile.read().replace('\n', '')
    #print pingparser.parse(ping_output)
