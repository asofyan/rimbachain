from flask import Flask, render_template, request, redirect, url_for, jsonify
from blockchain import Blockchain
from Crypto.PublicKey import RSA

app = Flask(__name__)

blockchain = Blockchain()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    blocks, total_pages = blockchain.get_blocks_paginated(page, 10)
    return render_template('index.html', blocks=blocks, page=page, total_pages=total_pages)

@app.route('/add_block', methods=['POST'])
def add_block():
    #print(request.form.get('miner_address'))
    miner_address = request.form.get('miner_address')
    blockchain.add_block(transactions=["New Block"], miner_address=miner_address)
    return redirect(url_for('index'))

@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return jsonify({'private_key': private_key, 'public_key': public_key})

@app.route('/get_balance', methods=['POST'])
def get_balance():
    data = request.get_json()
    public_key = data.get('public_key')
    balance = blockchain.get_balance(public_key)
    return jsonify({'balance': balance})

if __name__ == "__main__":
    app.run(debug=True)
