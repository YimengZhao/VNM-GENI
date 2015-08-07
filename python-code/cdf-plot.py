import numpy as np

import matplotlib.pyplot as plt

data = np.loadtxt('test.txt')

sorted_data = np.sort(data)

yvals=np.linspace(0,1,sorted_data.size)

plt.plot(sorted_data,yvals)

plt.show()

