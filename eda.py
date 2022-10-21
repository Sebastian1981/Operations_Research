import streamlit as st
from utils import import_data

def run_eda_app():
    fix_cost, var_cost, demand, cap, loc, size = import_data()
    st.write('Fix Costs:')
    st.write(fix_cost)
    st.write('Variable Costs:')
    st.write(var_cost)
    st.write('Demands:')
    st.write(demand)
    st.write('Warehouse Capacities:')
    st.write(cap)