from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from pyomo.core.expr.numvalue import value
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import os
import profile_gen

# Usage:
# python script.py

# struttura file config:
# pod:<ID_POD>:<COLONNA_PROFILO>:[<elementi separati da virgola>]

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
# controllo inolte se ci sono i flag per l'incertezza attivi
# se così fosse, aggiungo al df le colonne above e below, che userò poi nelle equazioni
def init_pods(pod_list_config, df1, df2, load_flag, pv_flag, debug=False):
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
        if load_flag == 1:
            if 'load' in pod[2]:
                temp_df['load+'] = temp_df['load'] + temp_df['load']*0.2
                temp_df['load-'] = temp_df['load'] - temp_df['load']*0.2
        else:
            if 'load' in pod[2]:
                temp_df['load+'] = temp_df['load']
                temp_df['load-'] = temp_df['load']

        pod_list_config[i] = [pod[0], pod[1], pod[2], temp_df]
        if pv_flag == 1:
            if 'pv' in pod[2]:
                temp_df['pv+'] = temp_df['pv'] + temp_df['pv']*0.1
                temp_df['pv-'] = temp_df['pv'] - temp_df['pv']*0.1
        else:
            if 'pv' in pod[2]:
                temp_df['pv+'] = temp_df['pv']
                temp_df['pv-'] = temp_df['pv']

        pod_list_config[i] = [pod[0], pod[1], pod[2], temp_df]
        #print(temp_df)
        component_name_list = [] # alla fine di ogni iterazione va svuotata, perchè iteriamo su ogni pod         

def get_info_from_results(results, info_string):
    i = str(results).lower().find(info_string.lower()) + len(info_string)
    value = ''
    while str(results)[i] != '\n':
        value = value + str(results)[i]
        i += 1
    return value

def run_offline(slice_size, load_flag, pv_flag, opt_func, threshold, tolerance):
    params = [slice_size, load_flag, pv_flag, opt_func, threshold, tolerance]
    print(params)
    main(params)

def main(argv):
    debug = False
    # CONTROLLI SUGLI ARGOMENTI
    # usage: python offlineU.py <slice_size> <load_flag> <pv_flag> <opt_func>
    slice_size = 60 
    pv_flag = 0
    load_flag = 0
    S = 4 
    opt_func = "cost"
    # S0 ++
    # S1 +-
    # S2 -+
    # S3 --

    if len(argv) < 4:
        print("Not enough arguments: using default values, 15 0 0 cost")    
    else:
        slice_size = int(argv[0])
        if argv[1] == 'on':
            load_flag = 1 
        if argv[2] == 'on':
            pv_flag = 1
        opt_func = argv[3]
    if opt_func == "profile":
        if len(argv) == 6:
            threshold = int(argv[4])
            tolerance = int(argv[5])
        else:
            print("Could not find correct values for threshold and tolerance, using default ones")
            threshold = 60
            tolerance = 10
   
    if pv_flag == 0 and load_flag == 0: 
        S = 1
    if (pv_flag == 1 and load_flag == 0) or (pv_flag == 0 and load_flag == 1):
        S = 2 
    
    # Data preprocessing
    load_profiles_df = pd.read_excel("Summer_Load_Profiles.xlsx", header=None) + pd.read_excel("Winter_Load_Profiles.xlsx", header=None)
    pv_profiles_df = pd.read_excel("Summer_PV_Profiles.xlsx", header=None)
    uchp_profiles_df = pd.read_excel("Winter_uCHP_Profiles.xlsx", header=None)
    prices_df = pd.read_csv("pricesGME.csv", usecols=[1])
    
    scaled_load_df = change_scale(5, slice_size, load_profiles_df, debug) # kW
    scaled_pv_df = change_scale(5, slice_size, pv_profiles_df, debug) # kW
    scaled_prices_df = change_scale(60, slice_size, prices_df, debug)
    scaled_prices_df.columns =['prices']
    #print(scaled_prices_df.values.tolist())

    pod_list_conf = parse_config('config.conf')
    init_pods(pod_list_conf, scaled_load_df, scaled_pv_df, load_flag, pv_flag)

    flattened_profile = []
    if opt_func == "profile":
        flattened_profile = profile_gen.generate_profile(scaled_load_df, threshold, tolerance, len(pod_list_conf))

    # definizione delle costanti     
    uchp_min = uchp_profiles_df.values.min() # kW
    uchp_max = uchp_profiles_df.values.max() # kW
    cuchp = 0.05
    cchp_gas = 0.039
    gas_chp_min = 0
    gas_chp_max = 10 
    eta = 0.9
    gin_min = 0
    gout_min = 0
    gin_max = 4
    gout_max = 4 
    sin_max = 4
    sout_max = 4
    charge_init = 2 ## inizializzato il valore della batteria
    charge_max = 6

    T = int(scaled_load_df[0].count()) # in questo caso 96
        
    if debug:
        print("DEBUG: uchp: min: {}; max: {}.".format(uchp_min, uchp_max))
    
    fixed_index_list = []
    fixed_time_list = range(T)
    fixed_scenario_list = range(S)
   
    model = ConcreteModel()

    for pod in pod_list_conf:
        fixed_index_list.append(pod[0])
    
    # variabili sempre presenti
    model.Pgin = Var(fixed_index_list, fixed_time_list, fixed_scenario_list, domain = NonNegativeReals)
    model.Pgout = Var(fixed_index_list, fixed_time_list, fixed_scenario_list, domain = NonNegativeReals)
    model.Tildeload = Var(fixed_time_list, fixed_scenario_list, domain = NonNegativeReals)
    
    # variabili dipendenti dalla costruzione del pod
    # charge
    charge_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'storage':
                charge_index_list.append(pod[0]) #prendiamo la lista dei pod, e controlliamo quali hanno st, quindi aggiungiamo il loro indice a charge_index_list
    
    if charge_index_list: #se la lista non è vuota
        model.charge = Var(charge_index_list, fixed_time_list, fixed_scenario_list, domain = NonNegativeReals)
        model.Psin = Var(charge_index_list, fixed_time_list, fixed_scenario_list, domain = NonNegativeReals)
        model.Psout = Var(charge_index_list, fixed_time_list, fixed_scenario_list,domain = NonNegativeReals)
    #pv
    pv_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'pv':
                pv_index_list.append(pod[0])

    # uchp
    uchp_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'uchp':
                uchp_index_list.append(pod[0])
    
    if uchp_index_list:
        model.Puchp = Var(uchp_index_list, fixed_time_list, fixed_scenario_list)
        model.Suchp = Var(uchp_index_list, fixed_time_list, domain = Reals)  # shifted uchp
        model.Tildeuchp = Var(fixed_time_list, fixed_scenario_list, domain = NonNegativeReals) # non associato a s perchè non centra niente con gli scenari, a differenza di tildeload

    # gas_chp
    gas_chp_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'gas_chp':
                gas_chp_index_list.append(pod[0])
    
    if gas_chp_index_list:
        model.Pgas_chp = Var(gas_chp_index_list, fixed_time_list, fixed_scenario_list)
        model.Sgas_chp = Var(gas_chp_index_list, fixed_time_list, domain = Reals)  # shifted uchp
        model.Tildegas_chp = Var(fixed_time_list, fixed_scenario_list, domain = NonNegativeReals) # non associato a s perchè non centra niente con gli scenari, a differenza di tildeload

    # load
    load_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'load':
                load_index_list.append(pod[0])
                           
    if load_index_list:
        model.Sload = Var(load_index_list, fixed_time_list, domain = Reals)

    def objective(model):
        result = 0
        
        for i, pod in enumerate(pod_list_conf):
            for t in fixed_time_list:
                for s in fixed_scenario_list:
                    if opt_func == "cost":
                        result += (1/ len(fixed_scenario_list))*model.Pgin[i,t,s]*scaled_prices_df['prices'].values.tolist()[t] - model.Pgout[i,t,s]*scaled_prices_df['prices'].values.tolist()[t]
                        if 'uchp' in pod[2]:
                            result += cuchp*model.Tildeuchp[t,s]
                        if 'gas_chp' in pod[2]:
                            result += cchp_gas*model.Tildegas_chp[t,s]
                        if 'storage' in pod[2]:
                            result += model.Psout[i,t,s]*scaled_prices_df['prices'].values.tolist()[t]
                    elif opt_func == "grid":
                        result += (1/ len(fixed_scenario_list))*model.Pgin[i,t,s]*scaled_prices_df['prices'].values.tolist()[t] + model.Pgout[i,t,s]*scaled_prices_df['prices'].values.tolist()[t]
                    # distanza minima tra profilo del carico e profilo desiderato
                    # formula = sqrt(sommatoria((x_i-y_i)^2)/N)
                    elif opt_func == "profile":
                        result += (1/(len(fixed_scenario_list)*T))*((model.Tildeload[t,s] - flattened_profile[t])**2)
            
        return result               

    model.OBJ = Objective(rule=objective)   

    # CONSTRAINTS

    # uchp:

    # if there are no uchp the constraint shouldn't be initialized
    if uchp_index_list:
        model.bound_uchp = ConstraintList()
        model.bound_Suchp = ConstraintList()
        model.bound_tildeuchp = ConstraintList()
    
    #print(str(uchp_min) + " " + str(uchp_max))
    for i in uchp_index_list:
        for t in fixed_time_list:
            for s in fixed_scenario_list:
                model.bound_uchp.add(inequality(uchp_min, model.Tildeuchp[t,s], uchp_max))

    multipl_constant = int(60/slice_size)
    for i in uchp_index_list:
        for s in fixed_scenario_list:
            for t in range(0*multipl_constant, 4*multipl_constant):
                model.bound_Suchp.add(inequality(-0.150, model.Suchp[i,t], 0.150))
                if t < 4*multipl_constant - 1:
                    #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                    model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                    model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])
                                    
            for t in range(4*multipl_constant, 8*multipl_constant):
                model.bound_Suchp.add(inequality(-0.150, model.Suchp[i,t], 0.150))
                if t < 8*multipl_constant - 1:
                   #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                   model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                   model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])

            for t in range(8*multipl_constant, 12*multipl_constant):
                model.bound_Suchp.add(inequality(-0.400, model.Suchp[i,t],0.400))
                if t < 12*multipl_constant - 1:
                    #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                    model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                    model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])

            for t in range(12*multipl_constant, 16*multipl_constant):
                model.bound_Suchp.add(inequality(-0.200, model.Suchp[i,t], 0.200))
                if t < 16*multipl_constant - 1:    
                   #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                   model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                   model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])

            for t in range(16*multipl_constant, 20*multipl_constant):
                model.bound_Suchp.add(inequality(-0.50, model.Suchp[i,t], 0.50))
                if t < 20*multipl_constant - 1:
                   #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                   model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                   model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])

            for t in range(20*multipl_constant, 24*multipl_constant):
                model.bound_Suchp.add(inequality(-0.100, model.Suchp[i,t],0.100))
                if t < 24*multipl_constant - 1:
                    #model.bound_Suchp.add( model.Tildeuchp[t,s] == model.Tildeuchp[t+1,s])
                    model.bound_Suchp.add( model.Suchp[i,t] == model.Suchp[i,t+1])
                    model.bound_Suchp.add( model.Puchp[i,t,s] == model.Puchp[i,t+1,s])
    
    if uchp_index_list:
        for t in fixed_time_list:   
            for s in fixed_scenario_list:
                left_side = 0
                right_side = 0 
                left_side += model.Tildeuchp[t,s]
                for i in uchp_index_list:
                    right_side += model.Puchp[i,t,s] + model.Suchp[i,t]
                model.bound_tildeuchp.add(left_side == right_side) 

    if uchp_index_list:    
        model.bound_suchp2 = Constraint(expr= sum(model.Suchp[i,t] for i in uchp_index_list for t in fixed_time_list) == 0)   
    
    # gas_chp:

    # if there are no gas_chp the constraint shouldn't be initialized
    if gas_chp_index_list:
        model.bound_gas_chp = ConstraintList()
        model.bound_Sgas_chp = ConstraintList()
        model.bound_tildegas_chp = ConstraintList()
    
    #print(str(gas_chp_min) + " " + str(gas_chp_max))
    for i in gas_chp_index_list:
        for t in fixed_time_list:
            for s in fixed_scenario_list:
                model.bound_gas_chp.add(inequality(gas_chp_min, model.Tildegas_chp[t,s], gas_chp_max))

    multipl_constant = int(60/slice_size)
    for i in gas_chp_index_list:
        for s in fixed_scenario_list:
            for t in range(0*multipl_constant, 4*multipl_constant):
                model.bound_Sgas_chp.add(inequality(0, model.Sgas_chp[i,t], 10))
                if t < 4*multipl_constant - 1:
                    #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                    model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                    model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])
                                    
            for t in range(4*multipl_constant, 8*multipl_constant):
                model.bound_Sgas_chp.add(inequality(0, model.Sgas_chp[i,t], 6))
                if t < 8*multipl_constant - 1:
                    #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                    model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                    model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])

            for t in range(8*multipl_constant, 12*multipl_constant):
                model.bound_Sgas_chp.add(inequality(-1, model.Sgas_chp[i,t],1))
                if t < 12*multipl_constant - 1:
                    #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                    model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                    model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])

            for t in range(12*multipl_constant, 16*multipl_constant):
                model.bound_Sgas_chp.add(inequality(0, model.Sgas_chp[i,t], 0.5))
                if t < 16*multipl_constant - 1:    
                    #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                    model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                    model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])

            for t in range(16*multipl_constant, 20*multipl_constant):
                model.bound_Sgas_chp.add(inequality(0, model.Sgas_chp[i,t], 5))
                if t < 20*multipl_constant - 1:
                   #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                   model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                   model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])

            for t in range(20*multipl_constant, 24*multipl_constant):
                model.bound_Sgas_chp.add(inequality(0, model.Sgas_chp[i,t],8))
                if t < 24*multipl_constant - 1:
                    #model.bound_Sgas_chp.add( model.Tildegas_chp[t,s] == model.Tildegas_chp[t+1,s])
                    model.bound_Sgas_chp.add( model.Sgas_chp[i,t] == model.Sgas_chp[i,t+1])
                    model.bound_Sgas_chp.add( model.Pgas_chp[i,t,s] == model.Pgas_chp[i,t+1,s])
    
    if gas_chp_index_list:
        for t in fixed_time_list:   
            for s in fixed_scenario_list:
                left_side = 0
                right_side = 0 
                left_side += model.Tildegas_chp[t,s]
                for i in gas_chp_index_list:
                    right_side += model.Pgas_chp[i,t,s] + model.Sgas_chp[i,t]
                model.bound_tildegas_chp.add(left_side == right_side) 

    if gas_chp_index_list:    
        model.bound_sgas_chp2 = Constraint(expr= sum(model.Sgas_chp[i,t] for i in gas_chp_index_list for t in fixed_time_list) == 0)   
    
    # STORAGE:
    #print(charge_index_list)
    if charge_index_list:
        model.bound_charge = ConstraintList()

    for i in charge_index_list:
        for t in fixed_time_list:
            for s in fixed_scenario_list:
                #constrain che devono valere sempre
                model.bound_charge.add(model.Psin[i,t,s] <= sin_max)
                model.bound_charge.add(model.Psout[i,t,s] <= sout_max)

                #constraint per l'istante iniziale
                if t == 0:
                    model.bound_charge.add(model.charge[i,t,s] == charge_init)
                    model.bound_charge.add(model.charge[i,t,s] <= charge_max)
                    model.bound_charge.add(model.charge[i,t,s] >= 0)
                    
                    model.bound_charge.add(model.Psin[i,t,s] <= charge_max - charge_init)
                    model.bound_charge.add(model.Psout[i,t,s] <= charge_init)
                else:               
                    model.bound_charge.add(model.charge[i,t,s] == model.charge[i,t-1,s] - eta*model.Psin[i,t,s] + eta*model.Psout[i,t,s])
                    
                    model.bound_charge.add(model.charge[i,t,s] <= charge_max)
                    model.bound_charge.add(model.charge[i,t,s] >= 0)
                    model.bound_charge.add(model.Psin[i,t,s] <= charge_max - model.charge[i,t-1,s])
                    model.bound_charge.add(model.Psout[i,t,s] <= model.charge[i,t-1,s])
                
    # GRID:
    
    model.bound_gin = ConstraintList()
    model.bound_gout = ConstraintList()
    for i, pod in enumerate(pod_list_conf):
        for t in fixed_time_list:
            for s in fixed_scenario_list:
                model.bound_gin.add(inequality(gin_min, model.Pgin[i,t,s], gin_max ))
                model.bound_gout.add(inequality(gout_min, model.Pgout[i,t,s], gout_max ))

    # TILDELOAD / POWER BALANCE
    # Potrebbe contenere un termine relativo ad un componente load
  
    model.bound_tildeload = ConstraintList()
    for t in fixed_time_list:
        for s in fixed_scenario_list:
            right_side = 0 
            left_side = model.Tildeload[t,s]
            for i, pod in enumerate(pod_list_conf):
                if 'load' in pod[2]:
                    if S == 1:
                        right_side += model.Sload[i,t] + pod[3]['load'].values.tolist()[t]
                    elif S == 2:
                        if s == 0:
                            right_side += model.Sload[i,t] + pod[3]['load+'].values.tolist()[t]
                        else:
                            right_side += model.Sload[i,t] + pod[3]['load-'].values.tolist()[t]
                    else:
                        if s <= 1 :
                            right_side += model.Sload[i,t] + pod[3]['load+'].values.tolist()[t]
                        else:
                            right_side += model.Sload[i,t] + pod[3]['load-'].values.tolist()[t]
                
            model.bound_tildeload.add(left_side == right_side) 

    model.bound_tildeload2 = ConstraintList()
    for t in fixed_time_list:
        for s in fixed_scenario_list:
            right_side = 0
            left_side = model.Tildeload[t,s]
            for i, pod in enumerate(pod_list_conf):
                right_side += model.Pgin[i,t,s] - model.Pgout[i,t,s] 
                if 'uchp' in pod[2]:
                    right_side += model.Puchp[i,t,s] + model.Suchp[i,t]
                if 'gas_chp' in pod[2]:
                    right_side += model.Pgas_chp[i,t,s] + model.Sgas_chp[i,t]
                if 'storage' in pod[2]:
                    right_side += model.Psin[i,t,s] - model.Psout[i,t,s]
                if 'pv' in pod[2]:
                    if S == 1:
                        right_side += pod[3]['pv'].values.tolist()[t]
                    elif S == 2:
                        if s == 0:
                            right_side += pod[3]['pv+'].values.tolist()[t]
                        else:
                            right_side += pod[3]['pv-'].values.tolist()[t]
                    else:
                        if s == 1 or s == 2 :
                            right_side += pod[3]['pv+'].values.tolist()[t]
                        else:
                            right_side += pod[3]['pv-'].values.tolist()[t]
            
        model.bound_tildeload2.add(left_side == right_side)

    #SLOAD:
    if load_index_list:    
        model.bound_sload2 = Constraint(expr= sum(model.Sload[i,t] for i in load_index_list for t in fixed_time_list) == 0)
    
    if load_index_list:
        model.bound_sload = ConstraintList()
    
    for i in load_index_list:
        current_pod = pod_list_conf[i]
        for t in fixed_time_list:
            for s in fixed_scenario_list:
                if S == 1:
                    model.bound_sload.add(inequality(-current_pod[3]['load'].values.tolist()[t] - 0.1*current_pod[3]['load'].values.tolist()[t], 
                                model.Sload[i,t], current_pod[3]['load'].values.tolist()[t] + 0.1*current_pod[3]['load'].values.tolist()[t])) 
                elif S == 2:
                    if s == 0:
                        model.bound_sload.add(inequality(-current_pod[3]['load+'].values.tolist()[t] - 0.1*current_pod[3]['load+'].values.tolist()[t], 
                                model.Sload[i,t], current_pod[3]['load+'].values.tolist()[t] + 0.1*current_pod[3]['load+'].values.tolist()[t])) 
                    else:
                        model.bound_sload.add(inequality(-current_pod[3]['load-'].values.tolist()[t] - 0.1*current_pod[3]['load-'].values.tolist()[t], 
                                model.Sload[i,t], current_pod[3]['load-'].values.tolist()[t] + 0.1*current_pod[3]['load-'].values.tolist()[t])) 
                else:
                    if s <= 1 : 
                        model.bound_sload.add(inequality(-current_pod[3]['load+'].values.tolist()[t] - 0.1*current_pod[3]['load+'].values.tolist()[t], 
                                model.Sload[i,t], current_pod[3]['load+'].values.tolist()[t] + 0.1*current_pod[3]['load+'].values.tolist()[t])) 
                    else:
                        model.bound_sload.add(inequality(-current_pod[3]['load-'].values.tolist()[t] - 0.1*current_pod[3]['load-'].values.tolist()[t], 
                                model.Sload[i,t], current_pod[3]['load-'].values.tolist()[t] + 0.1*current_pod[3]['load-'].values.tolist()[t]))      
        
    #model.pprint()
    
    opt = SolverFactory('gurobi')
    results = opt.solve(model, tee=True) 

    #in alternativa model.load(results)
    model.solutions.store_to(results)
    results.write()
        
    sload_df = pd.DataFrame()
    for i in load_index_list:
        temp_list = []
        for t in fixed_time_list:
            temp_list.append(model.Sload[i,t].value)
        sload_df[str(i)] = temp_list
    sload_df.to_csv('sload.csv', index=False)

    suchp_df = pd.DataFrame()
    for i in uchp_index_list:
        temp_list = []
        for t in fixed_time_list:
            temp_list.append(model.Suchp[i,t].value)
        suchp_df[str(i)] = temp_list
    suchp_df.to_csv('suchp.csv', index=False)
    
    sgas_chp_df = pd.DataFrame()
    for i in gas_chp_index_list:
        temp_list = []
        for t in fixed_time_list:
            temp_list.append(model.Sgas_chp[i,t].value)
        sgas_chp_df[str(i)] = temp_list
    sgas_chp_df.to_csv('sgas_chp.csv', index=False)

    # TEMPO DI RISOLUZIONE   
    solver_time = get_info_from_results(results, 'Time: ')
    #print("SOLVER TIME: " +  str(solver_time))
    #print(model.OBJ())
    f = open("output_offline.txt", "a")
    f.write("Components: {}\n".format(len(pv_index_list)+len(load_index_list)+len(gas_chp_index_list)+len(uchp_index_list)+len(charge_index_list)))
    f.write("    # Pv: {}\n".format(len(pv_index_list)))
    f.write("    # Load: {}\n".format(len(load_index_list)))
    f.write("    # Gas Chp: {}\n".format(len(gas_chp_index_list)))
    f.write("    # Uchp: {}\n".format(len(uchp_index_list)))
    f.write("    # Storage: {}\n".format(len(charge_index_list)))
    f.write("SOLVER TIME:" + str(solver_time) + "\n")
    f.write("OBJECTIVE VALUE with function {}:".format(argv[3]) + str(model.OBJ()) + "\n")
    f.write("\n")

    f.close()

    # CONTROLLO SULLA TERMINAZIONE
    if (results.solver.termination_condition == TerminationCondition.optimal):
        print("Modello risolto correttamente")
    elif (results.solver.termination_condition == TerminationCondition.infeasible):
        print("La condizione di terminazione è INFEASIBLE")
    else:
        print("Errore: Solver Status", results.solver.status)

    stdout_backup = sys.stdout

    with open('results_offline.yml', 'a') as f:
        sys.stdout = f
        results.write()

    sys.stdout = stdout_backup

    #da plottare: i valori di Pload presi in input, ovvero il carico previsto, e gli Sload, ovvero i carichi reali
    tildelist = []
    for t in fixed_time_list:
        acc = 0
        for s in fixed_scenario_list:
            acc += model.Tildeload[t,s].value
        plot = float(acc/S)
        tildelist.append(plot)

    loadlist = []
    if load_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in load_index_list:
                acc += pod_list_conf[i][3]['load'].values.tolist()[t]
            loadlist.append(acc)

    pvlist = []
    if pv_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in pv_index_list:
                acc += pod_list_conf[i][3]['pv'].values.tolist()[t]
            plot = float(acc)
            pvlist.append(plot)

    uchplist = []
    if uchp_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in uchp_index_list:
                for s in fixed_scenario_list:
                    acc += model.Puchp[i,t,s].value
                    #print(model.Puchp[i,t,s].value + str("uchp"))
            plot = float(acc/(S))
            uchplist.append(plot)

    suchplist = []
    if uchp_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in uchp_index_list:
                acc += model.Suchp[i,t].value
            plot = float(acc)
            suchplist.append(plot)
    
    tildeuchplist = []
    if uchp_index_list:
        for t in fixed_time_list:
            acc = 0
            for s in fixed_scenario_list:
                acc += model.Tildeuchp[t,s].value
            plot = float(acc/S)
            tildeuchplist.append(plot)

    gaschplist = []
    if gas_chp_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in gas_chp_index_list:
                for s in fixed_scenario_list:
                    acc += model.Pgas_chp[i,t,s].value
                    #print(model.Puchp[i,t,s].value + str("uchp"))
            plot = float(acc/(S))
            gaschplist.append(plot)

    sgaschplist = []
    if gas_chp_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in gas_chp_index_list:
                acc += model.Sgas_chp[i,t].value
            plot = float(acc)
            sgaschplist.append(plot)
    
    tildegaschplist = []
    if gas_chp_index_list:
        for t in fixed_time_list:
            acc = 0
            for s in fixed_scenario_list:
                acc += model.Tildegas_chp[t,s].value
            plot = float(acc/S)
            tildegaschplist.append(plot)

    gridINlist = []
    for t in fixed_time_list:
        acc = 0
        for i in range(len(pod_list_conf)):
            for s in fixed_scenario_list:
                acc += model.Pgin[i,t,s].value
        plot = float(acc/(S))
        #print(str(mean) + " Pgin")
        gridINlist.append(plot)

    gridOUTlist = []
    for t in fixed_time_list:
        acc = 0
        for i in range(len(pod_list_conf)):
            for s in fixed_scenario_list:
                acc += model.Pgout[i,t,s].value
        plot = float(acc/(S))
        #print(str(mean) + " Pgout")
        gridOUTlist.append(-plot)

    stINlist = []
    if charge_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in charge_index_list:
                for s in fixed_scenario_list:
                    acc += model.Psin[i,t,s].value
            plot = float(acc/(S))
            stINlist.append(plot)

    stOUTlist = []
    if charge_index_list:
        for t in fixed_time_list:
            acc = 0
            for i in charge_index_list:
                for s in fixed_scenario_list:
                    acc += model.Psout[i,t,s].value
            plot = float(acc/(S))
            stOUTlist.append(-plot)
    
    resultimg, result = plt.subplots(figsize=(20, 10))
    images, = result.plot(tildelist, linestyle='-', color='red')
    images, = result.plot(pvlist, linestyle='-', color='green')
    images, = result.plot(tildeuchplist, linestyle='-', color='magenta')
    images, = result.plot(tildegaschplist, linestyle='-', color='purple')
    images, = result.plot([sum(x) for x in zip(gridINlist,gridOUTlist)], linestyle='-', color='#3a55a1', linewidth=2)
    #images, = result.plot(gridOUTlist, linestyle='-', color='blue', linewidth=2)
    images, = result.plot([sum(x) for x in zip(stINlist,stOUTlist)], linestyle='-', color='#fa7e25', linewidth=2)
    #images, = result.plot(stOUTlist, linestyle='-', color='orange', linewidth=2)
    images, = result.plot(flattened_profile, linestyle='--', color='k')

    tilde = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildelist)
    result.fill_between(np.arange(0.0, 96.0, 0.1), tilde, 0, facecolor='red', alpha=0.3)

    if pv_index_list:
        pv = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, pvlist)
        result.fill_between(np.arange(0.0, 96.0, 0.1), pv, 0, facecolor='green', alpha=0.5)
    
    if uchp_index_list:
        uchp = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildeuchplist)
        result.fill_between(np.arange(0.0, 96.0, 0.1), uchp, 0, facecolor='purple', alpha=0.1)
    
    if gas_chp_index_list:
        gaschp = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildegaschplist)
        result.fill_between(np.arange(0.0, 96.0, 0.1), gaschp, 0, facecolor='purple', alpha=0.1)

    result.legend(['Load', 'PV', 'UChp', 'GASChp', 'Grid', 'Storage', 'Desired profile'], fancybox=True, framealpha=0.5)
    
    plt.ylabel('Energy value (kW)')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=96)
    plt.grid(True)
    resultimg = plt.savefig('results_offline.png', dpi=200) 

    plt.close(resultimg)

    # GRAFICO A CIAMBELLA CON PERCENTUALI
    
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    data = [sum(pvlist),
            sum(uchplist),
            sum(gaschplist),
            abs(sum([sum(x) for x in zip(gridINlist,gridOUTlist)])),
            abs(sum([sum(x) for x in zip(stINlist,stOUTlist)]))
            ]
    labels = ['PV', 'UChp', 'GASChp', 'Grid', 'Storage']
    
    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.1f}%\n({:d} kWh)".format(pct, absolute)

    wedges, texts, autotexts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40, autopct=lambda pct: func(pct, data), pctdistance=0.8, textprops={'color': "w", 'fontsize': 7})

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
            bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(labels[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                    horizontalalignment=horizontalalignment, **kw)
       
    ax = plt.savefig('pie_offline.png', dpi=200) 

    plt.close(ax)

    # GRAFICO uchp
    uchpimg, uchpplt = plt.subplots(figsize=(20, 10))
    images, = uchpplt.plot(tildeuchplist, linestyle='--', marker='.', color='red')
    images, = uchpplt.plot(suchplist, linestyle='-',color='purple')
    images, = uchpplt.plot(uchplist, linestyle='-', color='magenta')

    uchpplt.legend(['Tilde', 'Suchp', 'Puchp'], fancybox=True, framealpha=0.5)
    
    plt.ylabel('uchp value')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=24)
    plt.grid(True)
    uchpimg = plt.savefig('results_offline_uchp.png', dpi=200) 
    
    plt.close(uchpimg)

    # GRAFICO gas_chp
    gaschpimg, gaschpplt = plt.subplots(figsize=(20, 10))
    images, = gaschpplt.plot(tildegaschplist, linestyle='--', marker='.', color='red')
    images, = gaschpplt.plot(sgaschplist, linestyle='-',color='purple')
    images, = gaschpplt.plot(gaschplist, linestyle='-', color='magenta')

    gaschpplt.legend(['Tilde', 'Sgas_chp', 'Pgas_chp'], fancybox=True, framealpha=0.5)
    
    plt.ylabel('gas_chp value')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=24)
    plt.grid(True)
    uchpimg = plt.savefig('results_offline_gaschp.png', dpi=200) 
    
    plt.close(gaschpimg)

    # GRAFICO desired profile

    profileimg, profileplt = plt.subplots(figsize=(20, 10))
    images, = profileplt.plot(loadlist, linestyle='-', color='blue')
    images, = profileplt.plot(tildelist, linestyle='-', color='green')
    images, = profileplt.plot(flattened_profile, linestyle='-', color='red')
    
    profileplt.legend(['Original Load', 'Final Load', 'Desired Profile'], fancybox=True, framealpha=0.5)
    
    plt.ylabel('Energy value (kW)')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=24)
    plt.grid(True)
    uchpimg = plt.savefig('results_offline_profile.png', dpi=200) 
    
    plt.close(gaschpimg)

    
if __name__ == '__main__':
    main(sys.argv[1:])