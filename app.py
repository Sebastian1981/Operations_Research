import streamlit as st
from eda import run_eda_app
from optimize import run_optimize_app



def main():
    st.title('Demo Web-App: Supply Chain Optimization using Linear Programming')
    menu = ["About this Project", "Exploratory Data Analysis", "Supply Chain Optimization"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == 'About this Project':
        st.header('About this Project')
        st.write('Disclaimer (before moving on): xxx')
        #run_project_description_app()

    elif choice == 'Exploratory Data Analysis':
        st.header('Check Your Data!')
        run_eda_app()

    elif choice == 'Supply Chain Optimization':
        st.header('Optimize Your Supply Chain!')
        run_optimize_app()    

if __name__ == "__main__":
    main()