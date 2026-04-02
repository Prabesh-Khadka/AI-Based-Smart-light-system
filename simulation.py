import random
import math

class TrafficIntersection:
    """Single traffic intersection (for detailed view)"""
    def __init__(self, id, name, lat, lng, lanes_config=None):
        self.id = id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.lanes = ['N', 'E', 'S', 'W']
        self.vehicles = {lane: 0 for lane in self.lanes}
        self.current_green = 'N'
        self.time_remaining = 10
        self.emergency_active = False
        self.emergency_lane = None
        self.cycle_count = 0
        self.total_vehicles_passed = 0
        self.congestion_level = 0
        
        # Metrics for analysis
        self.wait_time_history = []
        self.passed_history = []
        
        # Custom lane configurations
        if lanes_config:
            for lane, config in lanes_config.items():
                if lane in self.vehicles:
                    self.vehicles[lane] = config.get('initial', 0)
    
    def update_congestion(self):
        """Calculate congestion level based on vehicle counts"""
        total_vehicles = sum(self.vehicles.values())
        max_capacity = 60
        self.congestion_level = min(100, (total_vehicles / max_capacity) * 100)
        return self.congestion_level
    
    def calculate_green_time(self, lane):
        """Adaptive green time based on vehicle count"""
        v = self.vehicles[lane]
        if v > 30:
            return 40
        elif v > 20:
            return 30
        elif v > 10:
            return 20
        elif v > 5:
            return 12
        else:
            return 8
    
    def calculate_fixed_green_time(self, lane):
        """Fixed timing for baseline"""
        return 15
    
    def step(self, densities, emergency_lane=None, use_adaptive=True):
        """Advance intersection by one second"""
        # Store wait time before update
        current_wait = sum(self.vehicles.values())
        self.wait_time_history.append(current_wait)
        
        # Emergency override
        if emergency_lane and emergency_lane in self.lanes:
            self.emergency_active = True
            self.emergency_lane = emergency_lane
            self.current_green = emergency_lane
            self.time_remaining = 12
        
        # Normal operation
        if not self.emergency_active:
            if self.time_remaining <= 0:
                idx = self.lanes.index(self.current_green)
                self.current_green = self.lanes[(idx + 1) % 4]
                if use_adaptive:
                    self.time_remaining = self.calculate_green_time(self.current_green)
                else:
                    self.time_remaining = self.calculate_fixed_green_time(self.current_green)
                self.cycle_count += 1
            else:
                self.time_remaining -= 1
        elif self.emergency_active and self.time_remaining <= 0:
            self.emergency_active = False
            self.emergency_lane = None
        
        # Process vehicles during green
        if self.current_green == self.emergency_lane or not self.emergency_active:
            departed = min(self.vehicles[self.current_green], 2)
            self.vehicles[self.current_green] -= departed
            self.total_vehicles_passed += departed
            self.passed_history.append(self.total_vehicles_passed)
        
        # Add new vehicles
        for lane in self.lanes:
            density = densities.get(lane, 3)
            new_vehicles = random.randint(0, int(density * 1.5))
            self.vehicles[lane] += new_vehicles
            if self.vehicles[lane] > 60:
                self.vehicles[lane] = 60
        
        # Update congestion
        self.update_congestion()
        
        return self.get_state()
    
    def get_state(self):
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.lat,
            'lng': self.lng,
            'vehicles': self.vehicles,
            'current_green': self.current_green,
            'time_remaining': self.time_remaining,
            'emergency_active': self.emergency_active,
            'cycle_count': self.cycle_count,
            'total_vehicles_passed': self.total_vehicles_passed,
            'congestion_level': self.congestion_level,
            'total_vehicles': sum(self.vehicles.values()),
            'average_wait': sum(self.wait_time_history[-100:]) / min(100, len(self.wait_time_history)) if self.wait_time_history else 0
        }
    
    def reset(self):
        """Reset intersection to initial state"""
        self.__init__(self.id, self.name, self.lat, self.lng)

class TrafficNetwork:
    """Manages multiple intersections in a city network"""
    def __init__(self):
        # Define intersections with real coordinates
        self.intersections = [
            TrafficIntersection(1, "Central Station", 40.7128, -74.0060),
            TrafficIntersection(2, "Times Square", 40.7580, -73.9855),
            TrafficIntersection(3, "Union Square", 40.7359, -73.9911),
            TrafficIntersection(4, "Herald Square", 40.7498, -73.9878),
            TrafficIntersection(5, "Columbus Circle", 40.7681, -73.9818),
        ]
        
        self.global_metrics = {
            'total_wait_time': 0,
            'total_vehicles_passed': 0,
            'timestamp': 0
        }
        
    def step(self, global_densities=None, emergency_intersection=None, emergency_lane=None, use_adaptive=True):
        """Step all intersections simultaneously"""
        self.global_metrics['timestamp'] += 1
        
        if global_densities is None:
            global_densities = {'N': 3, 'E': 3, 'S': 3, 'W': 3}
        
        total_vehicles_passed = 0
        
        for intersection in self.intersections:
            # Check if this intersection has emergency
            emergency = None
            if emergency_intersection == intersection.id:
                emergency = emergency_lane
            
            # Step the intersection
            state = intersection.step(global_densities, emergency, use_adaptive)
            total_vehicles_passed += state['total_vehicles_passed']
        
        self.global_metrics['total_vehicles_passed'] = total_vehicles_passed
        
        return self.get_network_state()
    
    def get_network_state(self):
        return {
            'timestamp': self.global_metrics['timestamp'],
            'intersections': [int.get_state() for int in self.intersections],
            'total_vehicles_passed': self.global_metrics['total_vehicles_passed'],
            'total_vehicles': sum(int.get_state()['total_vehicles'] for int in self.intersections),
            'average_congestion': sum(int.get_state()['congestion_level'] for int in self.intersections) / len(self.intersections)
        }
    
    def reset(self):
        """Reset entire network"""
        self.__init__()
        return self.get_network_state()
    
    def get_single_intersection(self, id=1):
        """Get a single intersection for detailed view"""
        for int in self.intersections:
            if int.id == id:
                return int
        return self.intersections[0]

# For backward compatibility - single intersection simulation
class TrafficSimulation:
    """Wrapper for single intersection (maintains previous functionality)"""
    def __init__(self):
        self.intersection = TrafficIntersection(1, "Main Intersection", 40.7128, -74.0060)
        
    def step(self, densities, emergency_lane=None, use_adaptive=True):
        return self.intersection.step(densities, emergency_lane, use_adaptive)
    
    def get_state(self):
        return self.intersection.get_state()
    
    def reset(self):
        self.intersection.reset()
        return self.get_state()
    
    def run_test(self, duration=300, densities=None, use_adaptive=True):
        if densities is None:
            densities = {'N': 5, 'E': 5, 'S': 5, 'W': 5}
        
        self.reset()
        for _ in range(duration):
            self.step(densities, use_adaptive=use_adaptive)
        
        state = self.get_state()
        return {
            'total_wait_time': sum(self.intersection.wait_time_history),
            'average_wait_time': state['average_wait'],
            'total_vehicles_passed': state['total_vehicles_passed'],
            'vehicles_per_second': state['total_vehicles_passed'] / duration,
            'cycle_count': state['cycle_count']
        }