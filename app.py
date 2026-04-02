from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from simulation import TrafficSimulation, TrafficNetwork
import json

app = Flask(__name__)
CORS(app)

# Initialize both simulation types
single_sim = TrafficSimulation()
network_sim = TrafficNetwork()
current_mode = 'single'  # 'single' or 'network'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_mode', methods=['POST'])
def set_mode():
    """Switch between single intersection and network mode"""
    global current_mode
    data = request.json
    current_mode = data.get('mode', 'single')
    return jsonify({'mode': current_mode, 'status': 'success'})

@app.route('/step', methods=['POST'])
def step():
    data = request.json
    densities = data.get('densities', {'N': 3, 'E': 3, 'S': 3, 'W': 3})
    emergency_intersection = data.get('emergency_intersection', None)
    emergency_lane = data.get('emergency_lane', None)
    use_adaptive = data.get('use_adaptive', True)
    
    if current_mode == 'network':
        state = network_sim.step(densities, emergency_intersection, emergency_lane, use_adaptive)
    else:
        # Single intersection mode
        state = single_sim.step(densities, emergency_lane, use_adaptive)
        # Wrap in network-like format for consistent frontend
        state = {
            'mode': 'single',
            'intersection': state,
            'timestamp': state.get('timestamp', 0),
            'total_vehicles': state['total_vehicles'],
            'total_vehicles_passed': state['total_vehicles_passed'],
            'average_congestion': state['congestion_level']
        }
    
    return jsonify(state)

@app.route('/reset', methods=['POST'])
def reset():
    if current_mode == 'network':
        state = network_sim.reset()
    else:
        state = single_sim.reset()
        state = {
            'mode': 'single',
            'intersection': state,
            'timestamp': 0,
            'total_vehicles': state['total_vehicles'],
            'total_vehicles_passed': state['total_vehicles_passed'],
            'average_congestion': state['congestion_level']
        }
    return jsonify(state)

@app.route('/get_state', methods=['GET'])
def get_state():
    if current_mode == 'network':
        state = network_sim.get_network_state()
    else:
        state = single_sim.get_state()
        state = {
            'mode': 'single',
            'intersection': state,
            'timestamp': 0,
            'total_vehicles': state['total_vehicles'],
            'total_vehicles_passed': state['total_vehicles_passed'],
            'average_congestion': state['congestion_level']
        }
    return jsonify(state)

@app.route('/run_test', methods=['POST'])
def run_test():
    data = request.json
    duration = data.get('duration', 300)
    densities = data.get('densities', {'N': 5, 'E': 5, 'S': 5, 'W': 5})
    
    # Run adaptive test
    if current_mode == 'network':
        network_sim.reset()
        for _ in range(duration):
            network_sim.step(densities, use_adaptive=True)
        adaptive_results = network_sim.get_network_state()
        
        network_sim.reset()
        for _ in range(duration):
            network_sim.step(densities, use_adaptive=False)
        fixed_results = network_sim.get_network_state()
        
        summary = {
            'adaptive': {
                'total_vehicles_passed': adaptive_results['total_vehicles_passed'],
                'average_congestion': adaptive_results['average_congestion']
            },
            'fixed': {
                'total_vehicles_passed': fixed_results['total_vehicles_passed'],
                'average_congestion': fixed_results['average_congestion']
            }
        }
    else:
        adaptive = single_sim.run_test(duration, densities, use_adaptive=True)
        fixed = single_sim.run_test(duration, densities, use_adaptive=False)
        summary = {'adaptive': adaptive, 'fixed': fixed}
    
    return jsonify(summary)

@app.route('/export_data', methods=['POST'])
def export_data():
    """Export current simulation data as CSV"""
    data = request.json
    mode = data.get('mode', 'single')
    
    if mode == 'network':
        state = network_sim.get_network_state()
        intersections = state['intersections']
        
        # Create CSV content
        csv_content = "Intersection ID,Name,Latitude,Longitude,Congestion %,Total Vehicles,Current Green,Time Left,N Vehicles,E Vehicles,S Vehicles,W Vehicles,Cycle Count\n"
        
        for int in intersections:
            csv_content += f"{int['id']},{int['name']},{int['lat']},{int['lng']},{int['congestion_level']:.1f},{int['total_vehicles']},{int['current_green']},{int['time_remaining']},{int['vehicles']['N']},{int['vehicles']['E']},{int['vehicles']['S']},{int['vehicles']['W']},{int['cycle_count']}\n"
        
        # Add summary
        csv_content += f"\n\n=== NETWORK SUMMARY ===\n"
        csv_content += f"Total Vehicles in Network,{state['total_vehicles']}\n"
        csv_content += f"Total Vehicles Passed,{state['total_vehicles_passed']}\n"
        csv_content += f"Average Congestion,{state['average_congestion']:.1f}%\n"
        csv_content += f"Simulation Time,{state['timestamp']} seconds\n"
        
    else:
        state = single_sim.get_state()
        csv_content = "Metric,Value\n"
        csv_content += f"Total Vehicles,{state['total_vehicles']}\n"
        csv_content += f"Vehicles Passed,{state['total_vehicles_passed']}\n"
        csv_content += f"Average Wait Time,{state['average_wait']:.2f} seconds\n"
        csv_content += f"Current Green Direction,{state['current_green']}\n"
        csv_content += f"Time Remaining,{state['time_remaining']} seconds\n"
        csv_content += f"Cycle Count,{state['cycle_count']}\n"
        csv_content += f"Congestion Level,{state['congestion_level']:.1f}%\n"
        csv_content += f"\n\n=== LANE STATUS ===\n"
        csv_content += f"North,{state['vehicles']['N']} vehicles\n"
        csv_content += f"East,{state['vehicles']['E']} vehicles\n"
        csv_content += f"South,{state['vehicles']['S']} vehicles\n"
        csv_content += f"West,{state['vehicles']['W']} vehicles\n"
    
    return jsonify({'csv': csv_content})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)