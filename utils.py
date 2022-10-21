import pandas as pd
import pulp
from pulp import *
import random
import streamlit as st

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