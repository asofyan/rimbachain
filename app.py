from flask import Flask, render_template, request, redirect, url_for, jsonify
from blockchain import Blockchain
from wallet import generate_keys

app = Flask(__name__)

blockchain = Blockchain()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    blocks, total_pages = blockchain.get_blocks_paginated(page, 10)
    return render_template('index.html', blocks=blocks, page=page, total_pages=total_pages)

@app.route('/add_block', methods=['POST'])
def add_block():
    miner_address = request.form.get('miner_address')
    transactions = ["New Block"]
    blockchain.add_block(transactions, miner_address)
    return redirect(url_for('index'))

@app.route('/generate_keys', methods=['GET'])
def generate_keys_route():
    keys = generate_keys()
    return jsonify(keys)

@app.route('/get_balance', methods=['POST'])
def get_balance():
    data = request.get_json()
    public_key = data.get('public_key')
    balance = blockchain.get_balance(public_key)
    return jsonify({'balance': balance})

@app.route('/synchronize', methods=['POST'])
def synchronize():
    data = request.get_json()
    external_blocks = data.get('blocks', [])
    for block_data in external_blocks:
        block = Block(**block_data)
        blockchain.chain.append(block)
    return jsonify({"message": "Blockchain synchronized successfully"}), 200

@app.route('/transfer_reward', methods=['POST'])
def transfer_reward():
    data = request.get_json()
    from_address = blockchain.clean_address(data.get('from_address'))
    to_address = blockchain.clean_address(data.get('to_address'))
    amount = data.get('amount')

    if blockchain.balances.get(from_address, 0) >= amount:
        blockchain.balances[from_address] -= amount
        if to_address in blockchain.balances:
            blockchain.balances[to_address] += amount
        else:
            blockchain.balances[to_address] = amount
        return jsonify({"message": "Transfer successful"}), 200
    else:
        return jsonify({"message": "Insufficient balance"}), 400

@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
