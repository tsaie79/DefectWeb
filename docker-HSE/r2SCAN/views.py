"""
Main implementation of Flamyngo webapp and all processing.
"""
import glob
import json
import os
import re
from functools import wraps

import pandas as pd
import numpy as np
import plotly
import plotly.express as px
from flask import Response, make_response, render_template, request
from flask.json import jsonify
from monty.json import jsanitize
from monty.serialization import loadfn
from monty.os import cd
from pymongo import MongoClient
from ruamel.yaml import YAML
from markupsafe import Markup
from bson.objectid import ObjectId

from flamyngo.app import app

from pymatgen.io.vasp.inputs import Structure

# from qubitPack.qc_searching.analysis.main import RunDefectState

# from flamyngo_Scan2dDefect.flamyngo import __file__
from flamyngo import __file__

__file__ = os.path.abspath(os.path.dirname(__file__))
print(f"__file__ = {__file__}")
SETTINGS = loadfn(os.environ["FLAMYNGO"])

APP_TITLE = SETTINGS.get("title", "Flamyngo")
HELPTXT = SETTINGS.get("help", "")
TEMPLATE_FOLDER = SETTINGS.get("template_folder", "templates")

DB_SETTINGS = SETTINGS["db"]

if "connection_string" in DB_SETTINGS:
    connect_string = DB_SETTINGS["connection_string"]
else:
    if "username" in DB_SETTINGS:
        connect_string = (
            f'mongodb://{DB_SETTINGS["username"]}:{DB_SETTINGS["password"]}@'
            f'{DB_SETTINGS["host"]}:{DB_SETTINGS["port"]}/{DB_SETTINGS["database"]}'
        )
    else:
        connect_string = f'mongodb://{DB_SETTINGS["host"]}:{DB_SETTINGS["port"]}/{DB_SETTINGS["database"]}'

CONN = MongoClient(connect_string)
DB = CONN[DB_SETTINGS["database"]]

CNAMES = [f'{d["name"]}' for d in SETTINGS["collections"]]
CSETTINGS = {d["name"]: d for d in SETTINGS["collections"]}
AUTH_USER = SETTINGS.get("AUTH_USER", None)
AUTH_PASSWD = SETTINGS.get("AUTH_PASSWD", None)
API_KEY = SETTINGS.get("API_KEY", None)


def check_auth(username, password):
    """
    This function is called to check if a username /
    password combination is valid.
    """
    if AUTH_USER is None:
        return True
    return username == AUTH_USER and password == AUTH_PASSWD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        "Could not verify your access level for that URL. You have to login "
        "with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def requires_auth(f):
    """
    Check for authentication.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        api_key = request.headers.get("API_KEY") or request.args.get("API_KEY")
        if (API_KEY is not None) and api_key == API_KEY:
            return f(*args, **kwargs)
        if (AUTH_USER is not None) and (
            not auth or not check_auth(auth.username, auth.password)
        ):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def get_mapped_name(settings, name):
    """
    The following allows used of mapped names in search criteria.
    """
    name_mappings = {v: k for k, v in settings.get("aliases", {}).items()}
    return name_mappings.get(name, name)


def process_search_string_regex(search_string, settings):
    """
    Process search string with regex
    """
    criteria = {}
    for regex in settings["query"]:
        if re.match(regex[1], search_string):
            criteria[regex[0]] = {"$regex": str(process(search_string, regex[2]))}
            break
    if not criteria:
        clean_search_string = search_string.strip()
        if clean_search_string[0] != "{" or clean_search_string[-1] != "}":
            clean_search_string = "{" + clean_search_string + "}"
        criteria = json.loads(clean_search_string)

        criteria = {get_mapped_name(settings, k): v for k, v in criteria.items()}
    return criteria


def process_search_string(search_string, settings):
    """
    Process search string with query.
    """
    criteria = {}
    for regex in settings["query"]:
        if re.match(regex[1], search_string):
            criteria[regex[0]] = process(search_string, regex[2])
            break
    if not criteria:
        clean_search_string = search_string.strip()
        if clean_search_string[0] != "{" or clean_search_string[-1] != "}":
            clean_search_string = "{" + clean_search_string + "}"
        criteria = json.loads(clean_search_string)

        criteria = {get_mapped_name(settings, k): v for k, v in criteria.items()}
    return criteria


@app.route("/", methods=["GET"])
@requires_auth
def index():
    """
    Index page.
    """
    return make_response(
        render_template(
            "index.html", collections=CNAMES, helptext=HELPTXT, app_title=APP_TITLE
        )
    )


@app.route("/autocomplete", methods=["GET"])
@requires_auth
def autocomplete():
    """
    Autocomplete if allowed.
    """
    if SETTINGS.get("autocomplete"):
        terms = []
        criteria = {}

        search_string = request.args.get("term")
        cname = request.args.get("collection").split(":")[0]

        collection = DB[cname]
        settings = CSETTINGS[cname]

        # if search looks like a special query, autocomplete values
        for regex in settings["query"]:
            if re.match(regex[1], search_string):
                criteria[regex[0]] = {"$regex": str(process(search_string, regex[2]))}
                projection = {regex[0]: 1}

                results = collection.find(criteria, projection)

                if results:
                    terms = [term[regex[0]] for term in results]

        # if search looks like a query dict, autocomplete keys
        if not criteria and search_string[0:2] == '{"':
            if search_string.count('"') % 2 != 0:
                splitted = search_string.split('"')
                previous = splitted[:-1]
                last = splitted[-1]

                # get list of autocomplete keys from settings
                # generic alternative: use a schema analizer like variety.js
                results = _search_dict(settings["autocomplete_keys"], last)

                if results:
                    terms = ['"'.join(previous + [term]) + '":' for term in results]

        return jsonify(matching_results=jsanitize(list(set(terms))))
    return jsonify(matching_results=[])


@app.route("/query", methods=["GET"])
@requires_auth
def query():
    """
    Process query search.
    """
    cname = request.args.get("collection").split(":")[0]
    settings = CSETTINGS[cname]
    search_string = request.args.get("search_string")
    projection = [t[0].split(".")[0] for t in settings["summary"]]
    fields = None
    results = None
    mapped_names = None
    error_message = None
    try:
        if search_string.strip() != "":
            criteria = process_search_string(search_string, settings)
            criteria.update(settings.get("filter_criteria", {}))
            exclude_entries = settings.get("exclude_entries", None)
            if exclude_entries:
                exclude_entries = {"_id": {"$nin": [ObjectId(v) for v in exclude_entries]}}
                criteria.update(exclude_entries)
            print(f"criteria: {criteria}")
            results = []
            for r in DB[cname].find(criteria, projection=projection):
                processed = []
                mapped_names = {}
                fields = []
                for m in settings["summary"]:
                    if len(m) == 2:
                        k, v = m
                    else:
                        raise ValueError("Invalid summary settings!")
                    mapped_k = settings.get("aliases", {}).get(k, k)
                    val = _get_val(k, r, v.strip())
                    val = val if val is not None else ""
                    mapped_names[k] = mapped_k
                    processed.append(val)
                    fields.append(mapped_k)
                results.append(processed)
            if not results:
                error_message = "No results!"
        else:
            error_message = "No results!"
    except Exception as ex:
        error_message = str(ex)

    try:
        sort_key, sort_mode = settings["sort"]
        sort_index = fields.index(sort_key)
    except Exception:
        sort_index = 0
        sort_mode = "asc"

    return make_response(
        render_template(
            "index.html",
            collection_name=cname,
            sort_index=sort_index,
            sort_mode=sort_mode,
            results=results,
            fields=fields,
            search_string=search_string,
            mapped_names=mapped_names,
            unique_key=settings["unique_key"],
            active_collection=cname,
            collections=CNAMES,
            error_message=error_message,
            helptext=HELPTXT,
            app_title=APP_TITLE,
        )
    )


@app.route("/plot", methods=["GET"])
@requires_auth
def plot():
    """
    Plot data.
    """
    cname = request.args.get("collection")
    if not cname:
        return make_response(render_template("plot.html", collections=CNAMES))

    cname = cname.split(":")[0]
    plot_type = request.args.get("plot_type") or "scatter"
    search_string = request.args.get("search_string")
    xaxis = request.args.get("xaxis")
    yaxis = request.args.get("yaxis")

    settings = CSETTINGS[cname]

    xaxis_mapped = get_mapped_name(settings, xaxis)
    yaxis_mapped = get_mapped_name(settings, yaxis)

    projection = [xaxis_mapped, yaxis_mapped]

    if search_string.strip() != "":
        criteria = process_search_string(search_string, settings)
        data = []
        for r in DB[cname].find(criteria, projection=projection):
            x = _get_val(xaxis_mapped, r, None)
            y = _get_val(yaxis_mapped, r, None)
            if x and y:
                data.append([x, y])
    else:
        data = []

    df = pd.DataFrame(data, columns=[xaxis, yaxis])
    if plot_type == "scatter":
        fig = px.scatter(df, x=xaxis, y=yaxis)
    else:
        fig = px.bar(df, x=xaxis, y=yaxis)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return make_response(
        render_template(
            "plot.html",
            collection=cname,
            search_string=search_string,
            plot_type=plot_type,
            xaxis=xaxis,
            yaxis=yaxis,
            active_collection=cname,
            collections=CNAMES,
            app_title=APP_TITLE,
            graphJSON=graphJSON,
        )
    )


@app.route("/<string:collection_name>/unique_ids")
@requires_auth
def get_ids(collection_name):
    """
    Returns unique ids
    """
    settings = CSETTINGS[collection_name]
    doc = DB[collection_name].distinct(settings["unique_key"])
    return jsonify(jsanitize(doc))


@app.route("/<string:collection_name>/doc/<string:uid>")
@requires_auth
def get_doc(collection_name, uid):
    """
    Returns document.
    """
    settings = CSETTINGS[collection_name]
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria)

    def get_structure_info():
        st = Structure.from_dict(doc["output"]["structure"])
        origin = np.array([0, 0, st.lattice.c/2])
        v1, v2, v3 = origin + st.lattice.matrix
        end = [v1, v2, v3]
        st.make_supercell([2, 2, 1])

        with cd(os.path.join(__file__, "static", "materials")):
            st.to("cif", f"{uid}.cif")
            # convert_poscar_to_pdb(f"{uid}.vif")

        return {"Ox": origin[0], "Oy": origin[1], "Oz": origin[2],
                "v1x": end[0][0], "v1y": end[0][1], "v1z": end[0][2], "v2x": end[1][0], "v2y": end[1][1],
                "v2z": end[1][2], "v3x": end[2][0], "v3y": end[2][1], "v3z": end[2][2]}


    def get_ir_data():
        filter = {"pc_from_id": doc["pc_from_id"], "defect_name": doc["defect_name"],
        "charge_state": doc["charge_state"]}
        ir_entry = DB['ir_data'].find_one(filter)
        ir_taskid = ir_entry['task_id']
        ir_url = f"/ir_data/doc_ir/{ir_taskid}"
        return ir_taskid, ir_url

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
            eigen_plot, fig, _, _, bulk_df, d_df, defect_levels, tot, perturbed_bandedge_df  = \
                run_defect_state.plot_ipr_vs_tot_proj(
                taskid=int(uid),
                threshold=0.2,
                defect_plot=None,#"eigen",
                threshold_from="tot_proj",
                edge_tol=(0.25, 0.25)
                )
            bandgap_df = pd.DataFrame({"bandgap": [perturbed_bandedge_df.iloc[1]["energy"] -
                                                   perturbed_bandedge_df.iloc[0]["energy"]]})
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
                b_up = b_up.drop(columns=["up_tran_ir", "up_tran_occ", "up_tran_deg", "up_tran_band_id",
                                          "up_tran_level", "up_tran_band_index"])
                b_dn = b_dn.drop(columns=["dn_tran_ir", "dn_tran_occ", "dn_tran_deg", "dn_tran_band_id",
                                          "dn_tran_level", "dn_tran_band_index"])


                #dump the dataframes into a json
                a_up.to_json(f"{uid}_up_in_gap.json", orient="records", indent=4)
                a_dn.to_json(f"{uid}_dn_in_gap.json", orient="records", indent=4)
                b_up.to_json(f"{uid}_up_tran.json", orient="records", indent=4)
                b_dn.to_json(f"{uid}_dn_tran.json", orient="records", indent=4)


            split_defect_levels()
            eigen_plot.savefig(f"{uid}.png")
            fig.savefig(f"{uid}_ipr.png")

    get_ev_ipr()
    with cd(os.path.join(__file__, "static", "materials")):
        up_in_gap_df = pd.read_json(f"{uid}_up_in_gap.json", orient="records")
        up_in_gap_df = Markup(up_in_gap_df.to_html(index=False))
        dn_in_gap_df = pd.read_json(f"{uid}_dn_in_gap.json", orient="records")
        dn_in_gap_df = Markup(dn_in_gap_df.to_html(index=False))
        up_tran_df = pd.read_json(f"{uid}_up_tran.json", orient="records")
        up_tran_df = Markup(up_tran_df.to_html(index=False))
        dn_tran_df = pd.read_json(f"{uid}_dn_tran.json", orient="records")
        dn_tran_df = Markup(dn_tran_df.to_html(index=False))
        perturbed_bandedge_df = pd.read_json(f"{uid}_perturbed_bandedge_df.json")
        perturbed_bandedge_df = Markup(perturbed_bandedge_df.to_html(index=False))
        bandgap_df = pd.read_json(f"{uid}_bandgap_df.json")
        bandgap_df = Markup(bandgap_df.to_html(index=False))

    lattice_info = get_structure_info()

    try:
        ir_taskid, ir_url = get_ir_data()
    except:
        ir_taskid, ir_url = None, f"/{collection_name}/doc/{uid}"

    return make_response(
        render_template(
            "doc.html", collection_name=collection_name, doc_id=uid, app_title=APP_TITLE, doc=doc,
            lattice_info=lattice_info,
            ir_taskid=ir_taskid, ir_url=ir_url, up_in_gap_df=up_in_gap_df, dn_in_gap_df=dn_in_gap_df,
            up_tran_df=up_tran_df, dn_tran_df=dn_tran_df, perturbed_bandedge_df=perturbed_bandedge_df,
            bandgap_df=bandgap_df
        )
    )


@app.route("/<string:collection_name>/doc_ir/<string:uid>")
@requires_auth
def get_doc_ir(collection_name, uid):
    """
    Returns document.
    """
    settings = CSETTINGS[collection_name]
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria)
    post_relax_sg_name = doc["post_relax_sg_name"][0]
    post_relax_sg_number = doc["post_relax_sg_number"]
    ir = doc["irvsp"]["parity_eigenvals"]["single_kpt"]["(0.0, 0.0, 0.0)"]

    up_pg_name = ir["up"]["point_group"]
    up_character_table = ir["up"]["pg_character_table"]
    up_character_table[0] = "IR1 IR2 " + up_character_table[0]
    up_character_table = pd.DataFrame([x.split() for x in up_character_table])
    # set first row as header
    up_character_table.columns = up_character_table.iloc[0]
    # remove first row and index
    up_character_table = up_character_table[1:]


    down_pg_name = ir["down"]["point_group"]
    down_character_table = ir["down"]["pg_character_table"]
    down_character_table[0] = "IR1 IR2 " + down_character_table[0]
    down_character_table = pd.DataFrame([x.split() for x in down_character_table])
    # set first row as header
    down_character_table.columns = down_character_table.iloc[0]
    # remove first row and index
    down_character_table = down_character_table[1:]

    up_band_idx = ir["up"]["band_index"]
    up_ir_index = list(range(0, len(up_band_idx)))
    up_ev = ir["up"]["band_eigenval"]
    up_deg  = ir["up"]["band_degeneracy"]
    up_irrep = ir["up"]["irreducible_reps"]
    # remove "\n" in up_irrep
    up_irrep = [x.replace("\n", "") for x in up_irrep]
    up_ir = pd.DataFrame({"band_index": up_band_idx, "ir_index": up_ir_index, "eigenval": up_ev, "degeneracy":up_deg,
                          "irreducible_reps": up_irrep}).round(3)

    down_band_idx = ir["down"]["band_index"]
    down_ir_index = list(range(0, len(down_band_idx)))
    down_ev = ir["down"]["band_eigenval"]
    down_deg  = ir["down"]["band_degeneracy"]
    down_irrep = ir["down"]["irreducible_reps"]
    # remove "\n" in down_irrep
    down_irrep = [x.replace("\n", "") for x in down_irrep]
    down_ir = pd.DataFrame({"band_index": down_band_idx, "ir_index": down_ir_index, "eigenval": down_ev,
                            "degeneracy": down_deg, "irreducible_reps": down_irrep}).round(3)


    ir_data = {"post_relax_sg_name": post_relax_sg_name, "post_relax_sg_number": post_relax_sg_number, "up_pg_name":
        up_pg_name, "up_character_table": Markup(up_character_table.to_html(index=False)), "down_pg_name":
        down_pg_name, "down_character_table": Markup(down_character_table.to_html(index=False)),
               "up_ir": Markup(up_ir.to_html(index=False)), "down_ir": Markup(down_ir.to_html(index=False))}

    filter = {"pc_from_id": doc["pc_from_id"], "defect_name": doc["defect_name"], "task_label": "SCAN_scf"}
    scf_entry = DB["calc_data"].find_one(filter)
    return make_response(
        render_template(
            "doc_ir.html", collection_name=collection_name, doc_id=uid, app_title=APP_TITLE, doc=doc,
            ir_data=ir_data, scf_taskid=scf_entry["task_id"]
        )
    )

@app.route("/<string:collection_name>/doc/<string:uid>/<string:field>")
@requires_auth
def get_doc_field(collection_name, uid, field):
    """
    Get doc field.
    """
    settings = CSETTINGS[collection_name]
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria, projection=[field])
    return Response(str(doc[field]), mimetype="text/plain")


@app.route("/<string:collection_name>/doc_ir/<string:uid>/<string:field>")
@requires_auth
def get_doc_field_ir(collection_name, uid, field):
    """
    Get doc field.
    """
    settings = CSETTINGS[collection_name]
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria, projection=[field])
    return Response(str(doc[field]), mimetype="text/plain")

@app.route("/<string:collection_name>/doc/<string:uid>/json")
@requires_auth
def get_doc_json(collection_name, uid):
    """
    Get doc json.
    """
    settings = CSETTINGS[collection_name]
    projection = {k: False for k in settings.get("doc_exclude", [])}
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria, projection=projection)

    return jsonify(jsanitize(doc))

@app.route("/<string:collection_name>/doc_ir/<string:uid>/json")
@requires_auth
def get_doc_json_ir(collection_name, uid):
    """
    Get doc json.
    """
    settings = CSETTINGS[collection_name]
    projection = {k: False for k in settings.get("doc_exclude", [])}
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria, projection=projection)

    return jsonify(jsanitize(doc))

@app.route("/<string:collection_name>/doc/<string:uid>/yaml")
@requires_auth
def get_doc_yaml(collection_name, uid):
    """
    Get doc yaml.
    """
    settings = CSETTINGS[collection_name]
    projection = {k: False for k in settings.get("doc_exclude", [])}
    criteria = {settings["unique_key"]: process(uid, settings["unique_key_type"])}
    doc = DB[collection_name].find_one(criteria, projection=projection)
    yml = YAML()
    yml.default_flow_style = False
    from io import StringIO

    s = StringIO()
    yml.dump(jsanitize(doc), s)
    response = make_response(s.getvalue(), 200)
    response.mimetype = "text/plain"
    return response


def process(val, vtype):
    """
    Value processing and formatting.
    """
    if vtype:
        if vtype.startswith("%"):
            return vtype % val

        toks = vtype.rsplit(".", 1)
        if len(toks) == 1:
            func = globals()["__builtins__"][toks[0]]
        else:
            mod = __import__(toks[0], globals(), locals(), [toks[1]], 0)
            func = getattr(mod, toks[1])
        return func(val)

    try:
        if float(val) == int(val):
            return int(val)
        return float(val)
    except Exception:
        try:
            return float(val)
        except Exception:
            # Y is string.
            return val


def _get_val(k, d, processing_func):
    toks = k.split(".")
    try:
        val = d[toks[0]]
        for t in toks[1:]:
            try:
                val = val[t]
            except TypeError:
                # Handle integer indices
                val = val[int(t)]
        val = process(val, processing_func)
    except Exception:
        # Return the base value if we cannot descend into the data.
        val = None
    return val


def _search_dict(dictionary, substr):
    result = []
    for key in dictionary:
        if substr.lower() in key.lower():
            result.append(key)
    return result


if "additional_endpoints" in SETTINGS:
    for rule, endpoint in SETTINGS["additional_endpoints"].items():
        toks = endpoint.rsplit(".", 1)
        if len(toks) == 1:
            func = globals()["__builtins__"][toks[0]]
        else:
            mod = __import__(toks[0], globals(), locals(), [toks[1]], 0)
            func = getattr(mod, toks[1])
        app.add_url_rule(rule, view_func=func)


if __name__ == "__main__":
    app.run(debug=True)
