import os
from flask import Flask, jsonify, make_response, request, render_template
import json
import crawler3
from conf import host, port

app = Flask(__name__)
#app.config['JSON_AS_ASCII'] = False


# html API
@app.route('/', methods=['GET'])
def raiz():
    a = request.remote_addr
    print('\n\nvariável'), a
    return render_template('index.html'), 200

@app.route('/veiculo')
def veiculo():
    placa = request.args.get('placa')
    renavam = request.args.get('renavam')
    data = json.dumps([{"placa":placa, "renavam":renavam}])
    response = crawler3.craw(data)
    return json.dumps(response)

@app.route('/veiculos', methods=['POST'])
def veiculos():
    data = request.get_data()
    response = crawler3.craw(data)
    return json.dumps(response)

if __name__ == "__main__":
    app.run(debug=True, host=host, port=port)