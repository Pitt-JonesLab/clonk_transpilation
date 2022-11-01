# %%
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from external.NuOp.parallel_two_qubit_gate_decomposition import *
from external.NuOp.gates_numpy import cnot_gate, fsim_gate, cphase_gate, xy_gate, get_gate_unitary_qiskit, iswap, fsim
from itertools import product
from qiskit.transpiler import PassManager
import sys
from src.utils.riswap_gates.riswap import RiSwapGate
import h5py
from tqdm import tqdm
#test

# %%
#don't change, would break previous data collection
#XXX
alpha_range = [2,3,4,5,6,7]
# # alpha_range = [5]
# gate_range = range(2,11)#9
#alpha_range = [1,2,3,4,5,6]
gate_range = range(2,9)#11
from qiskit.quantum_info import random_unitary

def collect_random2q_data(base_fidelity, N=15, mode="swap", fn=None):
    # alpha_range = [2,3,4,5,6,7]
    # # alpha_range = [5]
    # gate_range = range(2,9)#11
    
    base_fidelity = base_fidelity
    empty_flag = 0
    filename = f'data-archive2/data1_{mode}.h5' #f'data-archive2/data1_{mode}.h5' #f'data-archive/data1_{mode}.h5', #archive2 uses 2-7, archive3 uses 1-6
    #filename = f'src/benchmark_suite/data/data5_{mode}.h5'
    if fn is not None:
        filename = fn
    #load in previous data
    try:
        with h5py.File(filename, 'r') as h5f:
        
            #gate_error = h5f['random2q_gate_error'][:]
            decomp_error = h5f['decomp_error'][:]
            #fidelity_error = h5f['random2q_fidelity_error'][:]

            #backfill data
            gate_error = np.zeros(shape=(len(decomp_error), len(alpha_range), len(gate_range)))
            fidelity_error = np.zeros(shape=(len(decomp_error), len(alpha_range), len(gate_range)))
            for i in range(len(decomp_error)):
                for alpha_index, alpha in enumerate(alpha_range):
                    alpha = 1/alpha
                    for gate_index, gate_count in enumerate(gate_range):
                        gate_error[i][alpha_index][gate_index] = ((1-(alpha*(1-base_fidelity)))**gate_count)
                        fidelity_error[i][alpha_index][gate_index] = (decomp_error[i][alpha_index][gate_index])*gate_error[i][alpha_index][gate_index]

    except Exception:
        #case where data doesn't already exist
        empty_flag = 1
        decomp_error = []

    for n in tqdm(range(N-len(decomp_error))):

        # if not empty_flag and len(gate_error) >= N:
        #     break

        qc = QuantumCircuit(2)
        if mode == "random":
            qc.append(random_unitary(dims=(2,2)),[0,1])
        else:
            raise ValueError()
            #qc.append(SwapGate(), [0,1])
        dag = circuit_to_dag(qc)

        #new data for this iteration
        temp_gate_error = np.zeros(shape=(1, len(alpha_range), len(gate_range)))
        temp_decomp_error = np.zeros(shape=(1, len(alpha_range), len(gate_range)))
        temp_fidelity_error = np.zeros(shape=(1, len(alpha_range), len(gate_range)))

        for alpha_index, alpha in enumerate(alpha_range):
            alpha = 1/alpha
            for gate_index, gate_count in enumerate(gate_range):

                params = [[alpha]]
                gate_labels = [f'$iSwap^{alpha}$']
                gate_defs = [RiSwapGate]

                temp_gate_error[0][alpha_index][gate_index] = ((1-(alpha*(1-base_fidelity)))**gate_count)
            
                #run perfect if it doesn't already exist
                fid_2q = {(0,1):[1]}
                pgrp = ParallelGateReplacementPass(gate_defs, params ,fid_2q, fidelity_list_1q_gate=[1 for _ in range(54)], tol=1e-10, force_gate_count=gate_count)
                approx = pgrp.run(dag)
                temp_decomp_error[0][alpha_index][gate_index] = (pgrp.property_set["best_fid"])
                temp_fidelity_error[0][alpha_index][gate_index] = (temp_gate_error[0][alpha_index][gate_index])*temp_decomp_error[0][alpha_index][gate_index]

                #run noisy
                # fid_2q = {(0,1):[1-alpha*(1-base_fidelity)]}
                # pgrp = ParallelGateReplacementPass(gate_defs, params ,fid_2q, fidelity_list_1q_gate=[1 for _ in range(54)], tol=1e-10, force_gate_count=gate_count)
                # approx = pgrp.run(dag)
                # temp_fidelity_error[0][alpha_index][gate_index] = (pgrp.property_set["best_fid"])

                #these are equivalent - save some time and just calculate it using the previous values
                
                # print(f"{gate_error[-1]}, {decomp_error[-1]}, {fidelity_error[-1]}")

        #update data

        if empty_flag:
            gate_error = temp_gate_error
            decomp_error = temp_decomp_error
            fidelity_error = temp_fidelity_error
            empty_flag = 0
        else:
            gate_error = np.append(gate_error, temp_gate_error, axis=0)
            decomp_error = np.append(decomp_error, temp_decomp_error, axis=0)
            fidelity_error = np.append(fidelity_error, temp_fidelity_error, axis=0)

        #write back data after each iteration in case we end early
        with h5py.File(filename, 'a') as h5f:
            print(f"saving iter {n}")
            # delete old, differently sized dataset
            try:
                del h5f['gate_error'] 
                del h5f['decomp_error']
                del h5f['fidelity_error']
            except Exception:
                #don't need to delete if they don't exist
                pass
            h5f.create_dataset('gate_error', data=gate_error)
            h5f.create_dataset('decomp_error', data=decomp_error)
            h5f.create_dataset('fidelity_error', data=fidelity_error)
            
    return gate_error, decomp_error, fidelity_error


# %%
from scipy.stats import sem
# import h5py
# with h5py.File('data.h5', 'r') as h5f:
#     gate_error = h5f['random2q_gate_error'][:]
#     decomp_error = h5f['random2q_decomp_error'][:]
#     fidelity_error = h5f['random2q_fidelity_error'][:]

import matplotlib.pyplot as plt
plt.style.use(['science', 'no-latex'])

def create_plot(gate_error, decomp_error, fidelity_error):
    fig, axs = plt.subplots(1,len(gate_error[0]), sharey=True, sharex=True, figsize=(12, 4))
    for alpha_index in range(len(gate_error[0])):
        alpha = 1/alpha_range[alpha_index]
        gate_unit_time = [el*alpha for el in gate_range]
        axs[alpha_index].plot(gate_unit_time, np.average(gate_error, axis=0)[alpha_index], label="Gate Error", linestyle='--', marker='o')
        axs[alpha_index].errorbar(gate_unit_time, np.average(decomp_error, axis=0)[alpha_index], yerr=sem(decomp_error, axis=0)[alpha_index], label="Decomp Error", linestyle='--', marker='s')
        axs[alpha_index].errorbar(gate_unit_time, np.average(fidelity_error, axis=0)[alpha_index], yerr=sem(fidelity_error, axis=0)[alpha_index], label="Total Fidelity", marker='^')
        axs[alpha_index].set_xlabel("Gate Unit Time")
        axs[alpha_index].set_title(f"iSwap^(1/{1/alpha})")
    # for i, key in enumerate(np.max(np.average(fidelity_error, axis=0),axis=1)):
    #     axs[i].annotate(key, (i, frequency_list[key]))
    #     if i >= 3:
    #         break

    axs[-1].legend()
    axs[0].set_ylabel("Avg Fidelity")
    axs[0].set_yscale('logit')
    fig.tight_layout()
    fig.show()
    filename = "nuop_experiment"
    fig.savefig('{}.pdf'.format(filename), format="pdf", facecolor='white')

# %%
# gate_error, decomp_error, fidelity_error = collect_random2q_data(1-5e-2, N=25, mode="random")
# create_plot(gate_error, decomp_error, fidelity_error)

# %%
from scipy.stats import sem
def get_max(fidelity_error):
    max_list = []
    sem_list = []
    for alpha_index in range(len(fidelity_error[0])):
        best_over_templatelength = 0
        sem_temp = []
        for template_length_index in range(len(fidelity_error[0][0])):
                best_temp_average = []
                for n_repetition in range(len(fidelity_error)):
                    best_temp_average.append(fidelity_error[n_repetition][alpha_index][template_length_index])
                val = np.sum(best_temp_average)/len(fidelity_error)
                if val > best_over_templatelength:
                    best_over_templatelength = val
                    sem_temp = sem(best_temp_average)
        #print(best_over_templatelength)
        sem_list.append(sem_temp)
        max_list.append(best_over_templatelength)
    return max_list, sem_list

# %%
import itertools
marker = itertools.cycle(('o', '^', 's', 'd', 'v', '*')) 
color = itertools.cycle(("tab:blue", "tab:olive", "tab:purple", "tab:red", "tab:green", "tab:pink", "tab:orange", "tab:cyan"))
#color = itertools.cycle(("tab:green", "tab:pink", "tab:orange", "tab:cyan"))
# base_fidelity_list = [.97, .98, 1-10e-3,1-5e-3, 1-10e-4, 1]
# gate_error, decomp_error, fidelity_error = collect_random2q_data(1-10e-3, N=20, mode="random")
from scipy.stats import sem
def create_plot2(gate_error, decomp_error, fidelity_error, plot_bool, N=20, fn=None):
    plt.style.use(['science'])#, 'ieee'])
    SMALL_SIZE = 4
    MEDIUM_SIZE = 6
    BIGGER_SIZE = 12
    plt.rc("font", size=MEDIUM_SIZE+2)  # controls default text sizes
    plt.rc("axes", titlesize=MEDIUM_SIZE+2)  # fontsize of the axes title
    plt.rc("axes", labelsize=MEDIUM_SIZE + 1)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE + 2)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE + 2)  # fontsize of the tick labels
    plt.rc("legend", fontsize=MEDIUM_SIZE )  # legend fontsize
    plt.rc("figure", titlesize=MEDIUM_SIZE + 2)  # fontsize of the figure title
    plt.rc("lines", markersize=1.2, linewidth=.65)

    # fig = plt.figure()
    # gs = fig.add_gridspec(2,2)
    # ax1 = fig.add_subplot(gs[0, 0])
    # ax2 = fig.add_subplot(gs[0, 1])
    # ax3 = fig.add_subplot(gs[1, :])
    # axs = [ax1,ax2,ax3]

    if plot_bool:
        fig, axs = plt.subplots(1,2, figsize=(2,1.25), sharey=True,gridspec_kw={'width_ratios': [1,2]})
        for alpha_index in range(len(gate_error[0])):
                alpha = 1/alpha_range[alpha_index]
                set_color = next(color)
                set_marker = next(marker)
                #
                gate_unit_time = gate_range
                c = len([el for el in gate_unit_time if el <= 8])
                axs[0].errorbar(gate_unit_time[:c], [1-el for el in np.average(decomp_error, axis=0)[alpha_index][:c]], yerr=sem(decomp_error, axis=0)[alpha_index][:c], capsize=1.5, elinewidth=.5,  ecolor=set_color, label=r"$\sqrt[" + str(int(1/alpha))+ r"]{iSwap}$", marker=set_marker, color=set_color)
                #
                gate_unit_time = [el*alpha for el in gate_range]
                #gate_unit_time = gate_range
                #axs[1].plot(gate_unit_time, np.average(gate_error, axis=0)[alpha_index], label=f"Gate Error {alpha}", linestyle='--', marker='o')

                #cutting off values past 2 to make pulse duration plot look nicer
                c = len([el for el in gate_unit_time if el <= 2])
                c_bottom = len(gate_unit_time) - len([el for el in gate_unit_time if el >= 0])
                #c = len(gate_unit_time)
                axs[1].errorbar(gate_unit_time[c_bottom:c], [1-el for el in np.average(decomp_error, axis=0)[alpha_index][c_bottom:c]], yerr=sem(decomp_error, axis=0)[alpha_index][c_bottom:c], capsize=1.5, elinewidth=.5,  ecolor=set_color, label=r"$\sqrt[" + str(int(1/alpha))+ r"]{iSwap}$", marker=set_marker, color=set_color)
                #axs.errorbar(gate_unit_time, np.average(fidelity_error, axis=0)[alpha_index], yerr=sem(fidelity_error, axis=0)[alpha_index], label=f"Total Fidelity{alpha}", marker='^')
            #     axs[alpha_index].set_xlabel("Gate Unit Time")
                #axs[alpha_index].set_title(f"iSwap^(1/{1/alpha})")
        # for i, key in enumerate(np.max(np.average(fidelity_error, axis=0),axis=1)):
        #     axs[i].annotate(key, (i, frequency_list[key]))
        #     if i >= 3:
        #         break
        axs[0].set_yscale('log')
        #axs[1].set_xscale('log')
        axs[0].set_xlabel(r"Gate Count ($k$)")
        axs[1].set_xlabel(r"Pulse Duration ($k/n$)")
        fig.suptitle(r"$\sqrt[n]{iSwap}$ Expected Decomp Fidelity")
        #axs[0].legend(bbox_to_anchor=(2,-.2), ncol=2)
        handles, labels = axs[0].get_legend_handles_labels()
        #fig.legend(handles,labels,bbox_to_anchor=(.95,-.08),ncol=3)
        #axs[0].legend(bbox_to_anchor=(1.0,-.2), ncol=2)
        # axs[0].yaxis.set_major_locator(plt.LogitLocator(3))
        # axs[0].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        # axs[-1].legend()
        axs[0].set_ylabel(r"Avg Infidelity ($1-F_d$)")
        axs[0].set_xticks(range(2,9))
        axs[0].minorticks_on()
        axs[0].xaxis.set_tick_params(which='minor', bottom=False, top=False)
    else: #if plot_bool:
        fig, axs = plt.subplots(1,1, figsize=(2,1.15), sharey=True)
        ydata = []
        ysem = []
        base_fidelity_list = np.arange(.9, 1, .01)
        for bf in base_fidelity_list:
            gate_error, decomp_error, fidelity_error = collect_random2q_data(bf, N=N, mode="random", fn=fn)
            ydata.append(get_max(fidelity_error)[0])
            ysem.append(get_max(fidelity_error)[1])
            #axs.errorbar([bf]*len(alpha_range), get_max(fidelity_error)[0], yerr=get_max(fidelity_error)[1], capsize=1.5, elinewidth=.5,  ecolor='black', linestyle="-", marker=next(marker), label=bf,color=next(color))
        for i, n in enumerate(range(len(gate_error[0]))):
            alpha = 1/alpha_range[i]
            set_color = next(color)
            axs.errorbar(base_fidelity_list, [el[i] for el in ydata], yerr=[el[i] for el in ysem], capsize=1, elinewidth=.5,  ecolor=set_color, linestyle="-", marker=next(marker), label=r"$\sqrt[" + str(int(1/alpha))+ r"]{iSwap}$",color=set_color)
        #axs.set_xlabel(r"$\sqrt[x]{iSwap}$")
        axs.set_xlabel(r"$F_b(\texttt{iSwap})$")
        axs.invert_xaxis()
        axs.set_yscale('linear')
        axs.minorticks_on()
        axs.xaxis.set_tick_params(which='minor', bottom=False, top=False)
    # # axs[1].set_ylabel("Avg fidelity")
    # # legend = axs[1].legend(title="iSwap Fidelity", bbox_to_anchor=(1.25,-.22), ncol=2)
        axs.legend(bbox_to_anchor=(1.0,-.22), ncol=3)
    # # legend._legend_box.align = "bottoms"
    # axs.yaxis.set_major_locator(plt.MaxNLocator(4))
        axs.set_xticks(np.linspace(.9, 1, 5))
    # #axs[0].xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # axs[1].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    #     # axs[1].set_title(f"Random 2Q Fidelity vs nth root iswap")
    #axs.set_yscale('log')
        axs.set_ylabel(r"Avg Total Fidelity $F_t$")
    #axs.set_ylabel("Average Fidelity")
        axs.set_title(r"$\sqrt[n]{iSwap}$ Expected Total Fidelity")
    #axs.minorticks_off()
    #axs.set_ylabel("Average Infidelity")
    #axs.set_xticks = [2,3,4,5,6,7,8]
    #axs.minorticks_off()
    #fig.suptitle(f"Random 2Q Fidelity (N={N})")
    #plt.axes().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    #fig.tight_layout()
    fig.show()
    filename = "nuop_experiment"
    fig.savefig('{}.svg'.format(filename), format="svg", facecolor=None)



