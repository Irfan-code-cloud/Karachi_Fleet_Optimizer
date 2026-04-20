---
trigger: always_on
---

# Rule: Fleet Optimization Standards

# 1. Core Logic & Algorithms
**Routing Engine:** ALWAYS use `ortools.constraint_solver` for routing problems.
**Distance Calculation:** Use Haversine formula for calculating distances between lat/lon coordinates. Do NOT use Euclidean distance (Pythagoras) as it is inaccurate for geospatial data across a city grid.
**Optimization Goal:** The primary objective function must always be to minimize total distance.

# 2. Data Handling
**Input Format:** Expect CSV files with columns "Latitude" and "Longitude".
**Validation:** Always write a check to ensure coordinates are valid.

# 3. Visualization
**Mapping:** Use `folium` for all map visualizations.
**Color Coding:** Assign a unique color to each vehicle's route for clarity.
**Interactivity:** Maps must include tooltips showing the location name or stop ID on hover.