import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import logging
import os
import base64
import pytz

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

# Set page layout to wide mode
st.set_page_config(page_title="SENSORSTATE", layout="wide")

# Initialize session state attributes for the main app
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
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

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
        'refresh_interval': st.session_state.refresh_interval,
        'authenticated': st.session_state.authenticated
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
        st.session_state.plots = session_state_data.get('plots', [])
        st.session_state.refresh_interval = session_state_data.get('refresh_interval')
        st.session_state.authenticated = session_state_data.get('authenticated')
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

        all_columns = df.columns.tolist()
        logging.info("Data loaded successfully with columns: %s", all_columns)
        return df, all_columns
    except Exception as e:
        logging.error("Error loading data: %s", e)
        st.error(f"Error loading data: {e}")
        return None, None

# Function to apply filters
def filter_data(df, filter_col, start_val, end_val):
    logging.info("Filtering data from %s to %s", start_val, end_val)
    try:
        if pd.api.types.is_datetime64_any_dtype(df[filter_col]):
            df[filter_col] = pd.to_datetime(df[filter_col], errors='coerce')
            mask = (df[filter_col] >= start_val) & (df[filter_col] <= end_val)
        else:
            mask = (df[filter_col] >= start_val) & (df[filter_col] <= end_val)
        
        df = df.loc[mask]
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

# Load logo as base64
def load_logo(filename):
    with open(filename, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_image}"

# Custom CSS for styling
def custom_css():
    st.markdown("""
        <style>
            .main-title {
                font-size: 25px;
                color: #32c800;
                text-align: center;
                font-weight: bold;
            }
            .current-date {
                font-size: 18px;
                font-weight: bold;
                display: inline-block;
                margin-right: 20px;
            }
            .logo {
                height: 65px;
                width: auto;  /* Ensures the aspect ratio is maintained */
                display: inline-block;
                margin-left: auto;
                margin-right: 10px;
            }
            .header {
                position: relative;
                width: 100%;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                color: #32c800;
                align-items: center;
            }
            .developer-info {
                font-size: 12px;
                text-align: left;
                position: fixed;
                bottom: 10px;
                left: 150px;
                color: white;
            }
            .stButton > button {
                background-color: #32c800;
                color: white;
                border: none;
                font-weight: bold;
            }
            .stButton > button:hover {
                color: white;
                background-color: #32c800;
            }
            .custom-error {
                background-color: #32c800;
                color: white;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            .download-manual {
                font-size: 12px;
                font-weight: bold;
                position: fixed;
                bottom: 10px;
                left: 25px;
                background-color: #32c800;
                color: white !important;
                padding: 4px 8px; /* Adjusted padding to reduce the button size */
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
            }
        </style>
    """, unsafe_allow_html=True)

# Display the logo and date
def display_logo_and_date(logo_src, timezone_str):
    current_date_html = f"""
        <div class='header'>
            <div class='current-date' id='current-date'>{get_date(timezone_str)}</div>
            <img src='{logo_src}' class='logo'>
        </div>
    """
    st.markdown(current_date_html, unsafe_allow_html=True)

# Function to get the current date as a string for the clock
def get_date(timezone_str='UTC'):
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz).strftime('%Y-%m-%d')

# Add JavaScript for live date and timezone detection
def add_js_script():
    st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', (event) => {
            function updateDate() {
                var now = new Date();
                var dateString = now.getFullYear() + '-' + 
                                 ('0' + (now.getMonth() + 1)).slice(-2) + '-' + 
                                 ('0' + now.getDate()).slice(-2);
                document.getElementById('current-date').innerHTML = dateString;
            }
            setInterval(updateDate, 1000);

            var timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            var tzElement = document.createElement('input');
            tzElement.type = 'hidden';
            tzElement.id = 'timezone';
            tzElement.value = timezone;
            document.body.appendChild(tzElement);
        });
        </script>
    """, unsafe_allow_html=True)

# Authenticate user
def authenticate(username, password):
    if username == "admin" and password == "password106":
        st.session_state.authenticated = True
        save_session_state()
    else:
        st.error("Invalid username or password")

# Function to download the manual
def download_manual():
    manual_path = "Applications_manual.pdf"  # File in the same directory
    if os.path.exists(manual_path):
        with open(manual_path, "rb") as file:
            manual_data = file.read()
        file_name = os.path.basename(manual_path)
        b64 = base64.b64encode(manual_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}" class="download-manual">Download Manual</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("Manual not available. Send request to Ashish Malviya - info@starengts.com!")

# Main function for the login page
def login_page():
    custom_css()
    logo_src = load_logo('logo.png')
    add_js_script()

    query_params = st.experimental_get_query_params()
    timezone = query_params.get('timezone', ['UTC'])[0]

    display_logo_and_date(logo_src, timezone)
    st.markdown("<h1 class='main-title'>SENSORSTATE</h1>", unsafe_allow_html=True)

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            authenticate(username, password)
            if st.session_state.authenticated:
                st.experimental_rerun()
        
        st.markdown("""
            <div class='developer-info'>
                Copyright © 2024 Starengts-All Rights Reserved, Version 1.0.21, Last updated on 08 July 2024, Visit : www.starengts.com<br>
            </div>
        """, unsafe_allow_html=True)

        download_manual()  # Add manual download button on the login screen
        st.stop()

# Main function for the time series data monitoring app
def main():
    if st.session_state.get("authenticated"):
        # Display the main app content
        st.title('SENSORSTATE')
        st.sidebar.header('Filters')

        # Allow user to specify the file path or URL
        file_path_input = st.sidebar.text_input("File path or URL")

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
            # Use the specified file path or URL
            st.session_state.file_path = file_path_input
            load_data_into_session(st.session_state.file_path)

        if st.session_state.df is not None and st.session_state.file_path is not None:
            df = st.session_state.df
            all_columns = st.session_state.all_columns

            # User specifies the filter column
            filter_col = st.sidebar.selectbox("Select the filter column", ["None"] + all_columns)

            if filter_col and len(all_columns) > 0:
                # Check if the filter column is a datetime column
                if filter_col != "None" and pd.api.types.is_datetime64_any_dtype(df[filter_col]):
                    df[filter_col] = pd.to_datetime(df[filter_col], errors='coerce')

                    # Detect minimum and maximum values
                    min_val = df[filter_col].min()
                    max_val = df[filter_col].max()

                    # Display detected format
                    st.sidebar.write(f"Detected start value: {min_val}")
                    st.sidebar.write(f"Detected end value: {max_val}")

                    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

                    # Date input for start value
                    start_val = st.sidebar.date_input('Start date', value=min_val.date(), min_value=min_val.date(), max_value=max_val.date())

                    # Generate time options
                    time_options = [f"{hour:02}:{minute:02}" for hour in range(24) for minute in range(60)]

                    # Time input for start value
                    start_time_str = st.sidebar.selectbox('Start time', time_options, index=time_options.index(min_val.strftime('%H:%M')))
                    end_val = st.sidebar.date_input('End date', value=max_val.date(), min_value=min_val.date(), max_value=max_val.date())
                    end_time_str = st.sidebar.selectbox('End time', time_options, index=time_options.index(max_val.strftime('%H:%M')))

                    # Combine date and time
                    try:
                        start_time = datetime.strptime(start_time_str, '%H:%M').time()
                        end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    except ValueError:
                        st.error("Invalid time format. Please use HH:MM.")
                        start_time = min_val.time()
                        end_time = max_val.time()

                    start_val = datetime.combine(start_val, start_time)
                    end_val = datetime.combine(end_val, end_time)

                    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

                    # Add Clear Data button
                    if st.sidebar.button("Clear Data"):
                        start_val = min_val
                        end_val = max_val

                elif filter_col != "None":
                    # Numeric filter
                    min_val = df[filter_col].min()
                    max_val = df[filter_col].max()

                    start_val = st.sidebar.slider('Start value', min_value=float(min_val), max_value=float(max_val), value=float(min_val))
                    end_val = st.sidebar.slider('End value', min_value=float(min_val), max_value=float(max_val), value=float(max_val))

                    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

                    # Add Clear Data button
                    if st.sidebar.button("Clear Data"):
                        start_val = min_val
                        end_val = max_val

                else:
                    start_val = None
                    end_val = None

                # User specifies the value columns
                value_cols = st.sidebar.multiselect("Select the value column(s)", all_columns)

                # Add plot button and name input
                plot_name = st.sidebar.text_input("Plot Name")
                plot_type = st.sidebar.selectbox('Select plot type', ['Line', 'Pie', 'Box', 'Bar', 'Stacked Bar', 'Count', 'Scatter', 'Correlation'])
                if plot_name and st.sidebar.button('Add Plot'):
                    st.session_state.plots.append({
                        'filter_col': filter_col,
                        'value_cols': value_cols,
                        'plot_name': plot_name,
                        'plot_type': plot_type,
                        'start_val': start_val,
                        'end_val': end_val
                    })
                    save_session_state()
                    st.experimental_rerun()

                st.sidebar.markdown("<hr>", unsafe_allow_html=True)

                # Select plot to apply filters
                plot_names = ["All"] + [plot['plot_name'] for plot in st.session_state.plots]
                selected_plot = st.sidebar.selectbox("Select Plot", plot_names)

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
                    if selected_plot == "All" or selected_plot == plot_config['plot_name']:
                        filtered_df = filter_data(df, plot_config['filter_col'], plot_config['start_val'], plot_config['end_val'])
                        if not filtered_df.empty:
                            st.subheader(f"Plot: {plot_config['plot_name']}")
                            plot_type = st.selectbox(f'Select plot type for {plot_config["plot_name"]}', ['Line', 'Pie', 'Box', 'Bar', 'Stacked Bar', 'Count', 'Scatter', 'Correlation'], index=['Line', 'Pie', 'Box', 'Bar', 'Stacked Bar', 'Count', 'Scatter', 'Correlation'].index(plot_config['plot_type']), key=f'plot_type_{i}')
                            
                            if plot_type == 'Line':
                                fig = px.line(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Sensor Data Over Time - {plot_config["plot_name"]}', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Pie':
                                fig = px.pie(filtered_df, names=plot_config['filter_col'], values=plot_config['value_cols'][0], title=f'Sensor Data Pie Chart - {plot_config["plot_name"]}', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Box':
                                fig = px.box(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Sensor Data Box Plot - {plot_config["plot_name"]}', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Bar':
                                fig = px.bar(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Sensor Data Bar Plot - {plot_config["plot_name"]}', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Stacked Bar':
                                fig = px.bar(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Sensor Data Stacked Bar Plot - {plot_config["plot_name"]}', barmode='stack', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Count':
                                fig = px.histogram(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Count Plot - {plot_config["plot_name"]}', histfunc='count', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Scatter':
                                fig = px.scatter(filtered_df, x=plot_config['filter_col'], y=plot_config['value_cols'], title=f'Scatter Plot - {plot_config["plot_name"]}', color_discrete_sequence=['#32c800', '#FF0000'])
                            elif plot_type == 'Correlation':
                                corr = filtered_df[plot_config['value_cols']].corr()
                                fig = px.imshow(corr, text_auto=True, title=f'Correlation Plot - {plot_config["plot_name"]}')

                            st.plotly_chart(fig, use_container_width=True)

                            st.markdown("<hr>", unsafe_allow_html=True)

                            if st.button(f'Remove Plot {plot_config["plot_name"]}', key=f'remove_plot_{i}'):
                                plot_indices_to_remove.append(i)

                for i in reversed(plot_indices_to_remove):
                    del st.session_state.plots[i]
                    save_session_state()

                # Data Entry for Adding New Data
                st.sidebar.markdown("<hr>", unsafe_allow_html=True)
                
                st.sidebar.header("Add New Data")
                new_date = st.sidebar.date_input("Date", value=max_val.date() if filter_col != "None" else datetime.now().date())
                new_time_str = st.sidebar.selectbox("Time", time_options)
                new_value = st.sidebar.number_input("Value", value=0)
                new_value_col = st.sidebar.selectbox("Select the value column to add data to", all_columns)

                if st.sidebar.button("Add Data"):
                    try:
                        new_time = datetime.strptime(new_time_str, '%H:%M').time()
                        new_datetime = datetime.combine(new_date, new_time)
                        new_data = pd.DataFrame({filter_col if filter_col != "None" else new_value_col: [new_datetime], new_value_col: [new_value]})
                        st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
                        if filter_col != "None":
                            st.session_state.df[filter_col] = pd.to_datetime(st.session_state.df[filter_col], errors='coerce')
                            st.session_state.df = st.session_state.df.dropna(subset=[filter_col])
                            st.session_state.df = st.session_state.df.sort_values(by=filter_col).reset_index(drop=True)

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

        # Logout button at the bottom of the sidebar
        st.sidebar.markdown("<hr>", unsafe_allow_html=True)
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            save_session_state()
            st.markdown("""
                <script>
                window.location.href = window.location.href.split('?')[0];
                </script>
            """, unsafe_allow_html=True)

    else:
        login_page()

if __name__ == "__main__":
    main()
