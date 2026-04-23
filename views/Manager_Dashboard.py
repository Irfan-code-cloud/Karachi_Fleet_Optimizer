from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import math
import requests
from streamlit_folium import st_folium
from src.routing_engine import solve_cvrp
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import uuid
import json
import vertexai
from vertexai.generative_models import GenerativeModel
import json
import os

# --- AI INITIALIZATION FUNCTION ---
@st.cache_resource
def load_ai_model():
    """Initializes the Vertex AI model securely."""
    if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
        creds_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
        key_path = "temp_gcp_key.json"
        with open(key_path, "w") as f:
            json.dump(creds_dict, f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        vertexai.init(project=creds_dict["project_id"], location="us-central1")
        return GenerativeModel("gemini-2.5-flash")
    return None

ai_model = load_ai_model()

# Setup Page
st.set_page_config(page_title="Karachi Fleet Optimizer", layout="wide", page_icon=":material/local_shipping:")

# 1. Mobile Responsiveness Injection
st.markdown("""
    <style>
    /* Standard global styling to remove standard Streamlit margins if needed */
    .block-container {
        max-width: 100% !important;
        margin: 0 auto !important;
    }

    /* --- Mobile Viewport Breakpoint (Smaller than 768px) --- */
    @media screen and (max-width: 768px) {
        /* 1. Shrink KPI Metrics (st.metric) */
        /* This target the big numbers (e.g., '1', '100%') */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important; /* Significantly reduce number size */
            line-height: 1.2 !important;
        }
        /* This targets the labels/changes underneath the number */
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.75rem !important; /* Slightly reduce label size */
            color: #6B7280 !important; /* Force subtle grey label on mobile */
        }
        /* Tighten up the padding between metrics on mobile */
        div[data-testid="column"] {
            margin-bottom: 0px !important;
            padding-top: 5px !important;
            padding-bottom: 5px !important;
        }

        /* h1: Main Title ("Karachi Fleet Optimizer") */
        div[data-testid="stMarkdownContainer"] h1 {
            font-size: 1.25rem !important;
            margin-top: -0.5rem !important;
            line-height: 1.2 !important;
        }
        
        /* h2: Section Headers ("Fleet Overview") */
        div[data-testid="stMarkdownContainer"] h2 {
            font-size: 1.4rem !important;
        }
        /* h3: Subheaders ("Active Route Ledger", "System Logs") */
        div[data-testid="stMarkdownContainer"] h3 {
            font-size: 1.15rem !important;
            padding-top: 10px !important;
        }

        /* 3. Global Spacing Fixes */
        .block-container {
            padding-top: 0 !important; /* Prevent header overlay */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Remove the massive default top padding from the main block container */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
    }
    /* Inject a sleek SaaS drop-shadow to all bordered containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
    }
    /* Add a smooth hover animation so the cards 'lift' when interacted with */
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04) !important;
        transform: translateY(-2px) !important;
    }
    /* Master Sidebar Navigation Fix */
    [data-testid="stSidebarNav"] {
        padding-top: 0px !important; 
    }
    
    [data-testid="stSidebarNav"]::before {
        content: "Manager Control Menu";
        display: block !important;
        position: static !important;
        padding-left: 1rem !important;
        padding-top: 0px !important;
        padding-bottom: 15px !important;
        font-size: 1.25rem;
        font-weight: 800;
        /* color: ; */
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title(":material/local_shipping: Karachi Fleet Optimizer")
# Refresh the page every 30 seconds to fetch live driver updates
# st_autorefresh(interval=30000, key="datarefresh")
st.markdown("Optimize your logistics network using mathematically minimal distances across Karachi.")

# Inject this ROI explanation:
st.info("**How this system saves money:** The routing engine uses advanced algorithms to eliminate overlapping routes and backtracking. By mathematically minimizing the total kilometers driven, it directly slashes daily fuel consumption and fleet maintenance costs.", icon=":material/tips_and_updates:")

# --- FIREBASE SETUP ---
if not firebase_admin._apps:
    # 1. CLOUD DEPLOYMENT: Read from Streamlit Secrets
    if "firebase" in st.secrets:
        cert_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cert_dict)
    # 2. LOCAL DEVELOPMENT: Read from the JSON file
    else:
        cred = credentials.Certificate('firebase_credentials.json')
        
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://karachi-fleet-db-default-rtdb.firebaseio.com/'
    })

# --- INITIALIZE SESSION STATE ---
if 'route_calculated' not in st.session_state:
    st.session_state.route_calculated = False
if 'delivery_status' not in st.session_state:
    st.session_state.delivery_status = {}
if 'actual_routes' not in st.session_state:
    st.session_state.actual_routes = []
if 'fleet_data' not in st.session_state:
    st.session_state.fleet_data = None
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False
if 'show_toast' not in st.session_state:
    st.session_state.show_toast = False
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# Process any cached Toasts natively
if st.session_state.show_toast:
    st.toast("Report Saved to Ledger!", icon=":material/task_alt:")
    st.session_state.show_toast = False
    
def nuke_active_data():
    # 1. Wipe Firebase
    try:
        db.reference('/active_fleet_data').delete()
        db.reference('/routes').delete()
    except Exception:
        pass
    
    # 2. The Nuclear Option: Completely obliterate all session components
    st.session_state.clear()

# Safely recover map data and KPIs from the cloud on refresh
if "optimized_routes" not in st.session_state:
    st.session_state.optimized_routes = []
if "kpis" not in st.session_state:
    st.session_state.kpis = {}

try:
    active_payload = db.reference('/active_route_payload').get()
    if active_payload:
        st.session_state.optimized_routes = active_payload.get('routes', [])
        st.session_state.kpis = active_payload.get('kpis', {})
        # Map back to existing logic variable natively
        st.session_state.actual_routes = st.session_state.optimized_routes
        st.session_state.route_calculated = True
except Exception:
    pass

import uuid

st.sidebar.markdown("### :material/sensors: Live Telemetry")
# 1. A toggle to turn auto-refresh on or off
live_sync = st.sidebar.toggle("Enable Live Auto-Sync", value=False)

if live_sync:
    # If turned on, it refreshes every 60 seconds
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="live_sync_refresh")
    st.sidebar.caption("🟢 Auto-sync is active (60s)")
else:
    # 2. A manual button so they can just check for updates when they want to
    if st.sidebar.button(":material/refresh: Manually Refresh Data", use_container_width=True):
        st.rerun()

st.sidebar.divider()

st.sidebar.markdown("### :material/folder_open: Zone 1: Data Management")

# 1. Initialize persistent keys
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False

# 2. Render Uploader with dynamic key
uploaded_file = st.sidebar.file_uploader("Upload CSV...", type=['csv'], key=st.session_state.uploader_key)

# 3. Firebase Loading Failsafe
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.session_state.fleet_data = df

    # Sanitize numpy datatypes to pure Python types via JSON stringification
    safe_json_data = json.loads(df.to_json(orient='records'))
    db.reference('/active_fleet_data').set(safe_json_data)
elif db.reference('/active_fleet_data').get():
    st.session_state.fleet_data = pd.DataFrame(db.reference('/active_fleet_data').get())
    st.sidebar.success("Loaded active data from cloud.")
else:
    st.session_state.fleet_data = None

# 4. Two-Step Synchronous Deletion
if st.session_state.fleet_data is not None:
    if not st.session_state.confirm_clear:
        if st.sidebar.button(":material/delete: Clear Active Data"):
            st.session_state.confirm_clear = True
            st.rerun()
    else:
        st.sidebar.error("Are you sure? This will remove the active route.", icon=":material/warning:")
        c1, c2 = st.sidebar.columns(2)
        if c1.button("Cancel"):
            st.session_state.confirm_clear = False
            st.rerun()
        if c2.button("Yes, Delete", type="primary"):
            # Wipe Firebase
            db.reference('/active_fleet_data').delete()
            # Wipe Local State
            st.session_state.fleet_data = None
            st.session_state.confirm_clear = False
            # MUTATE THE WIDGET KEY
            st.session_state.uploader_key = str(uuid.uuid4())
            st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### :material/settings: Zone 2: Route Controls")
num_trucks = st.sidebar.number_input("Number of Trucks", min_value=1, max_value=50, value=3)
vehicle_capacity = st.sidebar.number_input("Vehicle Capacity (KG)", min_value=500, max_value=5000, value=1500, step=100)

st.sidebar.divider()
st.sidebar.markdown("### :material/payments: Zone 3: Economics & Logistics")
with st.sidebar.form("economics_form"):
    current_fuel_price = st.number_input("Diesel Price (PKR/L)", min_value=1.0, value=385.54, step=1.0)
    fleet_efficiency = st.number_input("Fleet Efficiency (km/L)", min_value=1.0, value=8.0, step=0.5)
    submitted = st.form_submit_button("Update Financials")
    
st.sidebar.divider()
if st.session_state.fleet_data is not None:
    if st.sidebar.button(":material/rocket_launch: Optimize Routes", use_container_width=True, type="secondary"):
        st.session_state.route_calculated = True
        st.session_state.actual_routes = []

COLORS = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']

# --- MAIN APP LOGIC ---
if st.session_state.fleet_data is not None:
    df = st.session_state.fleet_data

    if st.session_state.route_calculated:
        
        if not st.session_state.actual_routes:
            with st.spinner("Optimizing using OR-Tools... & Syncing to Cloud"):
                routes = solve_cvrp(df, num_trucks, vehicle_capacity=vehicle_capacity)
                
                if routes is None:
                    st.error("No valid solution found! Try increasing the number of trucks.")
                    st.stop()
                    
                st.session_state.actual_routes = routes
                
                # Firebase Sync
                delivery_init = {}
                for loc in df.to_dict('records'):
                    stop_id = loc['Stop_ID']
                    st.session_state.delivery_status[stop_id] = "Pending"
                    delivery_init[str(stop_id)] = "Pending" 
                
                try:
                    db.reference('/').update({
                        'routes': routes,
                        'deliveries': delivery_init
                    })
                except Exception as e:
                    st.error(f"Failed to sync with Firebase: {e}")
                    
        st.success(f"Successfully optimized routes. {len(st.session_state.actual_routes)} trucks in use.")
        
        depot_lat, depot_lon = df.loc[0, 'Latitude'], df.loc[0, 'Longitude']
        m = folium.Map(location=[depot_lat, depot_lon], zoom_start=12)
        marker_cluster = MarkerCluster(name="Delivery Stops").add_to(m)
        
        folium.Marker(
            location=[depot_lat, depot_lon],
            tooltip="Depot (Port of Karachi)",
            icon=folium.Icon(color='black', icon='home')
        ).add_to(m)
        
        # --- FETCH ALL STATUSES ONCE BEFORE DRAWING ---
        try:
            live_statuses = db.reference('/deliveries').get()
            if live_statuses is None:
                live_statuses = {}
        except Exception:
            live_statuses = {}
            
        # Calculate live metrics
        total = 0
        delivered = 0
        pending = 0
        
        status_items = live_statuses if isinstance(live_statuses, list) else live_statuses.values() if isinstance(live_statuses, dict) else []
        for v in status_items:
            if v is None: 
                continue
            
            total += 1
            if isinstance(v, dict):
                s = v.get("status", "Pending")
            else:
                s = v
                
            if s == "Delivered":
                delivered += 1
            else:
                pending += 1
                
        # Distance Calculation
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0 # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c
            
        total_fleet_distance = 0.0
        for route in st.session_state.actual_routes:
            for j in range(len(route) - 1):
                lat1, lon1 = route[j]['Latitude'], route[j]['Longitude']
                lat2, lon2 = route[j+1]['Latitude'], route[j+1]['Longitude']
                total_fleet_distance += haversine(lat1, lon1, lat2, lon2)

        # KPI 5: Latest Arrival
        latest_time_str = "N/A"
        latest_mins = 0
        def parse_time_str(time_str):
            if not time_str or time_str == "N/A": return 0
            parts = time_str.split()
            if len(parts) != 2: return 0
            try:
                time_parts = parts[0].split(':')
                h, m_val = int(time_parts[0]), int(time_parts[1])
                if parts[1].upper() == 'PM' and h != 12: h += 12
                if parts[1].upper() == 'AM' and h == 12: h = 0
                return h * 60 + m_val
            except Exception:
                return 0

        for r in st.session_state.actual_routes:
            if len(r) > 0:
                arr_str = r[-1].get('Scheduled_Arrival', 'N/A')
                m_val = parse_time_str(arr_str)
                if m_val > latest_mins:
                    latest_mins = m_val
                    latest_time_str = arr_str

        st.markdown("### :material/monitoring: Live Fleet Status")
        
        # Inject this KPI context:
        st.caption("Real-time operational telemetry. **Total Distance** tracks your optimized footprint, while **Latest Return** helps predict and eliminate driver overtime costs.")
        m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1.5, 1.5])
        with m1:
            with st.container(border=True):
                st.metric(":material/inventory_2: Total Stops", total)
        with m2:
            with st.container(border=True):
                st.metric(":material/check_circle: Delivered", delivered)
        with m3:
            with st.container(border=True):
                st.metric(":material/pending: Pending", pending)
        with m4:
            with st.container(border=True):
                st.metric(":material/route: Total Distance", f"{total_fleet_distance:.1f} km")
        with m5:
            with st.container(border=True):
                st.metric(":material/schedule: Latest Return", latest_time_str)
            
        # Financial Calculations
        fuel_used_litres = total_fleet_distance / fleet_efficiency
        optimized_cost_pkr = fuel_used_litres * current_fuel_price
        
        unoptimized_distance = total_fleet_distance * 1.25
        unoptimized_cost_pkr = (unoptimized_distance / fleet_efficiency) * current_fuel_price
        
        savings_pkr = unoptimized_cost_pkr - optimized_cost_pkr
        
        # PUSH ACTIVE SESSION PAYLOAD FOR BROWSER REFRESH RECOVERY
        if st.session_state.get('route_calculated', False) and st.session_state.actual_routes:
            db.reference('/active_route_payload').set({
                'routes': st.session_state.actual_routes,
                'kpis': {
                    'fuel': fuel_used_litres,
                    'savings': savings_pkr,
                    'cost': optimized_cost_pkr
                }
            })

        st.write("")
        st.divider()
        st.write("")
        st.markdown("### :material/account_balance: Financial Impact (Estimated)") 
        
        # Inject this financial KPI context:
        st.caption("Translates route optimization into daily financial ROI. **Optimized Fuel Cost** tracks your direct operational expenses, while **Estimated Savings** highlights the capital actively recovered by avoiding inefficient, unoptimized routes.")
        f1, f2, f3 = st.columns(3)
        with f1:
            with st.container(border=True):
                st.metric(":material/local_gas_station: Fuel Consumed", f"{fuel_used_litres:.1f} Litres", delta=" ", delta_color="off")
        with f2:
            with st.container(border=True):
                st.metric(":material/payments: Optimized Fuel Cost", f"Rs. {optimized_cost_pkr:,.2f}", delta=" ", delta_color="off")
        with f3:
            with st.container(border=True):
                st.metric(":material/savings: Estimated Savings", f"Rs. {savings_pkr:,.2f}", f"+ Rs. {savings_pkr:,.2f}")

        st.divider()

        # --- AI ROUTE EFFICIENCY AUDIT ---
        if ai_model:
            # 1. Replaced the emoji with the clean system icon
            st.markdown("### :material/smart_toy: AI Route Efficiency Audit")
            
            if st.button("Run Daily Route Audit"):
                with st.spinner("AI is analyzing route efficiency and suggesting improvements..."):
                    # Compile all route data for the AI
                    all_route_data = ""
                    for i, route in enumerate(st.session_state.actual_routes):
                        if route:
                            route_str = f"Route {i+1}: "
                            for stop in route:
                                route_str += f"{stop['Location_Name']} -> "
                            route_str += "(End)"
                            all_route_data += route_str + "\n"

                            
                    current_date = datetime.now().strftime("%B %d, %Y")
                    prompt = f"""
                    You are a senior logistics consultant in Karachi. 
                    Today's date is {current_date}.
                    We have {len(st.session_state.actual_routes)} optimized routes for today.
                    Total optimized distance: {total_fleet_distance:.1f} km.
                    Estimated savings: Rs. {savings_pkr:,.2f}.

                    Here are the routes:
                    {all_route_data}

                    Please provide a professional audit report with exactly two sections:
                    1. **Efficiency Analysis:** A short paragraph on how well-optimized the routes are.
                    2. **Improvement Suggestions:** 2-3 specific, actionable tips to reduce fuel consumption or travel time further.
                    
                    Include a formal report header at the very top that includes today's exact date ({current_date}) and your consultant title. Do not invent past dates.
                    """
                    try:
                        response = ai_model.generate_content(prompt)
                        # 2. Replaced st.info with the sleek, theme-adaptive box
                        with st.container(border=True):
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Google Cloud Error: {e}")

        # Plot Routes
        st.subheader(":material/map: Geographic Route Visualization")
        st.markdown("""
        <div style="font-size: 0.95rem; color: #555; padding-bottom: 15px;">
            <strong>Map Legend:</strong> &nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: black; font-size: 1.1rem; vertical-align: middle;">⬟</span> <span style="vertical-align: middle;">Main Depot</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #2ecc71; font-size: 1.1rem; vertical-align: middle;">⬤</span> <span style="vertical-align: middle;">Delivered Stops</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #3498db; font-size: 1.1rem; vertical-align: middle;">⬤</span> <span style="vertical-align: middle;">Pending Deliveries</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="display: inline-block; width: 28px; height: 5px; background-color: #9b59b6; vertical-align: middle; border-radius: 2px;"></span> <span style="vertical-align: middle;">Assigned Routes</span>
        </div>
        """, unsafe_allow_html=True)
        
        active_ledger_data = []
        truck_names = [f"Truck {i+1}" for i in range(len(st.session_state.actual_routes))]
        
        map_col1, map_col2 = st.columns([1, 2.5], vertical_alignment="bottom")
        with map_col1:
            truck_filter = st.selectbox(":material/filter_alt: Filter by Truck", ["All Fleet"] + truck_names)
        with map_col2:
            st.caption("Select a specific truck to highlight its optimized path on the map.")

        for i, route in enumerate(st.session_state.actual_routes):
            current_truck_name = f"Truck {i+1}"
            
            if truck_filter != "All Fleet" and truck_filter != current_truck_name:
                continue
                
            color = COLORS[i % len(COLORS)]
            route_coords = [(loc['Latitude'], loc['Longitude']) for loc in route]
            
            folium.PolyLine(
                locations=route_coords,
                color=color,
                weight=4,
                opacity=0.8,
                tooltip=f"Truck {i+1}"
            ).add_to(m)
            
            for loc in route[1:-1]:
                stop_id = loc['Stop_ID']
                
                if isinstance(live_statuses, list):
                    if int(stop_id) < len(live_statuses):
                        status_val = live_statuses[int(stop_id)]
                    else:
                        status_val = "Pending"
                elif isinstance(live_statuses, dict):
                    status_val = live_statuses.get(str(stop_id), "Pending")
                else:
                    status_val = "Pending"
                    
                if status_val is None:
                    status_val = "Pending"

                photo_data = ""
                override_note = ""
                delivery_time = "N/A"
                
                if isinstance(status_val, dict):
                    status = status_val.get("status", "Pending")
                    photo_data = status_val.get("photo_data", "")
                    override_note = status_val.get("override_note", "")
                    delivery_time = status_val.get("timestamp", "N/A")
                else:
                    status = status_val

                if int(stop_id) == 0:
                    marker_color = "black"
                    marker_icon = "home"
                elif status == "Delivered":
                    marker_color = "green"
                    marker_icon = "check"
                else:
                    marker_color = "blue"
                    marker_icon = "info-sign"

                arrival = loc.get('Scheduled_Arrival', 'N/A')
                service = loc.get('Service_Time_Mins', 0)
                
                # --- PREMIUM HTML TOOLTIP ---
                # Determine colors for the status badge
                status_color = "#10B981" if status == "Delivered" else "#3B82F6"
                status_bg = "#D1FAE5" if status == "Delivered" else "#DBEAFE"
                
                # Only show the time row if it's delivered
                time_row = f"""
                <div style="margin-bottom: 4px;">
                    <span style="color: #6B7280; font-size: 13px; font-weight: 600;">Time:</span> 
                    <span style="color: #111827; font-size: 13px; margin-left: 4px;">{delivery_time}</span>
                </div>
                """ if status == "Delivered" else ""

                tooltip_html = f"""
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-width: 200px; padding: 2px;">
                    <div style="font-size: 15px; font-weight: bold; color: #1F2937; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; margin-bottom: 8px;">
                        {loc.get('Location_Name', f'Stop {stop_id}')} <span style="font-size: 12px; color: #9CA3AF; font-weight: normal;">(ID: {stop_id})</span>
                    </div>
                    <div style="margin-bottom: 6px; display: flex; align-items: center;">
                        <span style="color: #6B7280; font-size: 13px; font-weight: 600;">Status:</span>
                        <span style="background-color: {status_bg}; color: {status_color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                            {status}
                        </span>
                    </div>
                    {time_row}
                    <div style="margin-bottom: 4px;">
                        <span style="color: #6B7280; font-size: 13px; font-weight: 600;">Arrival:</span> 
                        <span style="color: #111827; font-size: 13px; margin-left: 4px;">{arrival}</span>
                    </div>
                    <div>
                        <span style="color: #6B7280; font-size: 13px; font-weight: 600;">Unloading:</span> 
                        <span style="color: #111827; font-size: 13px; margin-left: 4px;">{service} mins</span>
                    </div>
                </div>
                """
                
                pod_str = "○ Pending"
                if status == "Delivered":
                    if photo_data:
                        pod_str = "✓ Photo Captured"
                    elif override_note:
                        pod_str = f"✓ Manual: {override_note}"
                        
                active_ledger_data.append({
                    "Truck ID": current_truck_name,
                    "Stop Name / Location": loc.get('Location_Name', f"Stop {stop_id}"),
                    "Status": status,
                    "Unloading Time (Mins)": service,
                    "Scheduled Arrival": arrival,
                    "Delivery Time": delivery_time,
                    "Proof of Delivery": pod_str,
                    "Photo_Data": photo_data
                })
                
                # --- CUSTOM PREMIUM MARKERS ---
                if status == "Delivered":
                    # Large Green Marker for Completed
                    delivered_html = """
                    <div style="
                        background-color: #10B981; 
                        color: white; 
                        border-radius: 50%; 
                        width: 34px; 
                        height: 34px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        border: 3px solid white; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
                        font-size: 18px;
                        font-weight: bold;
                    ">
                        ✓
                    </div>
                    """
                    custom_icon = folium.DivIcon(html=delivered_html, icon_anchor=(17, 17))
                else:
                    # Sleek Blue Hourglass Marker for Pending
                    # Slightly smaller (30px) to give visual priority to completed deliveries
                    pending_html = """
                    <div style="
                        background-color: #3B82F6; 
                        color: white; 
                        border-radius: 50%; 
                        width: 30px; 
                        height: 30px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        border: 3px solid white; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                        font-size: 14px;
                    ">
                        ⏳
                    </div>
                    """
                    custom_icon = folium.DivIcon(html=pending_html, icon_anchor=(15, 15))
                    
                # Add the styled marker to the map
                folium.Marker(
                    location=[loc['Latitude'], loc['Longitude']],
                    tooltip=tooltip_html,
                    icon=custom_icon
                ).add_to(marker_cluster)
                
        st_folium(m, use_container_width=True, height=600, returned_objects=[])
        
        st.divider()
        header_col1, spacer, header_col2 = st.columns([5, 2.5, 2.5], vertical_alignment="center")
        with header_col1:
            st.subheader(":material/list_alt: Active Route Ledger")
            
        with header_col2:
            if st.button(":material/save: Save to Ledger", use_container_width=True):
                date_key = datetime.now().strftime("%Y-%m-%d")
                ledger_data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_stops": total,
                    "total_distance_km": round(total_fleet_distance, 2),
                    "fuel_consumed_L": round(fuel_used_litres, 2),
                    "estimated_savings_PKR": round(savings_pkr, 2)
                }
                try:
                    db.reference(f'/ledger/{date_key}').set(ledger_data)
                    st.session_state.show_toast = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save ledger: {e}")
                    
        df_ledger = pd.DataFrame(active_ledger_data)
        df_ledger = df_ledger.sort_values(by=['Truck ID', 'Scheduled Arrival'], ascending=[True, True]).reset_index(drop=True)
        
        st.markdown("Select a row below to view the Proof of Delivery photo.")
        
        # Interactive Dataframe
        event = st.dataframe(
            df_ledger.drop(columns=['Photo_Data']), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Render the photo if a row is clicked
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            selected_photo = df_ledger.iloc[selected_idx]['Photo_Data']
            selected_stop = df_ledger.iloc[selected_idx]['Stop Name / Location']
            
            if selected_photo:
                st.success(f"Proof of Delivery for {selected_stop}")
                st.image(selected_photo, width=400)
            elif df_ledger.iloc[selected_idx]['Status'] == "Delivered":
                st.info(f"No photo available for {selected_stop}. Check for manual override notes.")

    else:
        st.info("Data loaded. Adjust settings and click 'Optimize Routes' to begin.")
        st.dataframe(df)

else:
    st.info("👋 Welcome! Please upload a CSV file in the sidebar to begin.")

st.write("")
st.write("")
st.divider() # Native full-width line

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <div style="text-align: center; padding-bottom: 20px;">
        <div style="font-size: 1.5rem; margin-bottom: 15px;">
            <a href="https://github.com/Irfan-code-cloud" target="_blank" style="color: #333333; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fab fa-github"></i>
            </a>
            <a href="https://www.linkedin.com/in/irfan-khattak-00b847251" target="_blank" style="color: #0077B5; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fab fa-linkedin"></i>
            </a>
            <a href="mailto:ifnkhattak@outlook.com" style="color: #D14836; margin: 0 15px; text-decoration: none; transition: opacity 0.3s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
                <i class="fas fa-envelope"></i>
            </a>
        </div>
        <p style="font-size: 14px; color: #6B7280; margin-top: 12px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            Engineered by <b>Irfan Khattak</b> &nbsp;|&nbsp; &copy; 2026 All Rights Reserved
        </p>
    </div>
""", unsafe_allow_html=True)
