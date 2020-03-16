from __future__ import division
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import os

def generate_profile(df, percentage_thresh, percentage_tol, pods_num):
    
    profile = df.mean(axis=1).values.tolist()
    for t in range(len(profile)):
        profile[t] *= pods_num
        
    percentage_thresh = 100 - percentage_thresh # la soglia parte dal basso verso l'alto

    max_num = max(profile)

    threshold = percentage_thresh*max_num/100

    plt.subplots(figsize=(20, 10))
    plt.plot(profile, linestyle='-', marker='.', color='b')
    plt.axhline(y=threshold, color='r', linestyle='--')
    plt.ylabel('Energy value (kW)')
    plt.xlabel('Time instant')
    #plt.locator_params(axis='x', nbins=96)
    plt.grid(True)

    # Calcolo uno slice per togliere eccessi

    acc_excess = 0
    indexes_over_threshold = []
    indexes_under_threshold = []
    for t in range(0, len(profile)):
        if profile[t] > threshold:
            acc_excess += profile[t] - threshold
            indexes_over_threshold.append(t)
        else:
            indexes_under_threshold.append(t)

    excess_slice = (acc_excess/(10000*len(indexes_under_threshold)))

    removed_power = 0
    for t in indexes_over_threshold:
        old_value = profile[t]
        removed_power += (profile[t]-threshold)*(100-percentage_tol)/100
        current_removed = (profile[t]-threshold)*(100-percentage_tol)/100
        profile[t] -= current_removed

    full_flags = []

    for t in range(0, len(profile)):
        full_flags.append(0)

    while removed_power > 0:
        for t in indexes_under_threshold:
            if profile[t] + excess_slice < threshold and removed_power > 0:
                profile[t] += excess_slice
                removed_power -= excess_slice
                #print("Iterazione {}, valori: profile[t] = {}, removed_power = {}".format(t, profile[t], removed_power))
                #print("remaining power to redistribute: ", removed_power)
            elif profile[t] + excess_slice > threshold and full_flags[t] != 1:
                #print("profile[{}]+excess_slice>threshold: {} + {} > {}".format(t, profile[t], excess_slice, threshold))
                full_flags[t] = 1
                if sum(full_flags) == len(indexes_under_threshold):
                    break
                #print(sum(full_flags))
                #print("Senza eccesso: ", len(indexes_under_threshold))
                #print("Con eccesso: ", len(indexes_over_threshold))
        if sum(full_flags) == len(indexes_under_threshold):
            break

    plt.plot(profile, linestyle='-', marker='.', color='g')
    plt.savefig('desired_profile.png', dpi=200)

    return profile
    

def main(argv):
    # in realtà il main ha solo funzionalità di testing, dall'esterno si chiama direttamente la funzione con i parametri

    load_profiles_df = pd.read_excel("Summer_Load_Profiles.xlsx", header=None) + pd.read_excel("Winter_Load_Profiles.xlsx", header=None)
    print(len(generate_profile(load_profiles_df, 60, 10)))

if __name__ == '__main__':
    main(sys.argv[1:])