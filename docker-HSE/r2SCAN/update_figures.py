from qubitPack.tool_box import get_db
from pymatgen import Structure
import numpy as np
from monty.os import cd
import glob
import pandas as pd
from qubitPack.qc_searching.analysis.main import RunDefectState
import os
import time, concurrent.futures

flamyngo_path = "/home/tsai/site-packages/flamyngo_Scan2dDefect/flamyngo/"
SCAN2dDefect = get_db("Scan2dDefect", "calc_data", user="Jeng", password="qimin", port=12349)

wrong_bandedges_taskids = [4, 57, 67, 84, 89, 160, 162, 165, 178, 205, 220, 291, 319, 361, 366, 375, 391, 412,
                           425, 437, 441, 494, 501, 528, 645, 659, 667, 673, 682, 687, 696, 720, 745, 866, 888,
                           889, 912, 920, 945, 948, 953, 956, 985, 1015, 1054, 1061, 1069, 1071, 1077, 1278,
                           1289, 1293, 1298, 1299, 1310, 1323, 1324, 1327, 1343, 1394, 1400, 1403, 1423, 1433,
                           1485, 1498, 1500, 1505, 1513, 1516, 1520, 1525, 1531, 1534, 1537, 1549, 1556, 1559,
                           1574, 1621, 1623, 1635, 1653, 1722, 1752, 1759, 1765, 1786, 1794, 1798, 1802, 1817,
                           1818, 1822, 1841, 1847, 1871, 1874, 1875, 1959, 1990, 2008, 2013, 2014, 2019, 2024,
                           2041, 2053, 2057, 2081, 2101, 2108, 2117, 2242, 2286, 2347, 2409, 2412, 2414, 2418,
                           2441, 2448, 2499, 2512, 2570, 2646, 2654, 2661, 2677, 2683, 2706, 2724, 2729, 2734,
                           2749, 2761, 2784, 2803, 2809, 2810, 2834, 2836, 2842, 2867, 2976, 2977, 2978, 2985,
                           3020, 3022, 3024, 3025, 3030, 3037, 3092, 3096, 3110, 3113, 3123, 3124, 3125, 3137,
                           3145, 3164, 3224, 3242, 3258, 3393, 3409, 3524, 3526, 3653, 3773, 3785, 3835, 3841,
                           3853, 3860, 3866, 3892, 3903, 3908, 3914, 3953, 3962, 3967, 3990, 3999, 4014, 4023,
                           4031, 4136, 4138, 4251, 4253, 4254, 4258, 4301, 4305, 4328, 4339, 4357, 4441, 4443,
                           4462, 4465, 4483, 4570, 4587, 4611, 4619, 4622, 4627, 4645, 4664, 4665, 4730, 4745,
                           4772, 4820, 4891, 4893, 4903, 4909, 4971, 4988, 4996, 5003, 5008, 5015, 5069, 5088,
                           5102, 5117, 5144, 5229, 5276, 5344, 5371, 5377, 5443, 5533, 5538, 5591, 5636, 5644,
                           5675, 5681, 5701, 5702, 5726, 5733, 5747, 5754, 5794, 5797, 5804, 5828, 5847, 5928,
                           5970, 5978, 5982, 6012, 6013, 6027, 6033, 6040, 6051, 6071, 6072, 6073, 6084]


def generate_all_figures():

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

            with cd(os.path.join(flamyngo_path, "static", "materials")):
                st.to("cif", f"{uid}.cif")
                # convert_poscar_to_pdb(f"{uid}.vif")

        def get_ev_ipr():
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
            run_defect_state.ir_db = None
            try:
                eigen_plot, fig, _, _, bulk_df, d_df, defect_levels, tot, perturbed_bandedge_df = \
                    run_defect_state.plot_ipr_vs_tot_proj(
                        taskid=int(uid),
                        threshold=0.03,
                        defect_plot=None,  # "eigen",
                        threshold_from="tot_proj",
                        edge_tol=(0.25, 0.25)
                    )
            except Exception as e:
                print(e)
                return None
            bandgap_df = pd.DataFrame(
                {
                    "bandgap": [perturbed_bandedge_df.iloc[1]["energy"] -
                                perturbed_bandedge_df.iloc[0]["energy"]]
                }
                )
            print(bandgap_df)
            with cd(os.path.join(flamyngo_path, "static", "materials")):
                perturbed_bandedge_df.to_json(f"{uid}_perturbed_bandedge_df.json")
                bandgap_df.to_json(f"{uid}_bandgap_df.json")

            def split_defect_levels(a=defect_levels, b=d_df):
                # transform a into a dataframe by making the length of values in each key the same by padding with None
                a = {k: v + (None,) * (max(map(len, a.values())) - len(v)) for k, v in a.items()}
                a = pd.DataFrame(a)
                # split a into to dataframes, one for up and one for down
                a_up = a[[col for col in a.columns if "up" in col]]
                a_dn = a[[col for col in a.columns if "dn" in col]]
                # remove rows with up_in_gap_level is None
                a_up = a_up[a_up["up_in_gap_level"].notnull()]
                a_dn = a_dn[a_dn["dn_in_gap_level"].notnull()]
                print(f"a_up: {a_up}", f"a_dn: {a_dn}")


                b_up = b[[col for col in b.columns if "up" in col]]
                b_dn = b[[col for col in b.columns if "dn" in col]]
                print(f"b_up: {b_up}", f"b_dn: {b_dn}")
                # remove rows iwth up_tran_en is None
                b_up = b_up[b_up["up_tran_en"].notnull()]
                b_dn = b_dn[b_dn["dn_tran_en"].notnull()]
                print(f"b_up: {b_up}", f"b_dn: {b_dn}")


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

                with cd(os.path.join(flamyngo_path, "static", "materials")):
                    a_up.to_json(f"{uid}_up_in_gap.json", orient="records", indent=4)
                    a_dn.to_json(f"{uid}_dn_in_gap.json", orient="records", indent=4)
                    b_up.to_json(f"{uid}_up_tran.json", orient="records", indent=4)
                    b_dn.to_json(f"{uid}_dn_tran.json", orient="records", indent=4)

            split_defect_levels()
            with cd(os.path.join(flamyngo_path, "static", "materials")):
                eigen_plot.savefig(f"{uid}.png")
                fig.savefig(f"{uid}_ipr.png")

        get_structure_info()
        get_ev_ipr()

    entries = list(SCAN2dDefect.collection.find({"task_label": "SCAN_scf",
                                                 "data_web.bandgap_df.bandgap.0": {"$exists": 0}}))
    t1 = time.perf_counter()
    for entry in entries:
        # with cd(os.path.join(path, "static", "materials")):
        #     if  len(glob.glob(f"{entry['task_id']}_ipr.png")) != 0:
        #         print("%%%%%%% done"*5)
        #         continue
        try:
            get_doc(entry)
        except Exception as e:
            print(e)
    t2 = time.perf_counter()
    print(f"Finished in {t2-t1} seconds")


def update_entries_in_db():
    from monty.serialization import loadfn
    def update_entry(uid):
        with cd(os.path.join(flamyngo_path, "static", "materials")):
            perturbed_bandedge_df = loadfn(f"{uid}_perturbed_bandedge_df.json") if len(glob.glob(f"{uid}_perturbed_bandedge_df.json")) != 0 else None
            bandgap_df = loadfn(f"{uid}_bandgap_df.json") if len(glob.glob(f"{uid}_bandgap_df.json")) != 0 else None
            a_up = loadfn(f"{uid}_up_in_gap.json") if len(glob.glob(f"{uid}_up_in_gap.json")) != 0 else None
            a_dn = loadfn(f"{uid}_dn_in_gap.json") if len(glob.glob(f"{uid}_dn_in_gap.json")) != 0 else None
            b_up = loadfn(f"{uid}_up_tran.json") if len(glob.glob(f"{uid}_up_tran.json")) != 0 else None
            b_dn = loadfn(f"{uid}_dn_tran.json") if len(glob.glob(f"{uid}_dn_tran.json")) != 0 else None
            total_update_dict = {}
            for d_name, d in zip(["perturbed_bandedge_df", "bandgap_df", "up_in_gap", "dn_in_gap", "up_tran",
                                 "dn_tran"],
                         [perturbed_bandedge_df, bandgap_df, a_up, a_dn, b_up, b_dn]):
                total_update_dict[d_name] = d
            total_update_dict.update({"threshold_tot_proj": 0.03})
            return total_update_dict

    tgt_taskids = [i["task_id"]for i in list(SCAN2dDefect.collection.find({"task_label": "SCAN_scf",
                                                 "data_web.bandgap_df.bandgap.0": {"$exists": 0}}))]
    with cd(os.path.join(flamyngo_path, "static", "materials")):
        t1 = time.perf_counter()
        for f in glob.glob("*.cif"):
            uid = f.split(".")[0]
            uid = int(uid)
            if uid in tgt_taskids:
                print(f"uid {uid}")
                total_update_dict = update_entry(uid)
                SCAN2dDefect.collection.update_one({"task_id": uid}, {"$set": {"data_web": total_update_dict}})
        t2 = time.perf_counter()
        print(f"Finished in {t2-t1} seconds")

if __name__ == "__main__":
    generate_all_figures()
    update_entries_in_db()
