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
import logging

logging.getLogger('pyomo.core').setLevel(logging.ERROR)

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

def get_info_from_results(results, info_string):
    i = str(results).lower().find(info_string.lower()) + len(info_string)
    value = ''
    while str(results)[i] != '\n':
        value = value + str(results)[i]
        i += 1
    return value

def run_online(time_slice, opt_func, offline_status):
    params = [time_slice, opt_func, offline_status]
    #print(params)
    main(params)

def main(argv):
    slice_size = 60 
    opt_func = "cost"
    
    if len(argv) != 3:
        print("Not enough arguments: using default values, 15 cost off")    
    else:
        slice_size = int(argv[0])
        opt_func = argv[1]
        #print(opt_func)

    sload_flag = 1
    suchp_flag = 1
    sgas_chp_flag = 1

    if argv[2] == 'off':
        sload_flag = 0
        suchp_flag = 0
        sgas_chp_flag = 0

    debug = False
    
    # Data preprocessing
    load_profiles_df = pd.read_excel("Summer_Load_Profiles.xlsx", header=None) + pd.read_excel("Winter_Load_Profiles.xlsx", header=None)
    pv_profiles_df = pd.read_excel("Summer_PV_Profiles.xlsx", header=None)
    uchp_profiles_df = pd.read_excel("Winter_uCHP_Profiles.xlsx", header=None)
    prices_df = pd.read_csv("pricesGME.csv", usecols=[1])

    # Adding noise
    load_profiles_df = load_profiles_df + np.random.normal(0, 0.1, [load_profiles_df.shape[0],load_profiles_df.shape[1]])
    load_profiles_df = load_profiles_df.clip(lower=0)

    pv_profiles_df = pv_profiles_df + np.random.normal(0, 0.1, [pv_profiles_df.shape[0],pv_profiles_df.shape[1]])
    pv_profiles_df = pv_profiles_df.clip(lower=0) # per fare in modo che non ci siano valori negativi
    
    prices_df = prices_df + abs(np.random.normal(0, 0.1, [prices_df.shape[0],prices_df.shape[1]]))
   
    scaled_load_df = change_scale(5, slice_size, load_profiles_df, debug)
    scaled_pv_df = change_scale(5, slice_size, pv_profiles_df, debug)
    scaled_prices_df = change_scale(60, slice_size, prices_df, debug)
    scaled_prices_df.columns =['prices']
    
    pod_list_conf = parse_config('config.conf')
    init_pods(pod_list_conf, scaled_load_df, scaled_pv_df)

    # definizione delle costanti     
    uchp_min = uchp_profiles_df.values.min() # kW
    uchp_max = uchp_profiles_df.values.max() # kW
    cuchp = 0.045
    cchp_gas = 0.039
    gas_chp_min = 0
    gas_chp_max = 3 
    eta = 0.9
    gin_min = 0
    gout_min = 0
    gin_max = 3
    gout_max = 3 
    sin_max = 2.5
    sout_max = 2.5
    charge_init = 3
    charge_max = 4
    
    T = int(scaled_load_df[0].count()) # in questo caso 96
    tildeload_df = pd.DataFrame()
    sload_df = pd.DataFrame()
    suchp_df = pd.DataFrame()
    sgas_chp_df = pd.DataFrame()

    fixed_index_list = []
    fixed_time_list = range(T)
    previous_charge = [None] * len(pod_list_conf)
    previous_uchp = [None] * len(pod_list_conf)
    previous_gaschp = [None] * len(pod_list_conf)

    # liste per salvare l'output ad ogni ciclo di t
    tildeloadlist = []
    pvlist = []
    tildeuchplist = []
    tildegaschplist = []
    gridINlist = []
    gridOUTlist = []
    stINlist = []
    stOUTlist = []
    tot_time = []

    # pod
    for pod in pod_list_conf:
        fixed_index_list.append(pod[0])

    # pv
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
    
    # se considero la fase offline, vado a cercare i valori shiftati del chp, altrimenti metto il df tutto a zero
    if uchp_index_list:
        if suchp_flag == 1:
            suchp_df = pd.read_csv('suchp.csv')
        else:
            for t in fixed_time_list:
                for i in uchp_index_list:
                    suchp_df.loc[t,str(i)] = 0

    # gas_chp
    gas_chp_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'gas_chp':
                gas_chp_index_list.append(pod[0])
    
    if gas_chp_index_list:
        if sgas_chp_flag == 1:
            sgas_chp_df = pd.read_csv('sgas_chp.csv')
        else:
            for t in fixed_time_list:
                for i in gas_chp_index_list:
                    sgas_chp_df.loc[t,str(i)] = 0
        
    # load   
    load_index_list = []
    for pod in pod_list_conf:
        for el in pod[2]:
            if el == 'load':
                load_index_list.append(pod[0])

    if load_index_list:
        if sload_flag == 1:
            sload_df = pd.read_csv('sload.csv')
        else:
            for t in fixed_time_list:
                for i in load_index_list:
                    sload_df.loc[t,str(i)] = 0

    # inizializzo la scrittura del file di output

    f = open("output_online.txt", "a")
    
    obj_value_list = []

    ### INIZIO MODELLO - PER OGNI T
   
    for t in fixed_time_list:

        model = ConcreteModel()
       
        # variabili sempre presenti
        model.Pgin = Var(fixed_index_list, domain = NonNegativeReals)
        model.Pgout = Var(fixed_index_list, domain = NonNegativeReals)
            
        # variabili dipendenti dalla costruzione del pod
        # charge
        charge_index_list = []
        for pod in pod_list_conf:
            for el in pod[2]:
                if el == 'storage':
                    charge_index_list.append(pod[0]) #prendiamo la lista dei pod, e controlliamo quali hanno st, quindi aggiungiamo il loro indice a charge_index_list
        
        if charge_index_list: #se la lista non è vuota
            model.charge = Var(charge_index_list, domain = NonNegativeReals)
            model.Psin = Var(charge_index_list, domain = NonNegativeReals)
            model.Psout = Var(charge_index_list, domain = NonNegativeReals)
        
        # uchp
        if uchp_index_list:
            model.Puchp = Var(uchp_index_list)
            model.tildeuchp = Var()

        # gas_chp
        if gas_chp_index_list:
            model.Pgas_chp = Var(gas_chp_index_list)
            model.tildegas_chp = Var()

        load_index_norm = []
        for el in load_index_list:
            load_index_norm.append(el%100)
        
        reduced_scaled_load_df = scaled_load_df[load_index_norm] # andiamo a prendere da load_df solo le colonne dei pod che effettivamente ci servono - e hanno il load
        # In questo modo noi preleviamo le colonne corrispondenti tra loro per la somma
        # a prescindere dall'indice; ciò dovrebbe coprirci anche nei casi in cui abbiamo
        # più pod con più load: le colonne saranno sempre disposte sempre nello stesso ordine
        # tra i due df
        reduced_scaled_load_df.columns = load_index_list
        #print(reduced_scaled_load_df)
                
        for col1, col2, i in zip(reduced_scaled_load_df.columns,sload_df.columns,load_index_list):
            # print(reduced_scaled_load_df[col1]) # colonna del primo, a prescindere dall'indice
            # print(sload_df[col2]) # colonna del secondo a prescindere dall'indice
            # print(i) # indice corretto di riferimento per il df finale sommato
            array = reduced_scaled_load_df[col1].values + sload_df[col2].values
            tildeload_df[i] = array
        
        tildeload = tildeload_df[load_index_list].sum(axis=1).clip(lower=0).values.tolist()
                   
        def objective(model):
            result = 0
            
            for i, pod in enumerate(pod_list_conf):
                if opt_func == "cost":
                    result += model.Pgin[i]*scaled_prices_df['prices'].values.tolist()[t] + model.Pgout[i]*scaled_prices_df['prices'].values.tolist()[t]
                    if 'uchp' in pod[2]:
                        result += cuchp*model.tildeuchp
                    if 'gas_chp' in pod[2]:
                        result += cchp_gas*model.tildegas_chp
                    if 'storage' in pod[2]:
                        result += model.Psout[i]*scaled_prices_df['prices'].values.tolist()[t]
                elif opt_func == "grid":
                    result += model.Pgin[i]*scaled_prices_df['prices'].values.tolist()[t] + model.Pgout[i]*scaled_prices_df['prices'].values.tolist()[t]
                
            return result                

        model.OBJ = Objective(rule=objective)   

        #### CONSTRAINTS

        # UCHP:

        if uchp_index_list:
            model.bound_uchp = ConstraintList()
            model.bound_tildeuchp = ConstraintList()
            model.bound_time_uchp = ConstraintList()

        for i in uchp_index_list:
            model.bound_uchp.add(inequality(uchp_min, model.tildeuchp, uchp_max))
        
        if uchp_index_list:
            left_side = model.tildeuchp
            right_side = 0
            for i in uchp_index_list:
                right_side += model.Puchp[i] + suchp_df[str(i)].values.tolist()[t]
            model.bound_tildeuchp.add(left_side == right_side)

        if uchp_index_list:
            multipl_constant = int(60/slice_size)
            for i in uchp_index_list:
                if t in range(0*multipl_constant+1, 4*multipl_constant) and t < 4*multipl_constant - 1:
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)
                                        
                if t in range(4*multipl_constant, 8*multipl_constant) and t < 8*multipl_constant - 1:
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)

                if t in range(8*multipl_constant, 12*multipl_constant) and t < 12*multipl_constant - 1:
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)

                if t in range(12*multipl_constant, 16*multipl_constant) and t < 16*multipl_constant - 1:    
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)

                if t in range(16*multipl_constant, 20*multipl_constant) and t < 20*multipl_constant - 1:
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)

                if t in range(20*multipl_constant, 24*multipl_constant) and t < 24*multipl_constant - 1:
                    model.bound_time_uchp.add( previous_uchp[i] == model.tildeuchp)

        #multipl_constant = int(60/slice_size)
            
        # GAS_CHP:

        if gas_chp_index_list:
            model.bound_gaschp = ConstraintList()
            model.bound_tildegaschp = ConstraintList()
            model.bound_time_gaschp = ConstraintList()

        for i in gas_chp_index_list:
            model.bound_gaschp.add(inequality(gas_chp_min, model.tildegas_chp, gas_chp_max))
        
        if gas_chp_index_list:
            left_side = model.tildegas_chp
            right_side = 0
            for i in gas_chp_index_list:
                right_side += model.Pgas_chp[i] + sgas_chp_df[str(i)].values.tolist()[t]
            model.bound_tildegaschp.add(left_side == right_side)

        if gas_chp_index_list:
            multipl_constant = int(60/slice_size)
            for i in gas_chp_index_list:
                if t in range(0*multipl_constant+1, 4*multipl_constant) and t < 4*multipl_constant - 1:
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)
                                        
                if t in range(4*multipl_constant, 8*multipl_constant) and t < 8*multipl_constant - 1:
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)

                if t in range(8*multipl_constant, 12*multipl_constant) and t < 12*multipl_constant - 1:
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)

                if t in range(12*multipl_constant, 16*multipl_constant) and t < 16*multipl_constant - 1:    
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)

                if t in range(16*multipl_constant, 20*multipl_constant) and t < 20*multipl_constant - 1:
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)

                if t in range(20*multipl_constant, 24*multipl_constant) and t < 24*multipl_constant - 1:
                    model.bound_time_gaschp.add( previous_gaschp[i] == model.tildegas_chp)
                    
        #multipl_constant = int(60/slice_size)
        #for i in gas_chp_index_list:
            #model.bound_tildegaschp.add( previous_gaschp[i] == model.Pgas_chp[i])
                
        # STORAGE:
        
        if charge_index_list:
            model.bound_charge = ConstraintList()

        for i in charge_index_list:
            model.bound_charge.add(model.Psin[i] <= sin_max)
            model.bound_charge.add(model.Psout[i] <= sout_max)

            #constraint per l'istante iniziale
            if t == 0:
                model.bound_charge.add(model.charge[i] == charge_init)
                model.bound_charge.add(model.charge[i] <= charge_max)
                model.bound_charge.add(model.charge[i] >= 0)
                
                model.bound_charge.add(model.Psin[i] <= charge_max - charge_init)
                model.bound_charge.add(model.Psout[i] <= charge_init)
            else:               
                model.bound_charge.add(model.charge[i] == previous_charge[i] - eta*model.Psin[i] + eta*model.Psout[i])
                
                model.bound_charge.add(model.charge[i] <= charge_max)
                model.bound_charge.add(model.charge[i] >= 0)
                model.bound_charge.add(model.Psin[i] <= charge_max - previous_charge[i])
                model.bound_charge.add(model.Psout[i] <= previous_charge[i])
            
        # GRID:
        
        model.bound_gin = ConstraintList()
        model.bound_gout = ConstraintList()
        for i, pod in enumerate(pod_list_conf):
            model.bound_gin.add(inequality(gin_min, model.Pgin[i], gin_max ))
            model.bound_gout.add(inequality(gout_min, model.Pgout[i], gout_max ))

        # BILANCIAMENTO:
        # Potrebbe contenere un termine relativo ad un componente load 

        model.bound_tildeload = ConstraintList()
        
        right_side = 0
        left_side = tildeload[t]
        for i, pod in enumerate(pod_list_conf): 
            right_side += model.Pgin[i] - model.Pgout[i] 
            if 'uchp' in pod[2]:
                right_side += model.Puchp[i] + suchp_df[str(i)].values.tolist()[t]
            if 'gas_chp' in pod[2]:
                right_side += model.Pgas_chp[i] + sgas_chp_df[str(i)].values.tolist()[t]
            if 'storage' in pod[2]:
                right_side += model.Psin[i] - model.Psout[i]
            if 'pv' in pod[2]:
                right_side += pod[3]['pv'].values.tolist()[t]
            
        model.bound_tildeload.add(left_side == right_side)

        #model.pprint()
        
        opt = SolverFactory('gurobi')
        results = opt.solve(model, tee=True) 

        # in alternativa model.load(results)
        model.solutions.store_to(results)
        #results.write()

        # per salvare il valore dell'iterazione precedente di charge, per usarlo nel constraint
        for i, pod in enumerate(pod_list_conf):
            if 'storage' in pod[2]:
                previous_charge[i] = model.charge[i].value

        for i, pod in enumerate(pod_list_conf):
            if 'uchp' in pod[2]:
                previous_uchp[i] = model.tildeuchp.value
                #print(previous_uchp[i])
            if 'gas_chp' in pod[2]:
                previous_gaschp[i] = model.tildegas_chp.value
                #print(previous_gaschp[i])   

        '''# per salvare tutti i valori delle variabili di ogni pod
        # PER OGNI POD i:
        #       var_1[i] ... var_N[i]
        # 0      valore  ...  valore
        # 1      valore  ...  valore
        # ...    valore  ...  valore
        # T      valore  ...  valore
        # 
        # PER COSTRUIRLI:
        # - Iteriamo ad ogni t, quindi ad ogni t noi possiamo costruire già tante strutture quanti sono i pod
        #   e in particolare aggiungere una riga ad ogni t.
        # - Per fare ciò ci serviranno dei df di appoggio (uno per ogni pod), che istanziamo all'inizio del programma
        #   e riempiamo alla fine di ogni iterazione in T.
        # - Alla fine del ciclo principale in T, salveremo (in un ciclo ausiliario) tutti questi df come csv.

        for i, pod in enumerate(pod_list_conf):
            labels = []
            row_as_list = []
            # temp_df = temp_df.append(model.Pgin[i], model.Pgout[i])
            labels.append('Pgin_{}'.format(pod[0]))
            labels.append('Pgout_{}'.format(pod[0]))
            row_as_list.append(model.Pgin[i].value)
            row_as_list.append(model.Pgout[i].value)
            if 'chp' in pod[2]:
                # temp_df = temp_df.append(model.Pchp[i])
                labels.append('Pchp_{}'.format(pod[0]))
                row_as_list.append(model.Pchp[i].value)
            if 'storage' in pod[2]:
                # temp_df = temp_df.append(model.Sout[i], model.Sin[i])
                labels.append('Psin_{}'.format(pod[0]))
                labels.append('Psout_{}'.format(pod[0]))
                row_as_list.append(model.Psin[i].value)
                row_as_list.append(model.Psout[i].value)
            if 'pv' in pod[2]:
                # temp_df = temp_df.append(model.Ppv[i])
                labels.append('Ppv_{}'.format(pod[0]))
                row_as_list.append(pod[3]['pv'].values.tolist()[t])
            if 'load' in pod[2]:
                # temp_df = temp_df.append(model.Sload[i]) 
                labels.append('Pload_{}'.format(pod[0]))
                row_as_list.append(pod[3]['load'].values.tolist()[t])
            
            row_as_series = pd.Series(row_as_list)

            pod[4] = pod[4].append(row_as_series, ignore_index = True)
            
            if t == T-1:
                pod[4].columns = labels
                pod[4].to_csv('pod_{}.csv'.format(pod[0]), index=False)
                print("PRINTING RESULTS FOR POD " + str(i))
                print(pod[4])'''
        
        # TEMPO DI RISOLUZIONE   
        solver_time = get_info_from_results(results, 'Time: ')
        tot_time.append(float(solver_time))

        obj_value_list.append(float(model.OBJ()))
                            
        # CONTROLLO SULLA TERMINAZIONE
        if (results.solver.termination_condition == TerminationCondition.optimal):
            print("Modello risolto correttamente")
        elif (results.solver.termination_condition == TerminationCondition.infeasible):
            print("La condizione di terminazione è INFEASIBLE")
        else:
            print("Errore: Solver Status", results.solver.status)

        
        '''stdout_backup = sys.stdout

        with open('results_online_step_{}.yml'.format(t), 'a') as f:
            sys.stdout = f
            results.write()

        sys.stdout = stdout_backup'''
    
        # PLOT OUTPUT

        if pv_index_list:
            acc = 0
            for i in pv_index_list:
                acc += pod_list_conf[i][3]['pv'].values.tolist()[t]
            pvlist.append(acc)


        if load_index_list:
            tildeloadlist.append(tildeload[t])
        
        if uchp_index_list:
            tildeuchplist.append(model.tildeuchp.value)
        
        if gas_chp_index_list:
            tildegaschplist.append(model.tildegas_chp.value)

        acc = 0
        for i in range(len(pod_list_conf)):
            acc += model.Pgin[i].value
        gridINlist.append(acc)

        acc = 0
        for i in range(len(pod_list_conf)):
            acc += model.Pgout[i].value
        gridOUTlist.append(-acc)
        
        if charge_index_list:
            acc = 0
            for i in charge_index_list:
                acc += model.Psin[i].value
            stINlist.append(acc)
        
        if charge_index_list:
            acc = 0
            for i in charge_index_list:
                acc += model.Psout[i].value
            stOUTlist.append(-acc)
        print(t)
    # Fine ciclo

    tot_time_sum = sum(tot_time)
    #print("SOLVER TIME: " + str(tot_time_sum))
    #print(obj_value_list)
    
    f.write("Components: {}\n".format(len(pv_index_list)+len(load_index_list)+len(gas_chp_index_list)+len(uchp_index_list)+len(charge_index_list)))
    f.write("    # Pv: {}\n".format(len(pv_index_list)))
    f.write("    # Load: {}\n".format(len(load_index_list)))
    f.write("    # Gas Chp: {}\n".format(len(gas_chp_index_list)))
    f.write("    # Uchp: {}\n".format(len(uchp_index_list)))
    f.write("    # Storage: {}\n".format(len(charge_index_list)))
    f.write("SOLVER TIME:" + str(tot_time_sum) + "\n")
    f.write("OBJ function {}:".format(argv[1]) + "\n")
    f.write("MIN OBJ: {}, MAX OBJ: {}, MEAN OBJ: {}\n".format(min(obj_value_list),max(obj_value_list),np.mean(obj_value_list)))
    f.write("TOTAL OBJ: {}\n".format(sum(obj_value_list)))
    f.write("FULL LIST: \n")
    for el in obj_value_list:
        if el < 0:
            f.write("     {}\n".format(str(el)))
        else:
            f.write("      {}\n".format(str(el)))
    f.write("\n")
    f.close()
   
    # GRAFICO PV + LOAD
    resultimg, result = plt.subplots(figsize=(15, 10))
    images, = result.plot(tildeloadlist, linestyle='-', color='brown', label='Load')
    images, = result.plot(pvlist, linestyle='-', color='green', label='PV')
    #images, = result.plot(loadlist, linestyle='--', color='red', label='Load')
    #images, = result.plot(sloadlist, linestyle='--', color='purple', label='Shift')
    
    #images, = result.plot([sum(x) for x in zip(gridINlist,gridOUTlist)], linestyle='-', color='#3a55a1', linewidth=2,label='Grid')  
    #images, = result.plot(tildelist2, linestyle='-', color='orange', label='Tilde2')
    
    tilde = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildeloadlist)
    result.fill_between(np.arange(0.0, 96.0, 0.1), tilde, 0, facecolor='red', alpha=0.5)

    if pv_index_list:
        pv = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, pvlist)
        result.fill_between(np.arange(0.0, 96.0, 0.1), pv, 0, facecolor='green', alpha=0.5)
    
    result.legend()
      
    plt.ylabel('Energy value (kW)')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=24)
    plt.grid(True)
    resultimg = plt.savefig('results1_online_{}.png'.format(argv[1]), dpi=200) 

    plt.close(resultimg)

    # GRAFICO ALTRI CONTRIBUTI
    result2img, result2 = plt.subplots(figsize=(15, 10))

    if uchp_index_list:
        images2, = result2.plot(tildeuchplist, linestyle='-', color='magenta', label= 'uCHP')
    if gas_chp_index_list:
        images2, = result2.plot(tildegaschplist, linestyle='-', color='purple', label='GasCHP')
    if charge_index_list:
        images2, = result2.plot(stOUTlist, linestyle='-', color='#b21e00', linewidth=2, label='StOUT')
        images2, = result2.plot(stINlist, linestyle='-', color='#fa7e25', linewidth=2, label='StIN')
        #images, = result.plot([sum(x) for x in zip(stINlist,stOUTlist)], linestyle='-', color='#fa7e25', linewidth=2, label='Storage')
    images2, = result2.plot(gridOUTlist, linestyle='-', color='#4f2bb3', linewidth=2, label='GridOUT')
    images2, = result2.plot(gridINlist, linestyle='-', color='#428db3', linewidth=2, label='GridIN')

    '''gridin = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, gridINlist)
    result2.fill_between(np.arange(0.0, 96.0, 0.1), gridin, 0, facecolor='#428db3', alpha=0.5)

    gridout = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, gridOUTlist)
    result2.fill_between(np.arange(0.0, 96.0, 0.1), gridout, 0, facecolor='#4f2bb3', alpha=0.5)'''

    if uchp_index_list:
        uchp = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildeuchplist)
        result2.fill_between(np.arange(0.0, 96.0, 0.1), uchp, 0, facecolor='purple', alpha=0.5)
    
    if gas_chp_index_list:
        gaschp = np.interp(np.arange(0.0, 96.0, 0.1), fixed_time_list, tildegaschplist)
        result2.fill_between(np.arange(0.0, 96.0, 0.1), gaschp, 0, facecolor='violet', alpha=0.5)

    result2.legend()
      
    plt.ylabel('Energy value (kW)')
    plt.xlabel('Time instant')
    plt.locator_params(axis='x', nbins=24)
    plt.grid(True)
    result2img = plt.savefig('results2_online_{}.png'.format(argv[1]), dpi=200) 

    plt.close(result2img)

    # GRAFICO A CIAMBELLA CON PERCENTUALI
    
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(aspect="equal"))
    
    data = []
    labels = []
    if pv_index_list:
        data.append(sum(pvlist))
        labels.append('PV')
    if uchp_index_list:
        data.append(sum(tildeuchplist))
        labels.append('uCHP')
    if gas_chp_index_list:
        data.append(sum(tildegaschplist))
        labels.append('GasCHP')
    data.append(abs(sum([sum(x) for x in zip(gridINlist,gridOUTlist)])))
    labels.append('Grid')

    if charge_index_list:
        data.append(abs(sum([sum(x) for x in zip(stINlist,stOUTlist)])))
        labels.append('Storage')
    
    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.1f}%\n({:d} kWh)".format(pct, absolute)

    wedges, texts, autotexts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40, autopct=lambda pct: func(pct, data), pctdistance=0.8, textprops={'color': "w", 'fontsize': 6})

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
        ax.annotate(labels[i], xy=(x, y), xytext=(1*np.sign(x), 1.3*y),
                    horizontalalignment=horizontalalignment, **kw, size=7)
       
    ax = plt.savefig('pie_online_{}.png'.format(argv[1]), dpi=200) 

    plt.close(ax)
     
if __name__ == '__main__':
    main(sys.argv[1:])
