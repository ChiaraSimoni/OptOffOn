import matplotlib.pyplot as plt

offline = [0.041387081146240234, 0.24812889099121094, 2.025507926940918, 5.046941041946411, 7.888674974441528]
online = [0.33979082107543945, 0.356090784072876, 0.5054318904876709, 0.5511560440063477,0.7350499629974365]
timelist = [sum(x) for x in zip(offline, online)]

resultimg, result = plt.subplots(figsize=(20, 10))
images, = result.plot(timelist, linestyle='-', color='green')

plt.ylabel('Execution Time')
plt.xlabel('Number of PODS')
plt.locator_params(axis='x', nbins=5)
plt.grid(True)
resultimg = plt.savefig('test.png', dpi=200) 

plt.close(resultimg)
