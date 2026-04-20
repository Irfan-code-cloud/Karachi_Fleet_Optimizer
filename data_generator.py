import pandas as pd
import numpy as np

# 1. Define the parameters for your generated dataset
NUM_STOPS = 100 # Change this to 500 or 1000 when you want to test scale!

# Karachi Geographical Bounding Box (Roughly covering the main city)
MIN_LAT, MAX_LAT = 24.7800, 24.9800
MIN_LNG, MAX_LNG = 66.9700, 67.1800

# 2. Generate Realistic Logistics Data
data = {
    "Stop_ID": np.arange(1, NUM_STOPS + 1),
    "Location_Name": [f"Karachi Dropoff #{i}" for i in range(1, NUM_STOPS + 1)],
    
    # Generate random coordinates within Karachi
    "Latitude": np.random.uniform(MIN_LAT, MAX_LAT, NUM_STOPS),
    "Longitude": np.random.uniform(MIN_LNG, MAX_LNG, NUM_STOPS),
    
    # Realistic package weights between 10 KG and 250 KG
    "Demand_KG": np.random.randint(10, 250, NUM_STOPS),
    
    # Random service times (how long it takes to unload) between 10 to 45 mins
    "Service_Time_Mins": np.random.choice([10, 15, 20, 30, 45], NUM_STOPS),
    
    # Standard business hours for constraints (e.g., 9:00 to 17:00)
    "Open_Time": ["9:00"] * NUM_STOPS,
    "Close_Time": ["17:00"] * NUM_STOPS
}

df = pd.DataFrame(data)

# 3. Add the Depot (The starting point - let's put it near the Airport)
depot_data = {
    "Stop_ID": 0,
    "Location_Name": "Main Hub (Jinnah Airport Area)",
    "Latitude": 24.9000, 
    "Longitude": 67.1600,
    "Demand_KG": 0,
    "Service_Time_Mins": 0,
    "Open_Time": "8:00",
    "Close_Time": "20:00"
}

# Combine depot and stops
df = pd.concat([pd.DataFrame([depot_data]), df], ignore_index=True)

# 4. Export to CSV perfectly formatted for your Streamlit App
df.to_csv("massive_karachi_fleet_data.csv", index=False)
print(f"Success! Generated massive_karachi_fleet_data.csv with {NUM_STOPS} stops.")