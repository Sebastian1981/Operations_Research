import streamlit as st
from utils import import_data, run_pulp_model, get_optimal_production_variables, get_shadow_prices_and_slack, get_optimal_production_sites
from collections import defaultdict
import pulp
from pulp import *
import plotly.express as px

def run_optimize_app():
    _, _, _, _, loc, size = import_data()
    production_costs = [] # save minimal production costs
    opt_var_dict = defaultdict(list) # save optimal variable values i.e. quantities produced
    optimal_prodsites_dict = defaultdict(list) # save optimal production site
    shadowprice_dict= defaultdict(list) # save shadow prices for each constraint
    slack_dict = defaultdict(list) # save slack for each constraint

    # loop over Monte-Carlo Simulations
    for rep in range(20):
        # run model
        model, x, y = run_pulp_model(fixcost_bias=0.0, fixcost_sd=0.1, varcost_bias=0.0, varcost_sd=0.1)
        
        # get production prices
        pc = value(model.objective)
        production_costs.append(pc)

        # get optimal production quantities
        df_var_opt = get_optimal_production_variables(x, loc)
        for n in range(len(df_var_opt)):
            site = df_var_opt.iloc[n,0]
            q = df_var_opt.iloc[n,1]
            opt_var_dict[site].append(q)

        # get shadow prices
        shadowprices_slack_df = get_shadow_prices_and_slack(model)
        for n in range(len(shadowprices_slack_df)):
            constraint = shadowprices_slack_df.iloc[n,0]
            sp = shadowprices_slack_df.iloc[n,1]
            shadowprice_dict[constraint].append(sp)

        # get slacks
        shadowprices_slack_df = get_shadow_prices_and_slack(model)
        for n in range(len(shadowprices_slack_df)):
            constraint = shadowprices_slack_df.iloc[n,0]
            slack = shadowprices_slack_df.iloc[n,2]
            slack_dict[constraint].append(slack) 

        # get optimal production locations
        optimal_prodsites_df = get_optimal_production_sites(y, loc, size)
        for n in range(len(optimal_prodsites_df)):
            site = optimal_prodsites_df.iloc[n,0]
            lc = optimal_prodsites_df.iloc[n,1]
            hc = optimal_prodsites_df.iloc[n,2]
            optimal_prodsites_dict[site].append(lc or hc) # produce either low or high capacity

    # plot production costs distribution
    fig = px.histogram(production_costs, 
                        histnorm = 'probability',
                        width = 500,
                        title="Production Costs Distributon")
    st.plotly_chart(fig)