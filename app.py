from flask import Flask, render_template, request, redirect, url_for, jsonify
from blockchain import Blockchain, Block
from wallet import generate_keys, Wallet

app = Flask(__name__)

# Import blockchain instance here to avoid circular imports 
from blockchain import blockchain

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

@app.route('/api/generate_wallet', methods=['POST'])
def api_generate_wallet():
    keys = generate_keys()
    return jsonify({
        'address': keys['address'],
        'public_key': keys['public_key'],
        'private_key': keys['private_key']
    })

@app.route('/api/send_transaction', methods=['POST'])
def send_transaction():
    data = request.get_json()
    required_fields = ['sender', 'recipient', 'amount', 'timestamp', 'public_key', 'signature']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing fields in transaction data'}), 400

    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']
    timestamp = data['timestamp']
    public_key = data['public_key']
    signature = data['signature']

    # Verify signature
    if not Wallet.verify_signature(public_key, sender, recipient, amount, timestamp, signature):
        return jsonify({'message': 'Invalid signature'}), 400

    transaction = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'timestamp': timestamp,
        'signature': signature
    }

    if blockchain.add_transaction(transaction):
        return jsonify({'message': 'Transaction added to pool'}), 201
    else:
        return jsonify({'message': 'Invalid or duplicate transaction'}), 400

@app.route('/api/pending_transactions', methods=['GET'])
def pending_transactions():
    return jsonify({'pending_transactions': blockchain.list_pending_transactions()}), 200

@app.route('/api/wallet_balance/<address>', methods=['GET'])
def wallet_balance(address):
    """Get the balance of a specific wallet address"""
    balance = blockchain.get_balance(address)
    return jsonify({'balance': balance})

@app.route('/api/create_wallet_from_private_key', methods=['POST'])
def create_wallet_from_private_key():
    """Create a wallet instance from a private key"""
    data = request.get_json()
    private_key = data.get('private_key')
    
    if not private_key:
        return jsonify({'message': 'Missing private key'}), 400
    
    try:
        from Crypto.PublicKey import RSA
        key = RSA.import_key(private_key.encode())
        public_key = key.publickey().export_key().decode('utf-8')
        
        # Generate address from public key
        import hashlib
        sha = hashlib.sha256(public_key.encode())
        address = sha.hexdigest()
        
        return jsonify({
            'address': address,
            'public_key': public_key
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error creating wallet: {str(e)}'}), 400

@app.route('/api/sign_transaction', methods=['POST'])
def sign_transaction():
    """Sign a transaction using the provided private key"""
    data = request.get_json()
    private_key = data.get('private_key')
    sender = data.get('sender')
    recipient = data.get('recipient')
    amount = data.get('amount')
    timestamp = data.get('timestamp')
    
    if not all([private_key, sender, recipient, amount, timestamp]):
        return jsonify({'message': 'Missing transaction data'}), 400
    
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Hash import SHA256
        from Crypto.Signature import pkcs1_15
        
        key = RSA.import_key(private_key.encode())
        data_string = f"{sender}:{recipient}:{amount}:{timestamp}"
        h = SHA256.new(data_string.encode())
        signature = pkcs1_15.new(key).sign(h)
        
        return jsonify({
            'signature': signature.hex()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error signing transaction: {str(e)}'}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
