
from flask import Flask, jsonify, request
import yaml
from flask_cors import cross_origin

app = Flask(__name__)

@app.route('/read_yaml')
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def read_yaml_data():
    try:
        with open('config.yaml', 'r') as file:  # 替换 'yourfile.yaml' 为您的 YAML 文件路径
            content = yaml.safe_load(file)
        return jsonify({"code":0,"data":content["Rules"]})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/update_enabled', methods=['POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
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
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def get_rule():
    rule_id = request.args.get('id', type=int)
    with open('config.yaml', 'r') as file:  # 替换 'yourfile.yaml' 为您的 YAML 文件路径
        data = yaml.safe_load(file)
    print(data)
    if rule_id is not None:
        for rule in data["Rules"]:
            if rule["Id"] == rule_id:
                return jsonify({"code": "200", "data": rule})
        return jsonify({"error": "No rule found with the provided ID","code":"-1"}), 404
    else:
        return jsonify({"error": "No ID provided","code":"-1"}), 400

if __name__ == '__main__':
    app.run(debug=True)
