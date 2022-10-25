import streamlit as st
from utils import   import_data, \
                    run_pulp_model, \
                    run_monte_carlo_sim, \
                    get_optimal_production_variables, \
                    get_shadow_prices_and_slack, \
                    get_optimal_production_sites
from collections import defaultdict
from pathlib import Path
import pickle
import pulp
from pulp import *
import plotly.express as px


# make directory to save simulation results
rootdir = os.getcwd()
SIMPATH = Path(rootdir) / 'simulation'
Path(SIMPATH).mkdir(parents=True, exist_ok=True)


def run_optimize_app():
    # select parameters
    n_experiments = st.slider(label='select number of monte-carlo simulations', min_value=10, max_value=1000, value=10, step=10)
    fixcost_sd_selected = st.slider(label='select relative fix-cost standard deviation', min_value=0.0, max_value=1.0, value=.05, step=0.05)
    varcost_sd_selected = st.slider(label='select relative variable-cost standard deviation', min_value=0.0, max_value=1.0, value=.05, step=0.05)
    fixcost_bias_selected = st.slider(label='select relative fix-cost bias', min_value=0.5, max_value=1.5, value=1.0, step=0.05)
    varcost_bias_selected = st.slider(label='select relative variable-cost bias', min_value=0.5, max_value=1.5, value=1.0, step=0.05)
    
    if st.button('Run Simulation'):

        # run monte-carlo simulation
        model, \
        production_costs, \
        opt_var_dict, \
        shadowprice_dict, \
        slack_dict, \
        optimal_prodsites_dict = run_monte_carlo_sim(   n_experiments, 
                                                        fixcost_sd_selected, 
                                                        varcost_sd_selected, 
                                                        fixcost_bias_selected, 
                                                        varcost_bias_selected)

        # Save simulation results
        filehandler = open(SIMPATH / "pulp_model","wb")
        pickle.dump(model, filehandler)
        filehandler.close()

        filehandler = open(SIMPATH / "production_costs","wb")
        pickle.dump(production_costs, filehandler)
        filehandler.close()

        filehandler = open(SIMPATH / "shadowprice_dict","wb")
        pickle.dump(shadowprice_dict, filehandler)
        filehandler.close()

        filehandler = open(SIMPATH / "slack_dict","wb")
        pickle.dump(slack_dict, filehandler)
        filehandler.close()

        filehandler = open(SIMPATH / "optimal_prodsites_dict","wb")
        pickle.dump(optimal_prodsites_dict, filehandler)
        filehandler.close()


    ###########################################################
    # Figures
    ###########################################################


    # plot production costs distribution
    st.subheader('Production Cost Distribution')
    file = open(SIMPATH / "production_costs",'rb')
    production_costs = pickle.load(file)
    file.close()
    fig = px.histogram(production_costs, 
                        histnorm = 'probability',
                        width = 500,
                        title="Production Costs Distributon")
    st.plotly_chart(fig)


    
    # plot shadow price distribution
    st.subheader('Show Shadow Price and Slack for each Constraint')
    file = open(SIMPATH / "pulp_model",'rb')
    model = pickle.load(file)
    file.close()
    # select constraint
    constraint_selected = st.selectbox(label='select constraint', options=['_C1', '_C2', '_C3','_C4','_C5','_C6','_C7'])
    st.write(str(model.constraints[constraint_selected]))

    file = open(SIMPATH / "shadowprice_dict",'rb')
    shadowprice_dict = pickle.load(file)
    file.close()
    fig = px.histogram(shadowprice_dict[constraint_selected],  
                        histnorm = 'probability',
                        width = 500,
                        title="Shadow-Price Distributon: "+constraint_selected)
    st.plotly_chart(fig)

    # plot slack distribution
    file = open(SIMPATH / "slack_dict",'rb')
    slack_dict = pickle.load(file)
    file.close()
    fig = px.histogram(slack_dict[constraint_selected],  
             histnorm = 'probability',
             width = 500,
             title="Slack Distributon: "+constraint_selected)
    st.plotly_chart(fig)


    # plot optimal production sites distribution
    st.subheader('Show Optimal Production Site Locations')
    # select production site
    _, _, _, _, loc, _ = import_data()
    productionsite_selected = st.selectbox(label='select production site', options=loc)

    file = open(SIMPATH / "optimal_prodsites_dict",'rb') 
    optimal_prodsites_dict = pickle.load(file)
    file.close()

    fig = px.histogram(optimal_prodsites_dict[productionsite_selected],
                    histnorm = 'probability',
                    range_x = [-.5,1.5],
                    width = 500,
                    title="Production Site Distribution for " + productionsite_selected)
    st.plotly_chart(fig)