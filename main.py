import configparser
import threading
import time

from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import yaml
from flask_cors import cross_origin
from flask_socketio import SocketIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = "CSaSvOU6h1iMb15s+GsV5TuKYSbREcBZ/g1Gjh9nCec="

socketio = SocketIO(app, cors_allowed_origins='*')
connected_sids = set()  # 存放已连接的客户端

def read_config(file_path='./config/setup.conf'):
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


# @app.route('/drop', defaults={'sid': None})
# @app.route('/drop/<sid>')
# def hello(sid):
#     """发消息"""
#     if sid:
#         if sid in connected_sids:
#             socketio.emit('my_response', {'data': f'world!'}, room=sid)
#             return f'已发信息给{sid}'
#         else:
#             return f'{sid}不存在'
#     else:
#         socketio.emit('my_response', {'data': 'Hello!'})
#         return '已群发信息'


@app.route('/read_yaml')
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def read_yaml_data():
    try:
        with open('config.yaml', 'r') as file:  # 替换 'yourfile.yaml' 为您的 YAML 文件路径
            content = yaml.safe_load(file)
        return jsonify({"code": 0, "data": content["Rules"]})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/update_enabled', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def update_enabled():
    req = request.json
    rule_id = req.get('id')
    new_enabled = req.get('enabled')

    if rule_id is None or new_enabled is None:
        return jsonify({"error": "Missing id or enabled in request"}), 400

    # 以读取模式打开并加载数据
    with open('config.yaml', 'r') as file:
        data = yaml.safe_load(file)

    # 查找并更新指定规则
    rule_found = False
    for rule in data["Rules"]:
        if rule["Id"] == rule_id:
            rule["Enabled"] = new_enabled
            rule_found = True
            break

    # 如果找到规则，再次以写入模式打开文件并写入更新后的数据
    if rule_found:
        with open('config.yaml', 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
        return jsonify({"success": f"Rule with id {rule_id} updated"}), 200
    else:
        return jsonify({'error': 'Rule not found'}), 404


@app.route('/get_rule', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_rule():
    rule_id = request.args.get('id', type=int)
    with open('config.yaml', 'r') as file:  # 替换 'yourfile.yaml' 为您的 YAML 文件路径
        data = yaml.safe_load(file)
    print(data)
    if rule_id is not None:
        for rule in data["Rules"]:
            if rule["Id"] == rule_id:
                return jsonify({"code": "200", "data": rule})
        return jsonify({"error": "No rule found with the provided ID", "code": "-1"}), 404
    else:
        return jsonify({"error": "No ID provided", "code": "-1"}), 400


@app.route('/update_rules', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def update_rules():
    rule = request.get_json()
    print(rule)
    return jsonify({"success": f"Rule with id {rule.get('id')} updated"}), 200


if __name__ == '__main__':
    config = read_config()
    watched_path = config.get("path_config_file")
    #print(watched_path)
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watched_path, recursive=False)
    observer.start()

    file_observer_thread = threading.Thread(target=file_observer)
    file_observer_thread.start()
    try:
        socketio.run(app)
    finally:
        print("Stopping observer...")
        observer.stop()
        print("Waiting for observer to join...")
        observer.join()
        print("Observer has stopped.")
