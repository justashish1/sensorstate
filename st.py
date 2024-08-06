import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Set page layout to wide mode
st.set_page_config(layout="wide")

# Initialize session state attributes
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'all_columns' not in st.session_state:
    st.session_state.all_columns = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'file_last_modified' not in st.session_state:
    st.session_state.file_last_modified = None
if 'plots' not in st.session_state:
    st.session_state.plots = []
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 10.0  # Default to 10 seconds
if 'last_saved_time' not in st.session_state:
    st.session_state.last_saved_time = time.time()

# Define file to save session state
session_state_file = 'session_state.pkl'

# Function to save session state to a file
def save_session_state():
    session_state_data = {
        'file_path': st.session_state.file_path,
        'df': st.session_state.df,
        'all_columns': st.session_state.all_columns,
        'auto_refresh': st.session_state.auto_refresh,
        'file_last_modified': st.session_state.file_last_modified,
        'plots': st.session_state.plots,
        'refresh_interval': st.session_state.refresh_interval
    }
    pd.to_pickle(session_state_data, session_state_file)
    logging.info("Session state saved to file")

# Function to load session state from a file
def load_session_state():
    if os.path.exists(session_state_file):
        session_state_data = pd.read_pickle(session_state_file)
        st.session_state.file_path = session_state_data.get('file_path')
        st.session_state.df = session_state_data.get('df')
        st.session_state.all_columns = session_state_data.get('all_columns')
        st.session_state.auto_refresh = session_state_data.get('auto_refresh')
        st.session_state.file_last_modified = session_state_data.get('file_last_modified')
        st.session_state.plots = session_state_data.get('plots')
        st.session_state.refresh_interval = session_state_data.get('refresh_interval')
        logging.info("Session state loaded from file")

# Load session state at the start
load_session_state()

# Function to load data and detect columns
@st.cache_data
def load_data(file_path):
    logging.info("Loading data from file: %s", file_path)
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            st.error("Unsupported file format")
            return None, None

        # Detect timestamp column and all columns
        all_columns = df.columns.tolist()
        logging.info("Data loaded successfully with columns: %s", all_columns)
        return df, all_columns
    except Exception as e:
        logging.error("Error loading data: %s", e)
        st.error(f"Error loading data: {e}")
        return None, None

# Function to apply filters
def filter_data(df, timestamp_col, start_datetime, end_datetime, freq):
    logging.info("Filtering data from %s to %s with frequency %s", start_datetime, end_datetime, freq)
    try:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        df = df.dropna(subset=[timestamp_col])

        mask = (df[timestamp_col] >= start_datetime) & (df[timestamp_col] <= end_datetime)
        df = df.loc[mask]

        if freq:
            df = df.set_index(timestamp_col).resample(freq).mean().reset_index()

        logging.info("Data filtered successfully with %d records", len(df))
        return df
    except Exception as e:
        logging.error("Error filtering data: %s", e)
        st.error(f"Error filtering data: {e}")
        return pd.DataFrame()

# Function to load data into session state
def load_data_into_session(file_path):
    logging.info("Loading data into session state from path: %s", file_path)
    if file_path:
        # Clear cache before loading new data
        st.cache_data.clear()
        
        df, all_columns = load_data(file_path)
        if df is not None and all_columns is not None:
            st.session_state.df = df
            st.session_state.all_columns = all_columns
            st.session_state.last_upload = time.time()
            st.session_state.file_last_modified = os.path.getmtime(file_path)
            logging.info("Data loaded into session state successfully")
            save_session_state()
        else:
            logging.error("Data loading failed")

# Function to manually refresh the data
def refresh_data():
    logging.info("Refreshing data")
    if st.session_state.file_path:
        file_path = st.session_state.file_path
        # Clear cache before loading new data
        st.cache_data.clear()
        
        df, all_columns = load_data(file_path)
        if df is not None and all_columns is not None:
            st.session_state.df = df
            st.session_state.all_columns = all_columns
            st.session_state.file_last_modified = os.path.getmtime(file_path)
            logging.info("Data refreshed successfully")
            save_session_state()
        else:
            logging.error("Data refresh failed")

# Periodic save function
def periodic_save():
    current_time = time.time()
    if current_time - st.session_state.last_saved_time >= 10:
        save_session_state()
        st.session_state.last_saved_time = current_time

# Streamlit UI
st.title('STARENGTS LIVE TIME SERIES DATA MONITORING')
st.sidebar.header('Filters')

# Allow user to specify the file path
file_path_input = st.sidebar.text_input("File path")

# File upload option
uploaded_file = st.sidebar.file_uploader("Or upload a CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Save uploaded file to the local filesystem
    file_path = f"./{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.file_path = file_path
    load_data_into_session(st.session_state.file_path)
elif file_path_input:
    # Use the specified file path
    st.session_state.file_path = file_path_input
    load_data_into_session(st.session_state.file_path)

if st.session_state.df is not None and st.session_state.file_path is not None:
    df = st.session_state.df
    all_columns = st.session_state.all_columns

    # User specifies the timestamp and value columns
    timestamp_col = st.sidebar.selectbox("Select the timestamp column", all_columns)
    value_cols = st.sidebar.multiselect("Select the value column(s)", all_columns)

    if len(value_cols) > 0:
        # Convert datetime column to pandas datetime
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        df = df.dropna(subset=[timestamp_col])

        # Detect minimum and maximum datetime values
        min_datetime = df[timestamp_col].min()
        max_datetime = df[timestamp_col].max()

        # Display detected format
        st.sidebar.write(f"Detected start datetime: {min_datetime}")
        st.sidebar.write(f"Detected end datetime: {max_datetime}")

        st.sidebar.markdown("<hr>", unsafe_allow_html=True)

        # Add plot button and name input
        plot_name = st.sidebar.text_input("Plot Name")
        if st.sidebar.button('Add Plot'):
            st.session_state.plots.append((timestamp_col, value_cols, plot_name, min_datetime, max_datetime, 'Line', 'None'))
            save_session_state()

        # Select plot to apply filters
        plot_names = ["All"] + [plot[2] for plot in st.session_state.plots]
        selected_plot = st.sidebar.selectbox("Select Plot", plot_names)

        st.sidebar.markdown("<hr>", unsafe_allow_html=True)

        # Date input for start datetime
        start_date = st.sidebar.date_input('Start date', value=min_datetime.date(), min_value=min_datetime.date(), max_value=max_datetime.date())

        # Generate time options
        time_options = [f"{hour:02}:{minute:02}" for hour in range(24) for minute in range(60)]

        # Time input for start datetime
        start_time_str = st.sidebar.selectbox('Start time', time_options, index=time_options.index(min_datetime.strftime('%H:%M')))
        end_date = st.sidebar.date_input('End date', value=max_datetime.date(), min_value=min_datetime.date(), max_value=max_datetime.date())
        end_time_str = st.sidebar.selectbox('End time', time_options, index=time_options.index(max_datetime.strftime('%H:%M')))

        # Combine date and time
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            st.error("Invalid time format. Please use HH:MM.")
            start_time = min_datetime.time()
            end_time = max_datetime.time()

        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        st.sidebar.markdown("<hr>", unsafe_allow_html=True)

        # Auto-refresh interval input
        st.sidebar.write("Auto-Refresh Settings")
        refresh_interval = st.sidebar.number_input('Auto-refresh interval (seconds)', min_value=0.1, max_value=86400.0, value=st.session_state.refresh_interval, step=0.1, key="refresh_interval_input")
        
        if st.sidebar.button('Start Auto-Refresh', key="start_auto_refresh"):
            st.session_state.auto_refresh = True
            st.session_state.refresh_interval = refresh_interval
            save_session_state()
            st.experimental_rerun()

        if st.sidebar.button('Stop Auto-Refresh', key="stop_auto_refresh"):
            st.session_state.auto_refresh = False
            save_session_state()
            st.experimental_rerun()

        # Display the current auto-refresh status
        if st.session_state.auto_refresh:
            st.sidebar.write("Auto-Refresh is currently: **Running**")
        else:
            st.sidebar.write("Auto-Refresh is currently: **Stopped**")

        st.sidebar.markdown("<hr>", unsafe_allow_html=True)

        if st.sidebar.button('Manual Refresh Data'):
            refresh_data()
            st.experimental_rerun()

        if st.sidebar.button("Show All Plots"):
            st.experimental_rerun()

        # Display data with Plotly for each plot configuration
        plot_indices_to_remove = []
        for i, plot_config in enumerate(st.session_state.plots):
            timestamp_col, value_cols, plot_name, plot_min_datetime, plot_max_datetime, plot_type, plot_freq = plot_config

            if selected_plot == "All" or selected_plot == plot_name:
                if plot_freq not in ['None', 'Minute', 'Hour', 'Daily', 'Weekly', 'Monthly', 'Yearly']:
                    plot_freq = 'None'

                freq = st.selectbox(f'Frequency for {plot_name}', ['None', 'Minute', 'Hour', 'Daily', 'Weekly', 'Monthly', 'Yearly'], index=['None', 'Minute', 'Hour', 'Daily', 'Weekly', 'Monthly', 'Yearly'].index(plot_freq), key=f'freq_{i}')
                freq_dict = {'None': None, 'Minute': 'T', 'Hour': 'H', 'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}
                plot_freq = freq_dict[freq]
                st.session_state.plots[i] = (timestamp_col, value_cols, plot_name, plot_min_datetime, plot_max_datetime, plot_type, freq)

                filtered_df = filter_data(df, timestamp_col, start_datetime, end_datetime, plot_freq)
                if not filtered_df.empty:
                    st.subheader(f"Plot: {plot_name}")
                    plot_type = st.selectbox(f'Select plot type for {plot_name}', ['Line', 'Pie', 'Box', 'Bar', 'Stacked Bar', 'Count', 'Scatter', 'Correlation'], index=['Line', 'Pie', 'Box', 'Bar', 'Stacked Bar', 'Count', 'Scatter', 'Correlation'].index(plot_type), key=f'plot_type_{i}')
                    
                    if plot_type == 'Line':
                        fig = px.line(filtered_df, x=timestamp_col, y=value_cols, title=f'Sensor Data Over Time - {plot_name}', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Pie':
                        fig = px.pie(filtered_df, names=timestamp_col, values=value_cols[0], title=f'Sensor Data Pie Chart - {plot_name}', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Box':
                        fig = px.box(filtered_df, x=timestamp_col, y=value_cols, title=f'Sensor Data Box Plot - {plot_name}', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Bar':
                        fig = px.bar(filtered_df, x=timestamp_col, y=value_cols, title=f'Sensor Data Bar Plot - {plot_name}', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Stacked Bar':
                        fig = px.bar(filtered_df, x=timestamp_col, y=value_cols, title=f'Sensor Data Stacked Bar Plot - {plot_name}', barmode='stack', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Count':
                        fig = px.histogram(filtered_df, x=timestamp_col, y=value_cols, title=f'Count Plot - {plot_name}', histfunc='count', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Scatter':
                        fig = px.scatter(filtered_df, x=timestamp_col, y=value_cols, title=f'Scatter Plot - {plot_name}', color_discrete_sequence=['#32c800', '#FF0000'])
                    elif plot_type == 'Correlation':
                        corr = filtered_df[value_cols].corr()
                        fig = px.imshow(corr, text_auto=True, title=f'Correlation Plot - {plot_name}')

                    # Display a message if the data is resampled
                    if plot_freq is not None:
                        st.markdown(f"*Data resampled using mean for {freq.lower()} frequency*")

                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("<hr>", unsafe_allow_html=True)

                    if st.button(f'Remove Plot {plot_name}', key=f'remove_plot_{i}'):
                        plot_indices_to_remove.append(i)

        for i in reversed(plot_indices_to_remove):
            del st.session_state.plots[i]
            save_session_state()

        # Data Entry for Adding New Data
        st.sidebar.markdown("<hr>", unsafe_allow_html=True)
        
        st.sidebar.header("Add New Data")
        new_date = st.sidebar.date_input("Date", value=max_datetime.date())
        new_time_str = st.sidebar.selectbox("Time", time_options)
        new_value = st.sidebar.number_input("Value", value=0)
        new_value_col = st.sidebar.selectbox("Select the value column to add data to", value_cols)

        if st.sidebar.button("Add Data"):
            try:
                new_time = datetime.strptime(new_time_str, '%H:%M').time()
                new_datetime = datetime.combine(new_date, new_time)
                new_data = pd.DataFrame({timestamp_col: [new_datetime], new_value_col: [new_value]})
                st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
                st.session_state.df[timestamp_col] = pd.to_datetime(st.session_state.df[timestamp_col], errors='coerce')
                st.session_state.df = st.session_state.df.dropna(subset=[timestamp_col])
                st.session_state.df = st.session_state.df.sort_values(by=timestamp_col).reset_index(drop=True)

                # Save updated data back to the file
                if st.session_state.file_path.endswith('.csv'):
                    st.session_state.df.to_csv(st.session_state.file_path, index=False)
                elif st.session_state.file_path.endswith('.xlsx') or st.session_state.file_path.endswith('.xls'):
                    st.session_state.df.to_excel(st.session_state.file_path, index=False)

                st.write("Data added successfully")
                save_session_state()
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error adding data: {e}")

        # Auto-refresh logic
        if st.session_state.auto_refresh:
            logging.info("Auto-refresh enabled, waiting for %d seconds", st.session_state.refresh_interval)
            while st.session_state.auto_refresh:
                time.sleep(st.session_state.refresh_interval)
                periodic_save()
                if st.session_state.file_path:
                    current_mod_time = os.path.getmtime(st.session_state.file_path)
                    if st.session_state.file_last_modified != current_mod_time:
                        refresh_data()
                    st.experimental_rerun()

else:
    st.write("Please upload a CSV or Excel file to display the data.")
