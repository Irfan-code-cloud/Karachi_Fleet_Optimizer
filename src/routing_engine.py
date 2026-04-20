import math
import requests
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def validate_coordinates(lat, lon):
    """Ensure coordinates are within valid geographical boundaries."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude: {lon}")

def create_distance_matrix(locations):
    """Creates a complete matrix of distance between each location in meters (Fallback)."""
    num_locations = len(locations)
    matrix = [[0] * num_locations for _ in range(num_locations)]
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                matrix[i][j] = int(haversine(
                    locations[i]['Latitude'], locations[i]['Longitude'],
                    locations[j]['Latitude'], locations[j]['Longitude']
                ))
    return matrix

def time_to_mins(time_str, is_close=False):
    """
    Converts a time string like '08:30' into integer minutes from midnight.
    Defaults to 0 for open times and 1440 (24h) for close times if missing.
    """
    if not time_str or not isinstance(time_str, str):
        return 1440 if is_close else 0
    try:
        hours, mins = map(int, time_str.split(':'))
        return hours * 60 + mins
    except (ValueError, AttributeError):
        return 1440 if is_close else 0

def mins_to_str(total_mins):
    """
    Converts integer minutes from midnight into 12-hour AM/PM string.
    """
    total_mins = max(0, int(total_mins)) # Ensure it's non-negative
    hours24 = (total_mins // 60) % 24
    mins = total_mins % 60
    
    am_pm = "AM" if hours24 < 12 else "PM"
    hours12 = hours24 % 12
    if hours12 == 0:
        hours12 = 12
        
    return f"{hours12:02d}:{mins:02d} {am_pm}"

def get_osrm_matrix(dataframe):
    """
    Fetches real-world driving distances and durations from OSRM. 
    Falls back to Haversine if the public API fails.
    """
    locations = dataframe.to_dict('records')
    
    try:
        # Build coordinate string: lon1,lat1;lon2,lat2
        coords_list = [f"{loc['Longitude']},{loc['Latitude']}" for loc in locations]
        coords_string = ";".join(coords_list)
        
        # Call OSRM returning BOTH distances and durations
        url = f"http://router.project-osrm.org/table/v1/driving/{coords_string}?annotations=distance,duration"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        dist_matrix_raw = data['distances']
        dur_matrix_raw = data['durations']
        
        # OSRM returns distances in meters, durations in seconds
        # Convert distances to int, durations (seconds) to integer minutes
        dist_matrix = [[int(round(val)) for val in row] for row in dist_matrix_raw]
        dur_matrix = [[int(round(val / 60.0)) for val in row] for row in dur_matrix_raw]
        
        return dist_matrix, dur_matrix
        
    except Exception as e:
        print(f"OSRM API Failed: {e}. Falling back to Haversine distance matrix.")
        # Fallback mapping: approximate duration using 60 km/h (1 min per km)
        dist_matrix = create_distance_matrix(locations)
        dur_matrix = [[int(math.ceil(val / 1000.0)) for val in row] for row in dist_matrix]
        return dist_matrix, dur_matrix

def solve_cvrp(dataframe, num_vehicles, vehicle_capacity=1500):
    """
    Solves the Capacitated Vehicle Routing Problem with Time Windows (VRPTW).
    """
    locations = dataframe.to_dict('records')
    demands = [int(loc.get('Demand_KG', 0)) for loc in locations]
    
    # Validation step
    for loc in locations:
        validate_coordinates(loc['Latitude'], loc['Longitude'])
        
    # Get Distance & Duration Matrices
    distance_matrix, duration_matrix = get_osrm_matrix(dataframe)
    
    # Store depot explicitly (index 0)
    depot = 0
    
    # Setup OR-Tools
    manager = pywrapcp.RoutingIndexManager(len(locations), num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)
    
    # 1. Distance Callback (Minimization objective)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
        
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # 2. Add Capacity constraint
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]
        
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [int(vehicle_capacity)] * num_vehicles,  # vehicle maximum capacities limits
        True,  # start cumul to zero
        'Capacity'
    )
    
    # 3. Create the Time Callback
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        travel_time = duration_matrix[from_node][to_node]
        service_time = int(locations[from_node].get('Service_Time_Mins', 0))
        
        return travel_time + service_time
        
    transit_time_callback_index = routing.RegisterTransitCallback(time_callback)
    
    # 4. Add the Time Dimension
    routing.AddDimension(
        transit_time_callback_index,
        1440,  # allow waiting time (slack) max 1 day in minutes
        1440,  # maximum time per vehicle max 1 day in minutes
        False, # Don't force start cumul to zero, time window of depot dictates start
        'Time'
    )
    time_dimension = routing.GetDimensionOrDie('Time')
    
    # 5. Enforce Time Windows
    for i, loc in enumerate(locations):
        index = manager.NodeToIndex(i)
        if index == -1: # Unused node (shouldn't happen here, but safe)
            continue
            
        open_time = time_to_mins(loc.get('Open_Time'), is_close=False)
        close_time = time_to_mins(loc.get('Close_Time'), is_close=True)
        
        time_dimension.CumulVar(index).SetRange(open_time, close_time)

    # Note: ensure that depot start and end time windows are respected across all vehicles
    for i in range(num_vehicles):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    # Set search parameters and heuristics
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(2)
    
    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        return None
        
    # Extract routes from the solution
    routes = []
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            # Make a copy of the dict to not overwrite original structures
            stop_data = locations[node_index].copy()
            
            # Fetch Scheduled_Arrival from VRPTW cumulative variables
            time_var = time_dimension.CumulVar(index)
            arrival_mins = solution.Value(time_var)
            stop_data['Scheduled_Arrival'] = mins_to_str(arrival_mins)
            
            # Pass through the service time explicit integer
            stop_data['Service_Time_Mins'] = int(stop_data.get('Service_Time_Mins', 0))
            
            route.append(stop_data)
            index = solution.Value(routing.NextVar(index))
        
        # Append the depot as the final point
        node_index = manager.IndexToNode(index)
        stop_data = locations[node_index].copy()
        
        time_var = time_dimension.CumulVar(index)
        arrival_mins = solution.Value(time_var)
        stop_data['Scheduled_Arrival'] = mins_to_str(arrival_mins)
        stop_data['Service_Time_Mins'] = 0 # No service time at final wrapup depot
        
        route.append(stop_data) 
        
        if len(route) > 2: # vehicle actually did some work, skip empty routes
            routes.append(route)
            
    return routes
