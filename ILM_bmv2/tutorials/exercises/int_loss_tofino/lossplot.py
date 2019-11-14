import matplotlib.pyplot as plt
import json
f = open("test.out","r")
line = f.readline()
paras = line.split(" ")
starttime = float(paras[0])
x = []
y = []
count = 0
while True:
     if line:
          paras = line.split(" ")
          time = float(paras[0]) - starttime
          loss = float(paras[3][1:-1])
          x.append(time)
          y.append(loss)
     plt.plot(x, y)
     plt.pause(0.01)
     plt.clf()
     line = f.readline()
     print(count)
     count+=1
     
