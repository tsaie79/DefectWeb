import os.path

import matplotlib.pyplot as plt
from qubitPack.tool_box import get_db
from __init__ import __file__
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
    calc_db = {"db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "calc_data-pbe_pc", "port": 12349,
          "user": "Jeng_ro"}
    ir_db = {"db_name": "HSE_triplets_from_Scan2dDefect", "collection_name": "ir_data-pbe_pc", "port": 12349,
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
if __name__ == "__main__":
    get_ev()