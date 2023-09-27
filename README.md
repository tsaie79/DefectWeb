# Introduction
This website is for demostration of defect databases containing the following information:
- Defect calculations with r2SCAN functional
- Defect calculations with HSE functional


# How to deploy
## Prerequisites: creating the raw data
1. Create a folder named `static/mateials` and put all the raw data in it.
2. Run `tools.py` to generate the raw data for the website, including structures and diagrams.
    - Notice that the arguments of the function `run_defect_state.plot_ipr_vs_tot_proj` in `get_doc.get_ev_ipr` in `tools.py` should be modified according to the raw data.
3. Some raw data can't comply with the general arguments for the above function and should be treated differently. Thus, run `update_figures.py`.

## Deploy the website
1. Install the required packages in `requirements.txt`.
2. Copy the this `r2SCAN` or `HSE` folder to site-packages of your python environment, and rename it as `flamyngo`.
3. Go to the directory `flamyngo` and run `flm -c config.yaml` to deploy the website.