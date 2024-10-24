import os
import sys
import json
import platform
from flask import Flask, render_template, request, jsonify
from pathlib import Path
from threading import Thread
import time
import logging
import re
from dotenv import load_dotenv  # Added for environment variable management

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
SETTINGS_FILE = os.getenv('SETTINGS_FILE', 'settings.json')
DEFAULT_SAVES_PATH = os.getenv('MINECRAFT_BASE_PATH')

if not DEFAULT_SAVES_PATH:
    raise ValueError("MINECRAFT_BASE_PATH environment variable is not set.")

logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s:%(message)s')

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def is_wsl():
    """
    Detect if the script is running under WSL.
    """
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().lower()
        return 'microsoft' in version or 'wsl' in version
    except:
        return False

def get_minecraft_saves_path(world_name=None):
    """
    Returns the Path object for the specified Minecraft world.
    If `world_name` is provided, it appends the world name to the base path.
    """
    base_path = Path(DEFAULT_SAVES_PATH).resolve()
    if world_name:
        # Sanitize world name to prevent directory traversal
        sanitized_world_name = Path(world_name).name
        world_path = base_path / sanitized_world_name
        if not world_path.exists() or not world_path.is_dir():
            return None
        return world_path
    else:
        return base_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.get_json()
    world_name = data.get('world_name')
    
    if not world_name:
        logging.warning('Connect attempt without world name.')
        return jsonify({'success': False, 'message': 'World name is required.'}), 400

    world_path = get_minecraft_saves_path(world_name)

    if not world_path:
        logging.error(f'World "{world_name}" does not exist in saves directory.')
        return jsonify({'success': False, 'message': f'World "{world_name}" does not exist in saves directory.'}), 404

    computercraft_path = world_path / 'computercraft'
    computercraft_installed = computercraft_path.exists() and computercraft_path.is_dir()

    computer_folder_path = computercraft_path / 'computer'
    computers_found = computercraft_installed and computer_folder_path.exists() and computer_folder_path.is_dir()

    ids_json_path = computercraft_path / 'ids.json'
    if computercraft_installed:
        if ids_json_path.exists():
            try:
                with open(ids_json_path, 'r') as f:
                    ids_data = json.load(f)
                max_id = ids_data.get('computer', 0)
            except json.JSONDecodeError:
                logging.warning(f'ids.json at {ids_json_path} is corrupted.')
                max_id = 0
        else:
            # Initialize ids.json
            max_id = 0
            try:
                with open(ids_json_path, 'w') as f:
                    json.dump({"computer": max_id}, f, indent=4)
                logging.info(f'ids.json created at {ids_json_path}.')
            except Exception as e:
                logging.error(f'Error creating ids.json at {ids_json_path}: {e}')
                max_id = 0
    else:
        max_id = 0

    settings = load_settings()
    settings['world_name'] = world_name
    settings['saves_path'] = str(world_path)
    save_settings(settings)

    response = {
        'success': True,
        'computercraft_installed': computercraft_installed,
        'computers_found': computers_found,
        'max_computer_id': max_id
    }

    if computercraft_installed and computers_found:
        response['message'] = f'Connected to "{world_name}". ComputerCraft is installed and computers are found.'
    elif computercraft_installed and not computers_found:
        response['message'] = f'Connected to "{world_name}". ComputerCraft is installed but no computers found.'
    else:
        response['message'] = f'Connected to "{world_name}". ComputerCraft is not installed.'

    logging.info(response['message'])
    return jsonify(response), 200

@app.route('/api/create_computercraft', methods=['POST'])
def create_computercraft():
    data = request.get_json()
    world_name = data.get('world_name')

    if not world_name:
        logging.warning('Create ComputerCraft folders attempt without world name.')
        return jsonify({'success': False, 'message': 'World name is required.'}), 400

    world_path = get_minecraft_saves_path(world_name)

    if not world_path:
        logging.error(f'World "{world_name}" does not exist in saves directory.')
        return jsonify({'success': False, 'message': f'World "{world_name}" does not exist in saves directory.'}), 404

    computercraft_path = world_path / 'computercraft'
    computer_folder_path = computercraft_path / 'computer'
    ids_json_path = computercraft_path / 'ids.json'

    try:
        computercraft_path.mkdir(parents=True, exist_ok=True)
        computer_folder_path.mkdir(parents=True, exist_ok=True)
        
        if not ids_json_path.exists():
            with open(ids_json_path, 'w') as f:
                json.dump({"computer": 0}, f, indent=4)
            logging.info(f'ids.json created at {ids_json_path}.')
    except Exception as e:
        logging.error(f'Error creating folders at {computercraft_path}: {e}')
        return jsonify({'success': False, 'message': f'Error creating folders: {str(e)}'}), 500

    logging.info('ComputerCraft and computer folders created successfully.')
    return jsonify({'success': True, 'message': 'ComputerCraft and computer folders created successfully.'}), 200

@app.route('/api/get_computer_ids', methods=['GET'])
def get_computer_ids():
    settings = load_settings()
    world_name = settings.get('world_name')
    saves_path = Path(settings.get('saves_path', ''))

    if not world_name or not saves_path:
        logging.warning('Attempt to get Computer IDs without connected world.')
        return jsonify({'success': False, 'message': 'World not connected.'}), 400

    computercraft_path = saves_path / 'computercraft' / 'computer'

    if not computercraft_path.exists() or not computercraft_path.is_dir():
        logging.error('ComputerCraft computer directory not found.')
        return jsonify({'success': False, 'message': 'ComputerCraft computer directory not found.'}), 404

    computer_ids = []
    for entry in computercraft_path.iterdir():
        if entry.is_dir():
            # Computer folders are usually named as numbers or [number]
            name = entry.name.strip("[]")
            if name.isdigit():
                computer_ids.append(name)

    logging.info(f'Fetched Computer IDs: {computer_ids}')
    return jsonify({'success': True, 'computer_ids': computer_ids}), 200

@app.route('/api/run_program', methods=['POST'])
def run_program():
    data = request.get_json()
    computer_id = data.get('computer_id')
    code = data.get('code')
    filename = data.get('filename', 'startup.lua')  

    if not computer_id or not code:
        logging.warning('Run program attempt without Computer ID or code.')
        return jsonify({'success': False, 'message': 'Computer ID and code are required.'}), 400

    settings = load_settings()
    saves_path = Path(settings.get('saves_path', ''))
    world_name = settings.get('world_name', '')
    if not saves_path or not world_name:
        logging.warning('Run program attempt without connected world.')
        return jsonify({'success': False, 'message': 'World not connected.'}), 400

    computercraft_path = saves_path / 'computercraft' / 'computer'
    computer_folder = computercraft_path / computer_id

    if not computer_folder.exists() or not computer_folder.is_dir():
        logging.error(f'Computer ID "{computer_id}" not found.')
        return jsonify({'success': False, 'message': f'Computer ID "{computer_id}" not found.'}), 404

    # Sanitize filename
    sanitized_filename = Path(filename).name  # Removes any path components

    if not sanitized_filename.endswith('.lua'):
        sanitized_filename += '.lua'

    try:
        functions = extract_functions(code)
        if not functions:
            # If no functions found, save the entire code as a single file
            lua_file_path = computer_folder / sanitized_filename
            with open(lua_file_path, 'w') as f:
                f.write(code)
            logging.info(f'Lua program successfully written to Computer ID "{computer_id}" as "{sanitized_filename}".')
            return jsonify({'success': True, 'message': f'Lua program successfully written to Computer ID "{computer_id}" as "{sanitized_filename}".'}), 200
        
        # No separate 'functions' directory; save directly in computer_folder
        # Read and update ids.json
        ids_json_path = computercraft_path / 'ids.json'
        if ids_json_path.exists():
            with open(ids_json_path, 'r') as f:
                ids_data = json.load(f)
        else:
            ids_data = {"computer": 0}
        
        for func_name, func_code in functions:
            # Sanitize function name for filename
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', func_name)
            func_filename = f"{clean_name}.lua"
            func_file_path = computer_folder / func_filename
            
            with open(func_file_path, 'w') as f:
                f.write(func_code)
            
            # Optionally, update 'ids.json' or any other tracking as needed
            # Example: Increment computer ID or track functions
            # Here, we'll skip updating ids.json for simplicity

            logging.info(f'Function "{func_name}" saved as "{func_filename}" in Computer ID "{computer_id}".')

        return jsonify({'success': True, 'message': f'{len(functions)} functions successfully written to Computer ID "{computer_id}".'}), 200

    except Exception as e:
        logging.error(f'Error writing Lua files to {computer_folder}: {e}')
        return jsonify({'success': False, 'message': f'Error writing Lua files: {str(e)}'}), 500

def extract_functions(lua_code):
    """
    Extracts all function definitions from the given Lua code and appends a call to each function.

    Args:
        lua_code (str): The Lua code as a string.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing function names and their executable code.
    """
    function_pattern = re.compile(
        r'function\s+([\w\.]+)\s*\((.*?)\)\s*(.*?)\s*end',
        re.DOTALL
    )
    functions = []
    for match in function_pattern.finditer(lua_code):
        full_name = match.group(1).strip()
        args = match.group(2).strip()
        body = match.group(3).strip()
        # Extract the function name without module prefix if present
        func_name = full_name.split('.')[-1]
        # Create the function definition
        func_def = f'function {full_name}({args})\n{body}\nend\n'
        # Append a call to the function
        func_call = f'{func_name}()\n'
        # Combine function definition and call
        executable_func_code = func_def + func_call
        functions.append((func_name, executable_func_code))
    return functions

@app.route('/api/os_info', methods=['GET'])
def os_info():
    """
    Returns the operating system information.
    Useful for debugging.
    """
    return jsonify({
        'os_name': os.name,
        'platform': sys.platform,
        'system': platform.system(),
        'release': platform.release(),
        'is_wsl': is_wsl()
    }), 200

if __name__ == '__main__':
    PORT = 5000

    def run_app():
        app.run(host='0.0.0.0', port=PORT, debug=False)

    thread = Thread(target=run_app)
    thread.start()

    time.sleep(1)
    # Removed webbrowser.open since it's not needed on a server
