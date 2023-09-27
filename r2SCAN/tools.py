import os.path

import matplotlib.pyplot as plt
from qubitPack.tool_box import get_db

from pymatgen import Structure
import numpy as np
from monty.os import cd
import glob
import pandas as pd
from qubitPack.qc_searching.analysis.main import RunDefectState

import time
from concurrent.futures import ProcessPoolExecutor

# get the path of the python file
__file__ = os.path.abspath(os.path.dirname(__file__))

import re
def regex_match(regex, string):
    return re.search(regex, string).group(0)


def convert_poscar_to_pdb(POSCAR_file):
    # use vaspkit 419 to convert POSCAR to PDB
    from subprocess import call
    call("rm POSCAR.pdb", shell=True)
    call(f"vaspkit -task 419 -file {POSCAR_file}", shell=True)

def get_pdb_from_db(db, filter):
    from pymatgen import Structure
    entry = db.collection.find_one(filter)
    st = entry["output"]["structure"]
    st = Structure.from_dict(st)
    import monty

    with monty.os.cd(os.path.join(__file__, "static", "materials")):
        st.to("POSCAR", "POSCAR")
        convert_poscar_to_pdb("POSCAR")

def get_ir_data():
    a = [1,2,3]
    b = [4,5,6]
    # generate a new list c = ["1 2", "3 4", "5 6"]
    c = [f"{i} {j}" for i, j in zip(a, b)]

def get_ev(task_id):
    from qubitPack.qc_searching.analysis.main import RunDefectState
    from qubitPack.tool_box import get_db
    calc_db = {"db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "calc_data-pbe_pc", "port": 27017,
          "user": "Jeng_ro"}
    ir_db = {"db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "ir_data-pbe_pc", "port": 27017,
             "user": "Jeng_ro"}
    run_defect_state = RunDefectState(
        calc_db_config={"db_name": calc_db["db_name"], "collection_name": calc_db[
        "collection_name"], "port": calc_db["port"], "user": calc_db["user"]},
        ir_db_config={"db_name": ir_db["db_name"],
                      "collection_name": ir_db["collection_name"],
                      "port": ir_db["port"],
                      "user": ir_db["user"]})

    eigen_plot, tot, proj, d_df, levels, defect_levels, bulk_tot, bandedge_bulk_tot = \
        run_defect_state.get_defect_state_ipr_with_ir(129, 0.02, edge_tol=(1,1), threshold_from="tot_proj", plot=None)
    eigen_plot.savefig(f"/static/images/{task_id}.pdf", format="pdf")
    plt.close(eigen_plot)
    plot_url = f"/static/images/{task_id}.pdf"
    return plot_url



def get_doc(doc):

    """
    Returns document.
    """
    uid = doc["task_id"]
    print(f"uid: {uid}")
    def get_structure_info():
        st = Structure.from_dict(doc["output"]["structure"])
        origin = np.array([0, 0, st.lattice.c / 2])
        v1, v2, v3 = origin + st.lattice.matrix
        end = [v1, v2, v3]
        st.make_supercell([2, 2, 1])

        with cd(os.path.join(__file__, "static", "materials")):
            st.to("cif", f"{uid}.cif")
            # convert_poscar_to_pdb(f"{uid}.vif")

        return {
            "Ox": origin[0], "Oy": origin[1], "Oz": origin[2],
            "v1x": end[0][0], "v1y": end[0][1], "v1z": end[0][2], "v2x": end[1][0], "v2y": end[1][1],
            "v2z": end[1][2], "v3x": end[2][0], "v3y": end[2][1], "v3z": end[2][2]
        }

    def get_ev_ipr():
        with cd(os.path.join(__file__, "static", "materials")):
            if len(glob.glob(f"{uid}_ipr.png")) != 0 and len(glob.glob(f"{uid}.png")) != 0:
                return None

            calc_db = {
                "db_name": "Scan2dDefect", "collection_name": "calc_data", "port": 12349,
                "user": "Jeng_ro"
            }
            ir_db = {
                "db_name": "Scan2dDefect", "collection_name": "ir_data", "port": 12349,
                "user": "Jeng_ro"
            }
            run_defect_state = RunDefectState(
                calc_db_config={
                    "db_name": calc_db["db_name"],
                    "collection_name": calc_db["collection_name"],
                    "port": calc_db["port"],
                    "user": calc_db["user"]
                },
                ir_db_config={
                    "db_name": ir_db["db_name"],
                    "collection_name": ir_db["collection_name"],
                    "port": ir_db["port"],
                    "user": ir_db["user"]
                }
            )
            eigen_plot, fig, _, _, bulk_df, d_df, defect_levels, tot, perturbed_bandedge_df = \
                run_defect_state.plot_ipr_vs_tot_proj(
                    taskid=int(uid),
                    threshold=0.2,
                    defect_plot=None,  # "eigen",
                    threshold_from="tot_proj",
                    edge_tol=(0.25, 0.25)
                )
            bandgap_df = pd.DataFrame(
                {
                    "bandgap": [perturbed_bandedge_df.iloc[1]["energy"] -
                                perturbed_bandedge_df.iloc[0]["energy"]]
                }
                )
            perturbed_bandedge_df.to_json(f"{uid}_perturbed_bandedge_df.json")
            bandgap_df.to_json(f"{uid}_bandgap_df.json")

            def split_defect_levels(a=defect_levels, b=d_df):
                # transform a into a dataframe by making the length of values in each key the same by padding with None
                a = {k: v + (None,) * (max(map(len, a.values())) - len(v)) for k, v in a.items()}
                a = pd.DataFrame(a)
                # split a into to dataframes, one for up and one for down
                a_up = a[[col for col in a.columns if "up" in col]]
                a_dn = a[[col for col in a.columns if "dn" in col]]
                # remove nan values
                a_up = a_up.dropna()
                a_dn = a_dn.dropna()

                b_up = b[[col for col in b.columns if "up" in col]]
                b_dn = b[[col for col in b.columns if "dn" in col]]
                b_up = b_up.dropna()
                b_dn = b_dn.dropna()

                # drop columns [up_tran_ir, up_tran_occ, up_tran_deg, up_tran_band_id, up_tran_level, up_tran_band_index]
                b_up = b_up.drop(
                    columns=["up_tran_ir", "up_tran_occ", "up_tran_deg", "up_tran_band_id",
                                "up_tran_level", "up_tran_band_index"]
                    )
                b_dn = b_dn.drop(
                    columns=["dn_tran_ir", "dn_tran_occ", "dn_tran_deg", "dn_tran_band_id",
                                "dn_tran_level", "dn_tran_band_index"]
                    )

                # dump the dataframes into a json
                a_up.to_json(f"{uid}_up_in_gap.json", orient="records", indent=4)
                a_dn.to_json(f"{uid}_dn_in_gap.json", orient="records", indent=4)
                b_up.to_json(f"{uid}_up_tran.json", orient="records", indent=4)
                b_dn.to_json(f"{uid}_dn_tran.json", orient="records", indent=4)

            split_defect_levels()
            eigen_plot.savefig(f"{uid}.png")
            fig.savefig(f"{uid}_ipr.png")

    get_structure_info()
    get_ev_ipr()


def generate_all_figures():
    # path = "/home/tsai/site-packages/flamyngo_Scan2dDefect/flamyngo/"
    SCAN2dDefect = get_db("Scan2dDefect", "calc_data", user="Jeng_ro", password="qimin", port=12349)
    entries = list(SCAN2dDefect.collection.find({"task_label": "SCAN_scf", }))
    print("-------------------")

    t1 = time.perf_counter()
    with ProcessPoolExecutor() as executor:
        results = executor.map(get_doc, entries[:5])
    # get_doc(entries[0])
    t2 = time.perf_counter()
    print("time: ", t2 - t1)


if __name__ == "__main__":
    generate_all_figures()
