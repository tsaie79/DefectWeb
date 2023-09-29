from qubitPack.tool_box import get_db
from pymatgen import Structure
import numpy as np
from monty.os import cd
import glob
import pandas as pd
from qubitPack.qc_searching.analysis.main import RunDefectState
import os
import time, concurrent.futures

flamyngo_path = "/home/tsai/site-packages/HT_defect_web/flamyngo"
HSEDB = get_db("HSE_triplets_from_Scan2dDefect", "calc_data-pbe_pc", user="Jeng", password="qimin", port=12349)
HSECDFT= get_db("HSE_triplets_from_Scan2dDefect", "cdft-pbe_pc", user="Jeng", password="qimin", port=12349)
HSEZFS =get_db("HSE_triplets_from_Scan2dDefect", "zfs_data-pbe_pc", user="Jeng", password="qimin", port=12349)

def generate_all_figures(threshold_tot_proj, taskid, edge_tol=None, select_bands=None):

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
                "db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "calc_data-pbe_pc", "port": 12349,
                "user": "Jeng_ro"
            }
            ir_db = {
                "db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "ir_data-pbe_pc", "port": 12349,
                "user": "Jeng_ro"
            }
            run_defect_state = RunDefectState(calc_db_config=calc_db, ir_db_config=ir_db)
            try:
                eigen_plot, fig, _, _, bulk_df, d_df, defect_levels, tot, perturbed_bandedge_df = \
                    run_defect_state.plot_ipr_vs_tot_proj(
                        taskid=int(uid),
                        threshold=threshold_tot_proj,
                        defect_plot=None,  # "eigen",
                        threshold_from="tot_proj",
                        edge_tol=(0.5, 0.5) if edge_tol is None else edge_tol,
                        select_bands=select_bands,
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

    entries = list(HSEDB.collection.find({"task_label": "HSE_scf", "task_id": taskid}))
    #"data_web.bandgap_df.bandgap.0": {
    # "$exists": 0}}))]
    t1 = time.perf_counter()
    for entry in entries:
        # with cd(os.path.join(flamyngo_path, "static", "materials")):
        #     if  len(glob.glob(f"{entry['task_id']}_ipr.png")) != 0:
        #         print("%%%%%%% done"*5)
        #         continue
        try:
            get_doc(entry)
        except Exception as e:
            print(e)
    t2 = time.perf_counter()
    print(f"Finished in {t2-t1} seconds")


def update_defect_level_plots_in_db(threshold_tot_proj, taskid):
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
            total_update_dict.update({"threshold_tot_proj": threshold_tot_proj})
            return total_update_dict

    tgt_taskids = [i["task_id"]for i in list(HSEDB.collection.find({"task_label": "HSE_scf", "task_id": taskid}))]
                                                # "data_web.bandgap_df.bandgap.0": {"$exists": 0}}))]
    with cd(os.path.join(flamyngo_path, "static", "materials")):
        t1 = time.perf_counter()
        for f in glob.glob("*.cif"):
            uid = f.split(".")[0]
            uid = int(uid)
            if uid in tgt_taskids:
                print(f"uid {uid}")
                total_update_dict = update_entry(uid)
                HSEDB.collection.update_one({"task_id": uid}, {"$set": {"data_web": total_update_dict}})
        t2 = time.perf_counter()
        print(f"Finished in {t2-t1} seconds")

def update_cdft_entries_in_db_and_generate_json():
    from JPack_independent.projects.defectDB.analysis.data_analysis import CDFT
    for doc in list(HSECDFT.collection.find({"task_label": "CDFT-B-HSE_scf"})):
        print("------------------"*5, doc["task_id"])
        owls = [2657, 2658, 2671, 2688, 2707, 2708]
        if doc["taskid"] in owls:
            continue
        cdft = CDFT()
        try:
            cdft.get_data_sheet({"taskid": doc["taskid"]})
        except Exception as e:
            print(e)
            continue

        basic_info_df = cdft.foundation_df
        cdft_df = cdft.get_zpl_data()
        # split those columns with "up_" into a new dataframe and remove them from cdft_df
        up_df = cdft_df[cdft_df.columns[cdft_df.columns.str.contains("up")]]
        cdft_df = cdft_df.drop(cdft_df.columns[cdft_df.columns.str.contains("up")], axis=1)
        # split those columns with "down_" into a new dataframe and remove them from cdft_df
        down_df = cdft_df[cdft_df.columns[cdft_df.columns.str.contains("dn")]]
        cdft_df = cdft_df.drop(cdft_df.columns[cdft_df.columns.str.contains("dn")], axis=1)

        cdft_dict = {}
        for d_name, d in zip(["zpl_df", "tdm_up_df", "tdm_dn_df"], [cdft_df, up_df, down_df]):
            cdft_dict[d_name] = d.to_dict(orient="records")
        HSECDFT.collection.update_one({"task_id": doc["task_id"]}, {"$set": {"data_web": cdft_dict}})
        HSEDB.collection.update_one({"task_id": doc["taskid"]}, {"$set": {"data_web.cdft_data": cdft_dict}})
        with cd(os.path.join(flamyngo_path, "static", "materials")):
            basic_info_df.to_json(f"{doc['taskid']}_basic_info_df.json")
            cdft_df.to_json(f"{doc['task_id']}_zpl_df.json")
            up_df.to_json(f"{doc['task_id']}_up_tdm_df.json")
            down_df.to_json(f"{doc['task_id']}_dn_tdm_df.json")


def update_singlet_triplet_diff_in_db():
    for triplet_entry in list(HSEDB.collection.find({"nupdown_set": 2, "task_label": "HSE_scf"})):
        pc_from = triplet_entry["pc_from"]
        charge_state = triplet_entry["charge_state"]
        defect_name = triplet_entry["defect_entry"]["name"]
        singlet_criteria = {
            "nupdown_set": 0,
            "pc_from": pc_from,
            "charge_state": charge_state,
            "defect_entry.name": defect_name,
            "task_label": "HSE_scf"
        }
        singlet_data = {}
        singlet_entry = HSEDB.collection.find_one(singlet_criteria)
        if singlet_entry is None:
            singlet_data["triplet_singlet_energy_diff"] = None
            singlet_data["singlet_taskid"] = None
            continue
        singlet_data["triplet_singlet_energy_diff"] = triplet_entry["output"]["energy"] - singlet_entry["output"][
            "energy"]
        singlet_data["singlet_taskid"] = singlet_entry["task_id"]
        # update the triplet entry["data_web"] with singlet data and save it to db
        data_web = triplet_entry["data_web"].copy()
        data_web.update(singlet_data)
        print(f"data_web: {data_web}")
        HSEDB.collection.update_one({"task_id": triplet_entry["task_id"]}, {"$set": {"data_web": data_web}})

def update_zfs_in_db():
    for scf_doc in list(HSEDB.collection.find({"task_label": "HSE_scf", "nupdown_set": 2,})):
        print(f"task_id: {scf_doc['task_id']}")
        doc = HSEZFS.collection.find_one({"prev_fw_taskid": scf_doc["task_id"]})
        if doc is None:
            continue
        D = round(doc["pyzfs_out"]["D"] / 1000, 2)
        E = round(doc["pyzfs_out"]["E"] / 1000, 2)
        Dx = round(doc["pyzfs_out"]["Dx"] / 1000, 2)
        Dy = round(doc["pyzfs_out"]["Dy"] / 1000, 2)
        Dz = round(doc["pyzfs_out"]["Dz"] / 1000, 2)
        zfs_data = {"D": D, "E": E, "Dx": Dx, "Dy": Dy, "Dz": Dz}
        HSEDB.collection.update_one({"task_id": scf_doc["task_id"]}, {"$set": {"data_web.zfs_data": zfs_data}})


if __name__ == "__main__":
    # loc, taskid = 0.14, 2569
    # generate_all_figures(loc, taskid)
    # update_defect_level_plots_in_db(loc, taskid)
    update_singlet_triplet_diff_in_db()
    # update_cdft_entries_in_db_and_generate_json()
    # update_zfs_in_db()