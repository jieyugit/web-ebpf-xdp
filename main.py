import configparser
import threading
import time
import atexit
import subprocess
import os
from flask import Flask, jsonify, request, render_template
import json
from flask_cors import cross_origin
from flask_socketio import SocketIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import uuid

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = "CSaSvOU6h1iMb15s+GsV5TuKYSbREcBZ/g1Gjh9nCec="

socketio = SocketIO(app, cors_allowed_origins='*')
connected_sids = set()  # 存放已连接的客户端
kernel_process = None
def read_config(file_path='./config/setting.conf'):
    config = configparser.ConfigParser()
    config.read(file_path)

    # 读取参数
    section = 'settings'
    config_dict = {key: config.get(section, key) for key in config.options(section)}
    return config_dict



class LogHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.new_log_lines = []
        self.last_line = 0
        self.lock = threading.Lock()

    # def on_any_event(self, event):
    #     print(f'Event type: {event.event_type}  Path: {event.src_path}')
    def on_modified(self, event):
        if event.is_directory:
            return
        # print(f'New log line added: {event.src_path}')
        with open(event.src_path, 'r') as f:
            lines = f.readlines()
            new_lines = lines[self.last_line:]
            with self.lock:
                self.new_log_lines.extend([line.strip() for line in new_lines])
            self.last_line = len(lines)


def file_observer():
    while True:
        time.sleep(1)  # 每隔1秒检查一次文件变化
        with event_handler.lock:
            if event_handler.new_log_lines:
                print(event_handler.new_log_lines)
                socketio.emit('my_response', {'data': event_handler.new_log_lines})
                event_handler.new_log_lines = []


@app.route('/')
def index():
    # if 'username' in session and session['username'] == "admin":
    #     return render_template('base.html')
    # return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/test')
def ttes():
    # if 'username' in session and session['username'] == "admin":
    #     return render_template('base.html')
    # return redirect(url_for('login'))
    return render_template('test.html')


@app.route('/login')
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def login():
    return render_template('login.html')


@app.route('/testindex')
def indexTest():
    return render_template('indexTest.html')


@socketio.on('connect')
def on_connect():
    connected_sids.add(request.sid)
    print(f'{request.sid} 已连接')


@socketio.on('disconnect')
def on_disconnect():
    connected_sids.remove(request.sid)
    print(f'{request.sid} 已断开')


@socketio.on('message')
def handle_message(message):
    """收消息"""
    data = message['data']
    print(f'{request.sid} {data}')



@app.route('/read_yaml')
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def read_yaml_data():
    try:
        with open('config.json', 'r') as file:
            content = json.load(file)
        return jsonify({"code": 0, "data": content["ens33"]})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/update_enabled', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def update_enabled():
    req = request.json
    rule_id = int(req.get('id'))
    new_enabled = int(req.get('enabled'))

    if rule_id is None or new_enabled is None:
        return jsonify({"error": "Missing id or enabled in request"}), 400

    try:
        rule_found = 0
        with open("config.json", 'r') as file:
            data = json.load(file)

        interface_rules = data.get("ens33", [])

        for rule in interface_rules:
            if int(rule.get("Id")) == int(rule_id):
                rule["Enabled"] = int(new_enabled)
                rule_found = 1
                break  # 找到匹配的规则后，更新字段并跳出循环
    except FileNotFoundError:
        print(f"Error: File not found at {config.json}")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON in file {config.json}")
    if rule_found:
        with open("config.json", 'w') as file:
            json.dump(data, file, indent=2)
        return jsonify({"success": f"Rule with id {rule_id} updated"}), 200
    else:
        return jsonify({'error': 'Rule not found'}), 404


@app.route('/get_rule', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_rule():
    rule_id = request.args.get('id', type=int)
    with open("config.json", 'r') as file:
        data = json.load(file)
    print(data)
    if rule_id is not None:
        for rule in data["ens33"]:
            if str(rule["Id"]) == str(rule_id):
                return jsonify({"code": "200", "data": rule})
        return jsonify({"error": "No rule found with the provided ID", "code": "-1"}), 404
    else:
        return jsonify({"error": "No ID provided", "code": "-1"}), 400


@app.route('/update_rules', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def update_rules():
    new_rule = request.get_json()
    id = int(new_rule.get("Id"))
    print(id)
    if str(id) is not None :
        try:
            with open("config.json", 'r') as file:
                data = json.load(file)
            for rule in data["ens33"]:
                # print(type(id))
                # print(type(rule["Id"]))
                if int(rule["Id"]) == int(id):
                    #print("found")
                    Action = int(new_rule.get("Action"))
                    Enabled =  int(rule["Enabled"])
                    rule.clear()
                    print(rule)
                    new_rule= washData(new_rule)
                    new_rule["Id"]=int(id)
                    new_rule["Enabled"]=int(Enabled)
                    new_rule["Action"] = int(Action)
                    print("Action = ",Action)
                    
                    
                    
                    rule.update(new_rule)
                    
                    print(rule)
                    print("========")
                    
                    with open("config.json", 'w') as file:
                        json.dump(data, file, indent=2)
                    return jsonify({"code":0,"success": f"Rule with id {rule.get('Id')} updated"}), 200

        except FileNotFoundError:
            jsonify({"code":-1,"error": f"Error: File not found at config.json"}), 200
        except json.JSONDecodeError:
            jsonify({"code":-1,"error": f"Error: File not found at config.json"}), 200
    return jsonify({"code": -1,"msg":"error"}), 200

@app.route('/get_paths', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_paths():
    return jsonify({"code": "0","data":"test/html"}), 200

@app.route('/up', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def up():
    global kernel_process  # 声明为全局变量，以便在退出处理函数中使用
    try:
        # 启动ls命令子进程
        kernel_process = subprocess.Popen(['bash', 'run.sh'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                          text=False)

        return jsonify({"code": 0, "data": "success"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/down', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def down():
    global kernel_process
    try:
        if kernel_process and kernel_process.poll() is None:
            # 子进程仍在运行，终止子进程
            kernel_process.terminate()
            kernel_process.wait()
            return jsonify({"code": 0, "message": "process terminated"})
        else:
            return jsonify({"code": -1, "message": "process is not running"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/insert', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def insert():
    global max_id
    new_rule = request.get_json()
    try:
        with open("config.json", 'r') as file:
            data = json.load(file)
        rules = data["ens33"]
        new_rule = washData(new_rule)
        new_rule["Enabled"] = 0
        new_rule["Id"] = int(max_id)
        new_rule["Action"] = int(new_rule["Action"])
        max_id = max_id + 1
        rules.append(new_rule)
        with open("config.json", 'w') as file:
            json.dump(data, file, indent=2)
        return jsonify({"code":0,"msg": "success"}), 200
            

    except FileNotFoundError:
            jsonify({"code":-1,"error": f"Error: File not found at config.json"}), 200
    except json.JSONDecodeError:
            jsonify({"code":-1,"error": f"Error: File not found at config.json"}), 200
    return jsonify({"code": -1,"msg":"error"}), 200

@atexit.register
def exit_handler():
    global kernel_process
    if kernel_process and kernel_process.poll() is None:
        # 子进程仍在运行，终止子进程
        kernel_process.terminate()
        kernel_process.wait()

def washData(l):
    for key, value in l.items():
        if value == "on":
            l[key] = 1

    keys_to_remove = [key for key, value in l.items() if value == "" or value == 0]
    for key in keys_to_remove:
        del l[key]
    
    if "ICMPTypeCode" in l.keys():
        value = l.get("ICMPTypeCode")
        l.pop("ICMPTypeCode")
        l['ICMPCode'] = int(value.split("_")[1])
        l['ICMPType'] = int(value.split("_")[0])
    if 'TCPSport' in l:
        l['TCPSport'] = int(l['TCPSport'])
    if 'TCPDport' in l:
        l['TCPDport'] = int(l['TCPDport'])
    if 'UDPSport' in l:
        l['UDPSport'] = int(l['UDPSport'])
    if 'UDPDport' in l:
        l['UDPDport'] = int(l['UDPDport'])
    return l
        
    
    

if __name__ == '__main__':
    with open("config.json", 'r') as file:
        data = json.load(file)
    global max_id
    max_id = int(max(rule["Id"] for rule in data["ens33"]))+1
    # 获取当前脚本所在目录的绝对路径
    current_directory = os.path.abspath(os.path.dirname(__file__))

    # 构建配置文件路径
    config_file_path = os.path.join(current_directory, 'config', 'setting.conf')

    # 构建要写入配置文件的路径
    absolute_path = os.path.abspath(current_directory)

    # 创建配置文件对象
    config = configparser.ConfigParser()

    # 更新配置文件的 [settings] 部分
    config['settings'] = {'path_filter_profile': os.path.join(absolute_path, 'config.json'),
                      'path_config_file': absolute_path+"/config"}

    # 写入配置文件
    with open(config_file_path, 'w') as config_file:
         config.write(config_file)

    print(f"绝对路径已写入配置文件: {config_file_path}")
    config = read_config()
    watched_path = config.get("path_config_file")
    print(watched_path)
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watched_path, recursive=False)
    observer.start()

    file_observer_thread = threading.Thread(target=file_observer)
    file_observer_thread.start()
    try:
        socketio.run(app,host="0.0.0.0")
    finally:
        print("Stopping observer...")
        observer.stop()
        print("Waiting for observer to join...")
        observer.join()
        print("Observer has stopped.")
