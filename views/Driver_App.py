import streamlit as st
import pytz
import firebase_admin
from firebase_admin import credentials, db
import base64
import folium
from streamlit_folium import st_folium
from datetime import datetime
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
st.set_page_config(page_title="Driver Portal", page_icon=":material/near_me:", layout="centered")

st.markdown("""
    <style>
    /* 1. THE ULTIMATE NAVIGATION KILLER */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="headerNoPadding"],
    button[aria-label="Open sidebar"],
    .st-emotion-cache-1infhvl {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }

    /* 2. COMPLETELY REMOVE SIDEBAR HITBOX */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    /* 3. DESKTOP VIEW (THE BIG SCREEN FIX) */
    /* Restrict the app to a clean, centered column on large monitors */
    .block-container {
        padding-top: 0 !important;
        max-width: 800px !important; /* Prevents ultra-wide stretching */
        margin: 0 auto !important;   /* Centers the column perfectly */
    }

    /* 4. MOBILE VIEW (SMARTPHONE OVERRIDES) */
    @media screen and (max-width: 768px) {
        /* Allow mobile to use the full screen width */
        .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* Force 'Today's Route' to fit perfectly on one line for narrow phones */
        [data-testid="stMarkdownContainer"] h1 {
            font-size: 1.35rem !important;
            white-space: nowrap !important;
            line-height: 1.1 !important;
        }
        /* Shrink 'Stop X' headings for small screens */
        [data-testid="stMarkdownContainer"] h3 {
            font-size: 1.1rem !important;
            line-height: 1.2 !important;
            margin-bottom: 0.1rem !important;
        }
        /* Tighten vertical gaps to save scroll space */
        [data-testid="stVerticalBlock"] > div {
            padding-top: 0px !important;
            padding-bottom: 2px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

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

st.title(":material/list_alt: Today's Route")

# --- FETCH REAL-TIME DATA ---
try:
    cloud_data = db.reference('/').get()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

# Check if the manager has actually pushed routes yet
if not cloud_data or 'routes' not in cloud_data:
    st.warning("No routes assigned yet. Please wait for the dispatcher to optimize the fleet.")
    st.stop()

# Extract the data from the cloud
routes = cloud_data.get('routes', [])
delivery_status = cloud_data.get('deliveries', {})

if len(routes) > 0:
    # Create a list like ["Truck 1", "Truck 2"] based on how many routes exist
    truck_ids = [f"Truck {i+1}" for i in range(len(routes))]
    
    with st.expander(":material/help: How to Use This App"):
        st.markdown("""
       **Driver Quick Guide:**
        * **:material/near_me: Navigate:** Tap to open Google Maps and get turn-by-turn directions to your next stop.
        * **:material/upload_file: Upload Photo:** Tap to open your phone's camera or gallery and upload a picture as Proof of Delivery (POD).
        * **:material/check_circle: Delivered:** The stop is automatically finalized once the photo is uploaded.
        * **:material/draw: Manual Override:** If you cannot take a photo, type a short note (e.g., "Handed directly to security") and confirm to clear the stop.
        * **:material/lock_open: Undo:** Made a mistake? Toggle 'Unlock Record' and tap 'Confirm Undo' to reset the stop back to 'Pending'.
        """)

    st.markdown("### :material/local_shipping: Vehicle Assignment")
    
    # Check if the user is a restricted driver
    if st.session_state.get("role") == "driver":
        # Force the assigned truck, no dropdown allowed
        selected_truck = st.session_state.get("assigned_truck", "Truck 1")
        st.info(f"**Locked Session:** You are securely assigned to **{selected_truck}**.", icon="🔒")
    else:
        # Managers and Admins can still select any truck to monitor them
        selected_truck = st.selectbox("Select Vehicle to Monitor", ["Truck 1", "Truck 2", "Truck 3", "Truck 4", "Truck 5", "Truck 6"])
    
    # Convert "Truck 2" into the math index 1, "Truck 3" into index 2, etc.
    truck_index = int(selected_truck.split(" ")[1]) - 1
    
    # Assign the correct route based on the dropdown choice
    truck_route = routes[truck_index]
    
    st.info(f":material/local_shipping: Driver: {selected_truck} | Vehicle Capacity: 500 KG")

    # --- AI DISPATCH BRIEFING ---
    if ai_model:
        if st.button(f"Generate Route Briefing for {selected_truck}"):
            with st.spinner("AI is analyzing your route..."):
                # Get a few stop names to make it personalized
                stops_list = ", ".join([loc.get('Location_Name', 'Stop') for loc in truck_route[1:-1]])
                prompt = f"""
                You are a logistics dispatcher in Karachi. Write a short, simple, and polite 2-sentence briefing for a driver assigned to {selected_truck}.
                They have {len(truck_route)-2} stops today.
                Remind them to drive safely in Karachi traffic.
                CRITICAL INSTRUCTION: Do not use time-specific greetings like "Good morning" or "Good afternoon". Start the message directly with the assignment details.
                """
                try:
                    response = ai_model.generate_content(prompt)
                    st.success(":material/smart_toy: **AI Dispatcher:**")
                    st.write(response.text)
                except Exception as e:
                    st.error("AI couldn't connect right now.")

    # --- MOBILE ROUTE MAP ---
    if len(truck_route) > 0:
        # Extract purely standard coordinates directly corresponding to the truck array natively avoiding the OSRM bounds
        route_coords = [(loc['Latitude'], loc['Longitude']) for loc in truck_route]
        
        # Determine center point
        center_lat = sum([lat for lat, lon in route_coords]) / len(route_coords)
        center_lng = sum([lon for lat, lon in route_coords]) / len(route_coords)
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=12)
        
        # PolyLine natively rendering path
        folium.PolyLine(locations=route_coords, color="blue", weight=4, opacity=0.8).add_to(m)
        
        # Markers for stops
        for loc in truck_route[1:-1]:
            folium.Marker(
                location=[loc['Latitude'], loc['Longitude']],
                tooltip=f"{loc.get('Location_Name', 'Stop')}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)
            
        # Draw Depot
        if len(truck_route) > 0:
            folium.Marker(
                location=[truck_route[0]['Latitude'], truck_route[0]['Longitude']],
                tooltip="Depot",
                icon=folium.Icon(color="black", icon="home")
            ).add_to(m)
            
        st_folium(m, width=350, height=300, returned_objects=[])

    st.divider()

    # Callback function to update status DIRECTLY IN THE CLOUD
    def mark_delivered(s_id, data_uri):
        karachi_tz = pytz.timezone('Asia/Karachi')
        timestamp = datetime.now(karachi_tz).strftime("%Y-%m-%d %I:%M %p")
        db.reference(f'/deliveries/{s_id}').set({
            "status": "Delivered",
            "photo_data": data_uri,
            "timestamp": timestamp,
            "override_note": ""
        })

    # Skip depot at start [0] and end [-1]
    for i, stop in enumerate(truck_route[1:-1]):
        stop_id = str(stop['Stop_ID']) 
        
        # --- NEW SMART STATUS LOOKUP ---
        # This handles the "list vs dict" error automatically
        if isinstance(delivery_status, list):
            idx = int(stop_id)
            # Look up by index if it's a list
            status_val = delivery_status[idx] if idx < len(delivery_status) else "Pending"
        elif isinstance(delivery_status, dict):
            # Look up by key if it's a dictionary
            status_val = delivery_status.get(stop_id, "Pending")
        else:
            status_val = "Pending"
            
        # Extra safety check for None values
        if status_val is None:
            status_val = "Pending"
            
        # Safely extract status if it's a dict
        if isinstance(status_val, dict):
            status = status_val.get("status", "Pending")
        else:
            status = status_val
        # -------------------------------

        with st.container():
            st.markdown(f"### Stop {i+1}: {stop['Location_Name']}")
            st.write(f"**Drop-off:** {stop['Demand_KG']} KG")
            
            c1, c2 = st.columns(2)

            # --- AI TRAFFIC & SAFETY BRIEFING FOR THIS STOP ---
            if ai_model:
                if st.button(f"AI Traffic Intel for {stop.get('Location_Name', 'this stop')}", key=f"intel_{stop_id}"):
                    with st.spinner("Analyzing Karachi traffic patterns..."):
                        current_time = datetime.now().strftime("%I:%M %p")
                        prompt = f"""
                        You are a local Karachi logistics expert. The current time is {current_time}. 
                        Our delivery driver is heading to: {stop.get('Location_Name', 'an unknown location')}.
                        
                        Write exactly two bullet points:
                        1. **Traffic Context:** A 1-sentence warning about typical traffic conditions or bottlenecks in this specific area of Karachi at this time of day.
                        2. **Driver Safety:** A 1-sentence hyper-specific safety tip for driving a delivery truck in this area.
                        """
                        try:
                            response = ai_model.generate_content(prompt)
                            with st.container(border=True):
                                st.markdown(response.text)
                        except Exception as e:
                            st.error("AI Dispatcher is currently offline.")
            
            # 1. Navigation
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={stop['Latitude']},{stop['Longitude']}"
            c1.link_button(":material/near_me: Navigate", maps_url, use_container_width=True)
                
            # 2. Status / Action
            if status == "Delivered":
                c2.success(":material/check_circle: Delivered")
                
                # Two-Step Undo Protection
                unlock_undo = c2.toggle("Unlock Record", key=f"unlock_{stop_id}")
                if unlock_undo:
                    if c2.button(":material/delete_forever: Confirm Undo", type="primary", key=f"undo_{stop_id}"):
                        db.reference(f'/deliveries/{stop_id}').set("Pending")
                        st.rerun()
            else:
                tab1, tab2 = st.tabs([":material/upload_file: Upload POD", ":material/draw: Manual"])
                
                with tab1:
                    # Using uploader allows native camera OR gallery selection on mobile
                    pic = st.file_uploader(f"Proof for Stop {stop_id}", type=["png", "jpg", "jpeg"], key=f"pod_{stop_id}")
                    
                    if pic is not None:
                        # Backend Validation (The Double-Check)
                        file_ext = pic.name.split('.')[-1].lower()
                        allowed_extensions = ['png', 'jpg', 'jpeg']
                        
                        if file_ext not in allowed_extensions:
                            st.error("🚨 Security Alert: Invalid file type. Only JPG and PNG images are permitted.", icon="🛑")
                            st.stop() # Immediately halt execution

                        # Read the image buffer, convert to Base64
                        encoded_string = base64.b64encode(pic.read()).decode('utf-8')
                        data_uri = f"data:image/jpeg;base64,{encoded_string}"
                        
                        # Update Firebase
                        mark_delivered(stop_id, data_uri)
                        st.rerun() 
                        
                with tab2:
                    override_note = st.text_input(
                        "Receiver Name / Reason:", 
                        placeholder="e.g., Camera broken, handed to security guard Ali",
                        key=f"note_{stop_id}"
                    )
                    if st.button("Confirm Manual Delivery", key=f"manual_btn_{stop_id}"):
                        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                        db.reference(f'/deliveries/{stop_id}').set({
                            "status": "Delivered", 
                            "photo_data": "",
                            "timestamp": timestamp,
                            "override_note": override_note
                        })
                        st.rerun()
            
            # This should be inside the container mapping layout specifically
            st.write("") # Add some vertical buffer before the footer

# --- REMOVE DEAD SPACE AT BOTTOM ---
st.markdown("""
    <style>
    /* Nuke the default Streamlit bottom padding */
    .block-container {
        padding-bottom: 0rem !important;
    }
    /* Completely remove the native Streamlit footer */
    footer {
        display: none !important;
    }
    /* Optional: tighten up the padding below the custom footer */
    div[data-testid="stVerticalBlock"] > div:last-child {
        padding-bottom: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.divider()
# Use the official authenticator to properly clear the auth cookies
if "authenticator" in st.session_state:
    st.session_state["authenticator"].logout("Log Out", "main", key="driver_main_logout_btn")

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
