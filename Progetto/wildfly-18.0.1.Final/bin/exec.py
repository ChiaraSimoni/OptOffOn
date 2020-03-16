import multiprocessing
import time
import sys
import offline
import online
import numpy
import subprocess
import os

# <offline_status> <online_status> <load> <pv> <obj_func_Offline> <obj_func_Online> <threshold> <tolerance> 

if __name__ == "__main__":
    sys.stdout = open('out.log', 'w')
    sys.stderr = sys.stdout
    result = None
    print(len(sys.argv))
    print(sys.argv)
    if len(sys.argv) < 9:
        print("Ops, non ci sono abbastanza flag")
    else:
        if sys.argv[1] == 'on':
            p1 = multiprocessing.Process(target=offline.run_offline, args=(15, sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[7], sys.argv[8]))
            p1.start()
            p1.join()
        if sys.argv[2] == 'on':
            p2 = multiprocessing.Process(target=online.run_online, args=(15, sys.argv[6], sys.argv[1]))
            p2.start()
            p2.join()             
    print("Finito!")
