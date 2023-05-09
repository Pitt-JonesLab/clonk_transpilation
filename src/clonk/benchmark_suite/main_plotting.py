# %%
# %%
# make a plot :)
import matplotlib.pyplot as plt

# plt.style.use(["science", "ieee"])
# plt.plot([0,0], [1,1]);
# plt.style.use(["science", "ieee"])
# I'm not sure why but theon't get updated until after running twice, so monkey fix like this?? styles d


def benchmark(
    backends,
    circuit_generator,
    q_range=None,
    continuously_save=False,
    overwrite=False,
    repeat=3,
):
    for iteration in range(repeat):
        benchmark_foo(
            iteration,
            backends,
            circuit_generator,
            q_range,
            continuously_save,
            overwrite,
        )


def benchmark_foo(
    i,
    backends,
    circuit_generator,
    q_range=None,
    continuously_save=False,
    overwrite=False,
):
    iteration = str(i)
    # override qrange if provided
    if q_range is None:
        q_range = circuit_generator.q_range

    # check if data dicts are empty
    for backend in backends:
        if iteration not in backend.data.keys():
            backend.data[iteration] = {}
        if circuit_generator.label not in backend.data[iteration].keys():
            backend.data[iteration][circuit_generator.label] = {}
            backend.data[iteration][circuit_generator.label]["duration"] = {}
            backend.data[iteration][circuit_generator.label]["preswap_gate_count"] = {}
            backend.data[iteration][circuit_generator.label]["gate_count"] = {}
            backend.data[iteration][circuit_generator.label][
                "preswap_gate_count_crit"
            ] = {}
            backend.data[iteration][circuit_generator.label]["layout_score"] = {}
            backend.data[iteration][circuit_generator.label]["edge_frequency"] = {}
    print(f"Starting benchmark for {circuit_generator.label}")

    # outer loop over circuit since this may take long time to generate
    for q in q_range:
        # create new variable sized lambda circuit
        # wait to build circuit (may be costly), if we end up not needing it for any backend
        qc = None
        if overwrite:
            qc = circuit_generator.circuit_lambda(q)

        for backend in backends:
            # condition to skip
            if not overwrite:
                # convert to int because if loaded from json key will be a string
                if q in [
                    int(k)
                    for k in backend.data[iteration][circuit_generator.label][
                        "preswap_gate_count"
                    ].keys()
                ]:
                    continue

            # another condition to skip if size is invalid
            if backend.backend.num_qubits < q:
                continue

            # resolve wait
            if qc is None:
                qc = circuit_generator.circuit_lambda(q)

            # logging.info(f"Transpiler qc{q} for {backend.label}")
            print(f"Transpiler qc{q} for {backend.label}")
            backend.pass_manager.run(qc)

            # save data to dict
            # might be empty if not decomposing swaps, this comment is deprecated
            # if (
            #     "duration_longest_path_length"
            #     in backend.pass_manager.property_set.keys()
            # ):

            # switch to using standard count ops method now w/o pulse normalization arg
            duration = backend.pass_manager.property_set["count_ops_longest_path"]
            backend.data[iteration][circuit_generator.label]["duration"][
                str(q)
            ] = duration

            gate_count = backend.pass_manager.property_set["preswap_count_ops"]
            backend.data[iteration][circuit_generator.label]["preswap_gate_count"][
                str(q)
            ] = gate_count

            gate_count_critical_path = backend.pass_manager.property_set[
                "preswap_count_ops_longest_path"
            ]
            backend.data[iteration][circuit_generator.label]["preswap_gate_count_crit"][
                str(q)
            ] = gate_count_critical_path

            gate_count_post_decomp = backend.pass_manager.property_set["count_ops"]
            backend.data[iteration][circuit_generator.label]["gate_count"][
                str(q)
            ] = gate_count_post_decomp

            layout_score = backend.pass_manager.property_set["layout_score"]
            backend.data[iteration][circuit_generator.label]["layout_score"][
                str(q)
            ] = float(layout_score)

            frequency_list = backend.pass_manager.property_set["edge_frequency"]
            backend.data[iteration][circuit_generator.label]["edge_frequency"][
                str(q)
            ] = frequency_list

            # for long tests, may want to save more regularly in case exit early
            if continuously_save:
                backend.save_json()

    for backend in backends:
        # save dict to json
        backend.save_json()


# %%
# !pip install SciencePlots
# import matplotlib.pyplot as plt
# plt.style.reload_library()
# plt.style.use(['science','no-latex'])


# %%
def plot_wrap(backends, circuit_label_list, motivation=False, plot_average=True):
    # fig, axs = plt.subplots(len(circuit_label_list),4, figsize=(24,24))
    height = 5
    if 1 or motivation:
        height = 2.5
    fig = plt.figure(constrained_layout=True, figsize=(7.16, height))
    # fig = plt.figure(constrained_layout=True, figsize=(4.5, 3.75))
    # plt.style.use(["science"])
    SMALL_SIZE = 4
    MEDIUM_SIZE = 6
    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=MEDIUM_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=MEDIUM_SIZE + 4)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE + 2)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE + 2)  # fontsize of the tick labels
    plt.rc("legend", fontsize=MEDIUM_SIZE + 2)  # legend fontsize
    plt.rc("figure", titlesize=MEDIUM_SIZE + 4)  # fontsize of the figure title
    plt.rc("lines", markersize=1.8, linewidth=0.75)

    if 1 or motivation:
        nrows = 2
    else:
        nrows = 4
    axs = fig.subplots(ncols=len(circuit_label_list), nrows=nrows)
    i = 0
    for circuit_label in circuit_label_list:
        ax = plot(
            backends,
            circuit_label,
            duration=2,
            subfig=axs,
            first=(i == 0),
            index=i,
            motivation=motivation,
            plot_average=plot_average
            # last=(i + 1 == len(circuit_label_list)),
        )
        i += 1
        circuit_label = circuit_label.replace("_", " ")
        if circuit_label == "QAOA Vanilla":
            circuit_label = "QAOA"
        ax.set_xlabel(f"{circuit_label}", y=0)
    # for ax, row in zip(ax[:,0], subfigs):
    #     ax.set_ylabel(row, rotation=0, size='large')
    fig.align_ylabels(axs)
    handles, labels = ax.get_legend_handles_labels()

    # patch labels
    def fix_labels(labels):
        for index, label in enumerate(labels):
            if "small" in label:
                label = label[:-6]
            if label == "Heavy-Hex-cx":
                labels[index] = "Heavy-Hex" + ("-CX" if not motivation else "")
            if label == "Hex-Lattice-cx":
                labels[index] = "Hex-Lattice" + ("-CX" if not motivation else "")
            if label == "Lattice+AltDiagonals-cx":
                labels[index] = "Lattice+AltDiagonals" + (
                    "-CX" if not motivation else ""
                )
            if label == "Square-Lattice-syc":
                labels[index] = "Square-Lattice" + ("-SYC" if not motivation else "")
            if label == "Modular-riswap":
                labels[index] = "Tree" + (r"-$\sqrt{iSWAP}$" if not motivation else "")
            if label == "Modular-RR3-riswap":
                labels[index] = "Tree-I" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "Hypercube-riswap":
                labels[index] = "Hypercube" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "HypercubeSNAIL-(0, 0)-riswap":
                labels[index] = "Corral$_{1,1}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "HypercubeSNAIL-(0, 1)-riswap":
                labels[index] = "Corral$_{1,2}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "Corral-8-(0, 0)-riswap":
                labels[index] = "Corral$_{1,1}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "Corral-8-(0, 1)-riswap":
                labels[index] = "Corral$_{1,2}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "Corral-42-(0, 0)-riswap":
                labels[index] = "Corral$_{1,1}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )
            if label == "Corral-42-(0, 1)-riswap":
                labels[index] = "Corral$_{1,2}$" + (
                    r"-$\sqrt{iSWAP}$" if not motivation else ""
                )

        if "Non-Swap Gate Count" in labels:
            temp_index = labels.index("Non-Swap Gate Count")
            temp_handle = handles.pop(temp_index)
            handles.insert(0, temp_handle)
            temp_label = labels.pop(temp_index)
            labels.insert(0, temp_label)

        return labels

    labels = fix_labels(labels)

    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.01),
        markerscale=2,
    )
    # savefig
    # filename = f"images/data1"
    # import os

    # i = 0
    # while os.path.exists("{}{:d}.pdf".format(filename, i)):
    #     i += 1
    # #fig.savefig("{}{:d}.pdf".format(filename, i), format="pdf", facecolor="white")
    # fig.savefig("{}{:d}.svg".format(filename, i), format="svg", facecolor='None')


# %%
import numpy as np


def plot(
    backends,
    circuit_label,
    duration=0,
    subfig=None,
    first=False,
    index=0,
    motivation=False,
    plot_average=True,
):
    def mark(backend_label):
        if "Modular" in backend_label:
            if "RR" in backend_label:
                return "p"
            return "*"
        if "Google" in backend_label or "Square" in backend_label:
            return "s"
        if "IBM" in backend_label or "Heavy" in backend_label:
            return "h"
        if "Hex-Lattice" in backend_label:
            return "^"
        if "AltDiagonals" in backend_label:
            return "x"
        if "SNAIL" in backend_label or "Corral" in backend_label:
            if "(0, 1)" in backend_label:
                return "D"
            return "8"
        if "Hypercube" in backend_label:
            return "o"
        pass

    def color_map(backend_label):
        if "Modular" in backend_label:
            if "RR" in backend_label:
                return "tab:olive"
            return "tab:green"
        if "Google" in backend_label or "Square" in backend_label:
            return "tab:red"
        if "IBM" in backend_label or "Heavy" in backend_label:
            return "tab:blue"
        if "Hex-Lattice" in backend_label:
            return "tab:cyan"
        if "AltDiagonals" in backend_label:
            return "tab:orange"
        if "SNAIL" in backend_label or "Corral" in backend_label:
            if "(0, 1)" in backend_label:
                return "tab:pink"
            if "(0, 2)" in backend_label:
                return "tab:gray"
            if "(1, 2)" in backend_label or "split" in backend_label:
                return "black"
            return "tab:purple"
        if "Hypercube" in backend_label:
            return "tab:brown"
        pass

    if subfig is None:
        if duration == 2:
            fig, (ax2, ax3, ax4, ax1) = plt.subplots(1, 4, figsize=(24, 8))
        else:
            raise NotImplementedError
    else:
        # axs = subfig.subplots(nrows=4, ncols=1)
        ax2 = subfig[0][index]
        ax3 = subfig[1][index]
        if not motivation:
            pass
            # ax4 = subfig[2][index]
            # ax1 = subfig[3][index]
        if 1 or motivation:
            ax_list = [ax2, ax3]
        else:
            ax_list = [ax2, ax3, ax4, ax1]
        for ax in ax_list:
            # ax.xaxis.set_major_locator(plt.MaxNLocator(3))
            ax.yaxis.set_major_locator(plt.MaxNLocator(3))
            ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    # elif duration==1:
    #     fig, (ax1) = plt.subplots(1,1, figsize=(12,8))
    # else:
    #     fig, (ax2, ax3) = plt.subplots(1,2, figsize=(24,8))

    for backend_i, backend in enumerate(backends):
        if circuit_label in backend.data["0"].keys():
            if motivation:
                # total swap gates
                x = backend.data["0"][circuit_label]["preswap_gate_count"].keys()
                x = [int(el) for el in list(x)]
                y_best = np.ones(len(x)) * np.inf
                y_average = np.zeros(len(x))
                # XXX monkey patch :(
                # for iter_key in backend.data.keys():
                keys = [el for el in backend.data.keys() if el.isdigit()]
                for iter_key in keys:
                    y = backend.data[iter_key][circuit_label][
                        "preswap_gate_count"
                    ].values()
                    x, y = zip(*zip(x, y))
                    y = [el["swap"] if "swap" in el.keys() else 0 for el in y]
                    # XXX monkey patch
                    x = list(x)
                    y = list(y)
                    if len(x) > 10:
                        for val in [4, 6, 10, 12, 14]:
                            if val in x:
                                del_index = x.index(val)
                                x.pop(del_index)
                                y.pop(del_index)

                    x, y = zip(*sorted(zip(x, y)))

                    for index, el in enumerate(y):
                        if y_best[index] > el:
                            y_best[index] = el
                        y_average[index] += el
                y_average /= len(keys)
                y_average = y_average[0 : len(x)]
                if plot_average:
                    y = y_average
                else:
                    y = y_best
                ax2.plot(
                    x,
                    y,
                    marker=mark(backend.label),
                    label=backend.label,
                    color=color_map(backend.label),
                )

                if backend_i == 0:
                    pass
                    # skip for now
                    # monkey patch in a thing which prints the non swap gates
                    # from qiskit import transpile
                    # from circuit_suite import circuits
                    # y = [transpile(circuits[circuit_label].circuit_lambda(xi), basis_gates=['u', 'cx']).count_ops()['cx'] for xi in x]
                    # ax2.plot(x, y, marker='.', linestyle='-.', label="Non-Swap Gate Count", color='black')

                # ax2.set_ylabel("Total SWAP Count")
                # if last:
                #     ax2.set_xlabel("Num Qubits")
                if not duration == 2:
                    ax2.legend()
                if first:
                    ax2.set_ylabel("Total SWAP Count")  # vs Num Qubits")

            if motivation:
                # critical path swap gates
                x = backend.data["0"][circuit_label]["preswap_gate_count_crit"].keys()
                x = [int(el) for el in list(x)]
                y_best = np.ones(len(x)) * np.inf
                y_average = np.zeros(len(x))
                keys = [el for el in backend.data.keys() if el.isdigit()]
                for iter_key in keys:
                    y = backend.data[iter_key][circuit_label][
                        "preswap_gate_count_crit"
                    ].values()
                    x, y = zip(*zip(x, y))
                    y = [el["swap"] if "swap" in el.keys() else 0 for el in y]
                    # XXX monkey patch
                    x = list(x)
                    y = list(y)
                    if len(x) > 10:
                        for val in [4, 6, 10, 12, 14]:
                            if val in x:
                                del_index = x.index(val)
                                x.pop(del_index)
                                y.pop(del_index)
                    x, y = zip(*sorted(zip(x, y)))

                    for index, el in enumerate(y):
                        if y_best[index] > el:
                            y_best[index] = el
                        y_average[index] += el
                y_average /= len(keys)
                y_average = y_average[0 : len(x)]
                if plot_average:
                    y = y_average
                else:
                    y = y_best
                ax3.plot(
                    x,
                    y,
                    marker=mark(backend.label),
                    label=backend.label,
                    color=color_map(backend.label),
                )

                if backend_i == 0:
                    # skip for now
                    pass
                    # monkey patch in a thing which prints the non swap gates
                    # from qiskit import transpile
                    # from qiskit.converters import circuit_to_dag
                    # from circuit_suite import circuits
                    # y = [circuit_to_dag(transpile(circuits[circuit_label].circuit_lambda(xi), basis_gates=['u', 'cx'])).count_ops_longest_path()['cx'] for xi in x]
                    # ax3.plot(x, y, marker='.', linestyle='--', label="Non-Swap Gate Count", color='black')

                # ax3.set_ylabel("Critical Path SWAP Count")
                # if last:
                #     ax3.set_xlabel("Num Qubits")
                if first:
                    ax3.set_ylabel("Critical Path SWAPs")  #  vs Num Qubits")
                if not duration == 2:
                    ax3.legend()
            if not motivation:
                # critical path swap gates
                x = backend.data["0"][circuit_label]["gate_count"].keys()
                x = [int(el) for el in list(x)]
                y_best = np.ones(len(x)) * np.inf
                y_average = np.zeros(len(x))
                keys = [el for el in backend.data.keys() if el.isdigit()]
                for iter_key in keys:
                    y = backend.data[iter_key][circuit_label]["gate_count"].values()
                    x, y = zip(*zip(x, y))
                    twoqgate_list = ["rzx", "riswap", "cx", "syc", "fSim"]
                    for twoqgate in twoqgate_list:
                        temp = [
                            el[twoqgate] if twoqgate in el.keys() else 0 for el in y
                        ]
                        if temp[-1] != 0:
                            y = temp
                            break
                    # XXX monkey patch
                    x = list(x)
                    y = list(y)
                    if len(x) > 10:
                        for val in [4, 6, 10, 12, 14]:
                            if val in x:
                                del_index = x.index(val)
                                x.pop(del_index)
                                y.pop(del_index)

                    x, y = zip(*sorted(zip(x, y)))

                    for index, el in enumerate(y):
                        if y_best[index] > el:
                            y_best[index] = el
                        y_average[index] += el
                y_average /= len(keys)
                y_average = y_average[0 : len(x)]
                if plot_average:
                    y = y_average
                else:
                    y = y_best
                ax2.plot(
                    x,
                    y,
                    marker=mark(backend.label),
                    label=backend.label,
                    color=color_map(backend.label),
                )
                # ax4.set_ylabel("Total 2Q Gate Count")
                # if last:
                #     ax4.set_xlabel("Num Qubits")
                if first:
                    ax2.set_ylabel("Total 2Q Count")  #  vs Num Qubits")
                if not duration == 2:
                    ax2.legend()

            # #duration
            if not motivation:
                x = backend.data["0"][circuit_label]["duration"].keys()
                x = [int(el) for el in list(x)]
                y_best = np.ones(len(x)) * np.inf
                y_average = np.zeros(len(x))
                keys = [el for el in backend.data.keys() if el.isdigit()]
                for iter_key in keys:
                    y = backend.data[iter_key][circuit_label]["duration"].values()
                    # XXX monkey patch
                    x = list(x)
                    y = list(y)
                    if len(x) > 10:
                        for val in [4, 6, 10, 12, 14]:
                            if val in x:
                                del_index = x.index(val)
                                x.pop(del_index)
                                y.pop(del_index)
                    x, y = zip(*zip(x, y))
                    twoqgate_list = ["rzx", "riswap", "cx", "syc", "fSim"]
                    for twoqgate in twoqgate_list:
                        temp = [
                            el[twoqgate] if twoqgate in el.keys() else 0 for el in y
                        ]
                        if temp[-1] != 0:
                            y = temp
                            break

                    for index, el in enumerate(y):
                        if y_best[index] > el:
                            y_best[index] = el
                        y_average[index] += el
                y_average /= len(keys)
                y_average = y_average[0 : len(x)]
                if plot_average:
                    y = y_average
                else:
                    y = y_best

                ax3.plot(
                    x,
                    y,
                    marker=mark(backend.label),
                    label=backend.label,
                    color=color_map(backend.label),
                )
                # ax1.set_ylabel("Critical Path 2Q Pulse Duration")
                # if last:
                #     ax1.set_xlabel("Num Qubits")
                if first:
                    ax3.set_ylabel("Pulse Duration")  #  vs Num Qubits")
    if 1 or motivation:
        return ax3
    return ax1
