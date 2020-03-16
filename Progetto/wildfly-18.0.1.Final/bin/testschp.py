import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import os

def parse_config(conf_file_path):
    result = []
    with open(conf_file_path, 'r') as config:
        for line in config:
            #prima divido ogni riga del file in elementi
            elements = line.strip().split(':')
            pod_id = int(elements[1])
            column_index = elements[2]
            #poi mi ricavo i componenti del pod 
            comp_list = elements[3][1:-1].split(',')
            #e trasformo tutto in lista: [pod_id, column_index, [lista di elementi]]
            result.append([pod_id, column_index, comp_list])
    
    return result

def change_scale(actual_slice_minutes, intended_slice_minutes, df, debug=False):
    if actual_slice_minutes < intended_slice_minutes:
        row_interval = int(intended_slice_minutes/actual_slice_minutes)
        actual_row_number, actual_column_number = df.shape
        result = pd.DataFrame()
        for i in range(int(actual_row_number/row_interval)):
            temp_list = []
            for j in range(row_interval):
                if debug:
                    print("DEBUG: Converting row {}".format(i*row_interval+j))
                temp_list.append(df.iloc[i*row_interval+j].values.flatten().tolist())
            result = result.append(pd.Series(np.mean(np.asarray(temp_list), axis=0)), ignore_index=True)
            if debug:
                print("DEBUG: Produced row {}".format(i))
    elif actual_slice_minutes > intended_slice_minutes:
        row_interval = int(actual_slice_minutes/intended_slice_minutes)
        result = pd.DataFrame()
        actual_row_number, actual_column_number = df.shape
        for index, row in df.iterrows():
            if debug:
                print("DEBUG: Converting row {}".format(index))
            for j in range(row_interval):
                if debug:
                    print("DEBUG: Produced sub-row {}".format(j))
                result = result.append(row, ignore_index=True)
    else:
        result = df

    return result
# prende in ingresso la pod_list_config e l'obiettivo è quello di inserire dopo tutti gli elementi già presenti, i df con i valori di
# load e pv, se questi componenti sono inclusi nel pod, altrimenti inserisce un df vuoto
# ricordiamo che pod[1] è l'indice del pod, pod[2] è l'indice della colonna nel file xlsx
def init_pods(pod_list_config, df1, df2, debug=False):
    component_name_list = []
    # i in questo caso è la posizione in cui è arrivata l'iterazione 
    for i, pod in enumerate(pod_list_config):
        temp_df = pd.DataFrame()
        #controlliamo se è presente il load, il pv, uno dei due o nessuno
        for component in pod[2]:
            if component == 'load':
                temp_df = pd.concat([temp_df, df1[int(pod[1])]], axis=1)
                component_name_list.append(component)
            elif component == 'pv':
                temp_df = pd.concat([temp_df, df2[int(pod[1])]], axis=1) 
                component_name_list.append(component)
        
        #print(component_name_list)
        #print(pod[2])
        temp_df.columns = component_name_list
        result_df = pd.DataFrame()
        pod_list_config[i] = [pod[0], pod[1], pod[2], temp_df, result_df]
        component_name_list = []     

load_profiles_df = pd.read_excel("Summer_Load_Profiles.xlsx", header=None) + pd.read_excel("Winter_Load_Profiles.xlsx", header=None)
pv_profiles_df = pd.read_excel("Summer_PV_Profiles.xlsx", header=None)

scaled_load_df = change_scale(5, 60, load_profiles_df, False)
scaled_pv_df = change_scale(5, 60, pv_profiles_df, False)

pod_list_conf = parse_config('config.conf')
init_pods(pod_list_conf, scaled_load_df, scaled_pv_df)



chp_index_list = []
for pod in pod_list_conf:
    for el in pod[2]:
        if el == 'chp':
            chp_index_list.append(pod[0])

schp_df = pd.read_csv('schp.csv')
print(schp_df)
for t in range(0,24):
    print(schp_df.values.tolist()[t])
    for i in chp_index_list:
        print(schp_df[str(i)].values.tolist()[t])

