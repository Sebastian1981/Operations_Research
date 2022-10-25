import pandas as pd
import pulp
from pulp import *
import random
import streamlit as st
from collections import defaultdict

@st.cache
def import_data()->pd.DataFrame:
    """Import fix costs, variable costs, demand and capacities and return them as dataframe"""
    # import fix_costs data
    fix_cost = pd.read_csv('./data/fixcosts.csv', sep=';', index_col='Supply_Region')
    # import var_costs data
    var_cost = pd.read_csv('./data/varcosts.csv', sep=';', index_col='Supply_Region')
    # import demand data
    demand = pd.read_csv('./data/demand.csv', sep=';', index_col='Supply_Region')
    demand['Dmd'] = demand['Dmd'].replace(regex=r',', value='.').astype(float)
    # import capacity data
    cap = pd.read_csv('./data/capacity.csv', sep=';', index_col='Supply_Region')
    # get locations
    loc = list(fix_cost.index) 
    # get production sizes
    size = list(fix_cost.columns) 

    return fix_cost, var_cost, demand, cap, loc, size

def run_pulp_model(fixcost_bias=0.0, fixcost_sd=0.05, varcost_bias=0.0, varcost_sd=0.05):
    """run the pulp model. Input the bias and the standard deviation for the fixcost/varcost estimates"""
    ##################################
    # Import Data
    ##################################
    fix_cost, var_cost, demand, cap, loc, size = import_data()

    ##################################
    # Init model and define Variables
    ##################################
    # Initialize Class
    model = LpProblem("Capacitated Plant Location Model", LpMinimize)
    # Define Decision Variables
    x = LpVariable.dicts("production_", [(i,j) for i in loc for j in loc], lowBound=0, upBound=None, cat='Continuous') # fraction of e.g. thousands
    y = LpVariable.dicts("plant_", [(i,s) for s in size for i in loc], cat='Binary') # is plant open or not

    ##################################
    # Define objective function
    ##################################
    # Define Objective Function
    model += (lpSum([(fix_cost.loc[i,s] + random.normalvariate(fix_cost.loc[i,s]*fixcost_bias, fix_cost.loc[i,s]*fixcost_sd)) *y[(i,s)] for s in size for i in loc]) + 
              lpSum([(var_cost.loc[i,j] + random.normalvariate(var_cost.loc[i,j]*varcost_bias, var_cost.loc[i,j]*varcost_sd)) *x[(i,j)] for i in loc for j in loc]))

    ##################################
    # Define constraints
    ##################################
    # Define the Constraints
    for j in loc: 
        model += lpSum([x[(i, j)] for i in loc]) == demand.loc[j, 'Dmd'] # production must meet demand

    for i in loc: 
        model += lpSum([x[(i, j)] for j in loc]) <= lpSum([cap.loc[i,s]*y[(i,s)] for s in size]) # produce equal or below local capacity

    ##################################
    # Solve Problem
    ##################################
    # Solve
    model.solve()
    #print('Model Status: ', LpStatus[model.status])

    return model, x, y # return model and decision variables


def run_monte_carlo_sim(n_experiments, fixcost_sd_selected, varcost_sd_selected, fixcost_bias_selected, varcost_bias_selected):
    """run montecarlo simulation"""
    _, _, _, _, loc, size = import_data()
    production_costs = [] # save minimal production costs
    opt_var_dict = defaultdict(list) # save optimal variable values i.e. quantities produced
    optimal_prodsites_dict = defaultdict(list) # save optimal production site
    shadowprice_dict= defaultdict(list) # save shadow prices for each constraint
    slack_dict = defaultdict(list) # save slack for each constraint

    # loop over Monte-Carlo Simulations
    for rep in range(n_experiments):
        # run model
        model, x, y = run_pulp_model(fixcost_bias=fixcost_bias_selected, 
                                    fixcost_sd=fixcost_sd_selected, 
                                    varcost_bias=varcost_bias_selected, 
                                    varcost_sd=varcost_sd_selected)
        
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
    
    return model, production_costs, opt_var_dict, shadowprice_dict, slack_dict, optimal_prodsites_dict



def get_shadow_prices_and_slack(model)->pd.DataFrame:
    # get Shadow Price
    o = [{'name':name, 'shadow price':c.pi, 'slack': c.slack} for name, c in model.constraints.items()]
    return pd.DataFrame(o)

def get_optimal_production_variables(prod_var, locations)->pd.DataFrame:
    o = [{'prod':"{} to {}".format(i,j), 'quant':prod_var[(i,j)].varValue} for i in locations for j in locations]
    return pd.DataFrame(o)

def get_optimal_production_sites(prod_site_var, locations, warehouse_size)->pd.DataFrame:
    o = [{'loc':i, 'lc':prod_site_var[(i,warehouse_size[0])].varValue, 'hc':prod_site_var[(i,warehouse_size[1])].varValue} for i in locations]
    return pd.DataFrame(o) 