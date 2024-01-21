from flask import Flask, request, jsonify
import os
import traceback
import shutil
import subprocess
import sys

app = Flask(__name__)

def get_directory_contents(directory_path):
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        contents = os.listdir(directory_path)
        return {
            'files': [x for x in contents if os.path.isfile(os.path.join(directory_path, x))],
            'directories': [x for x in contents if os.path.isdir(os.path.join(directory_path, x))]
        }
    else:
        return None

@app.route('/list_directory', methods=['GET'])
def list_directory():
    try:
        directory_path = "./" + request.args.get('directory_path', '.')
        contents = get_directory_contents(directory_path)
        
        if contents is not None:
            return jsonify(contents), 200
        else:
            return jsonify({'error': 'Directory not found'}), 404
    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500

@app.route('/create_file', methods=['POST'])
def create_file():
    try:
        data = request.json
        file_name = "./" + data['file_name']
        content = data.get('content', '')
        
        current_directory = os.path.dirname(file_name) or '.'
        os.makedirs(current_directory, exist_ok=True)
        with open(file_name, 'w') as file:
            file.write(content)

        directory_contents = get_directory_contents(current_directory)
    
        return jsonify({'message': 'File created successfully', 'directory_contents': directory_contents, 'current_directory': current_directory}), 200
    
    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500

@app.route('/create_directory', methods=['POST'])
def create_directory():
    try:
        data = request.json
        directory_path = "./" + data['directory_path']
        
        current_directory = os.path.dirname(directory_path) or '.'
        os.makedirs(directory_path, exist_ok=True)
        
        directory_contents = get_directory_contents(current_directory)
        
        return jsonify({'message': 'Directory created successfully', 'directory_contents': directory_contents, 'current_directory': current_directory}), 200
    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500
    
@app.route('/remove_file', methods=['POST'])
def remove_file():
    try:
        data = request.json
        file_path = "./" + data['file_path']
        current_directory = os.path.dirname(file_path) or '.'
        if os.path.isfile(file_path):
            os.remove(file_path)
            directory_contents = get_directory_contents(current_directory)
            return jsonify({'message': 'File removed successfully', 'directory_contents': directory_contents, 'current_directory': current_directory}), 200
        else:
            directory_contents = get_directory_contents(current_directory)
            return jsonify({'error': 'File not found', 'directory_contents': directory_contents, 'current_directory': current_directory}), 404
    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500

@app.route('/remove_directory', methods=['POST'])
def remove_directory():
    try:
        data = request.json
        directory_path = "./" + data['directory_path']
        current_directory = os.path.dirname(directory_path) or '.'
        if os.path.isdir(directory_path):
            shutil.rmtree(directory_path)
            directory_contents = get_directory_contents(current_directory)
            return jsonify({'message': 'Directory removed successfully', 'directory_contents': directory_contents, 'current_directory': current_directory}), 200
        else:
            directory_contents = get_directory_contents(current_directory)
            return jsonify({'error': 'Directory not found', 'directory_contents': directory_contents, 'current_directory': current_directory}), 404
    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500

@app.route('/read_file', methods=['POST'])
def read_file():
    try:
        data = request.json
        file_path = "./" + data['file_path']
        start_line = data.get('start_line')
        end_line = data.get('end_line')

        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        if not start_line:
            return jsonify({'error': 'You forgot to specify start_line, the line to start reading the file from'}), 400
        
        if start_line < 1:
            return jsonify({'error': 'Invalid start_line index! Lines start from 1'}), 400

        with open(file_path, 'r') as file:
            lines = file.readlines()
            if end_line:
                lines = [{i + start_line: line} for i, line in enumerate(lines[start_line-1:end_line])]
            else:
                lines = [{i + start_line: line} for i, line in enumerate(lines[start_line-1:])]
                
        if len(lines) > 300:
            return jsonify({'warning': f'The file is too long, returning only lines {start_line}..{start_line+300}', 'file_content': lines[:300]}), 200

        return jsonify({'file_content': lines}), 200

    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500
    
@app.route('/remove_lines', methods=['POST'])
def remove_lines():
    try:
        data = request.json
        file_path = "./" + data['file_path']
        start_line = data.get('start_line')
        length = data.get('length')
        
        if not start_line:
            return jsonify({'error': 'You forgot to specify start_line, the line from which to start removing'}), 400
        
        if start_line < 1:
            return jsonify({'error': 'Invalid start_line index! Lines start from 1'}), 400
        
        if not length:
            return jsonify({'error': 'You forgot to specify length, the number of lines that should be removed from start_line'}), 400
            
        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404

        with open(file_path, 'r') as file:
            
            lines = file.readlines()
            
            lines = lines[:start_line-1] + lines[start_line - 1 + length:]

        with open(file_path, 'w') as file:
            file.writelines(lines)

        return jsonify({'message': f'File lines {start_line}..{start_line+length} removed successfully'}), 200

    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500
    
@app.route('/insert_lines', methods=['POST'])
def insert_lines():
    try:
        data = request.json
        file_path = "./" + data['file_path']
        start_line = data.get('start_line')
        new_lines = data.get('new_lines')
        
        if not start_line:
            return jsonify({'error': 'You forgot to specify start_line, the line your new lines should be inserted to'}), 400

        if start_line < 1:
            return jsonify({'error': 'Invalid start_line index! Lines start from 1'}), 400

        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404

        with open(file_path, 'r') as file:
            lines = file.readlines()
            
            for i in range(max(0, start_line + len(new_lines) - len(lines))):
                lines.append("")    
                
            new_lines = [x + "\n" for x in new_lines]
            
            lines = lines[:start_line-1] + new_lines + lines[start_line-1:]

        with open(file_path, 'w') as file:
            file.writelines(lines)

        return jsonify({'message': f'New lines inserted successfully into file lines {start_line}..{start_line+len(new_lines)}'}), 200

    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500
    
@app.route('/execute_command', methods=['POST'])
def execute_command():
    try:
        data = request.json
        command = data['command']

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return jsonify({'error': 'Command failed', 'details': stderr.decode()}), 400

        return jsonify({'message': 'Command executed successfully', 'output': stdout.decode()}), 200

    except Exception:
        error_traceback = traceback.format_exc()
        return jsonify({'error': error_traceback}), 500

if __name__ == '__main__':
    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    app.run(debug=True, use_reloader=False)

