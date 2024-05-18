import hashlib
import json
import time
import math
from collections import deque
from flask import Flask, request, jsonify

app = Flask(__name__)

class MerkleTree:
    def __init__(self, transactions):
        self.transactions = transactions
        self.root = self.build_merkle_tree(transactions)

    def build_merkle_tree(self, transactions):
        tree = deque(transactions)
        if len(tree) % 2 != 0:
            tree.append(tree[-1])  # Duplicate the last transaction if odd number

        while len(tree) > 1:
            temp_tree = deque()
            while tree:
                left = tree.popleft()
                right = tree.popleft()
                temp_tree.append(self.hash_pair(left, right))
            tree = temp_tree
            if len(tree) % 2 != 0 and len(tree) > 1:
                tree.append(tree[-1])

        return tree[0]

    @staticmethod
    def hash_pair(left, right):
        return hashlib.sha256((left + right).encode()).hexdigest()

class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, nonce, merkle_root, hash, reward, miner_address):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.merkle_root = merkle_root
        self.hash = hash
        self.reward = reward
        self.miner_address = miner_address

    def to_dict(self):
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root,
            'hash': self.hash,
            'reward': self.reward,
            'miner_address': self.miner_address,
        }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 1
        self.reward = 50  # Initial reward
        self.balances = {}  # Dictionary to keep track of balances
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = self.create_block(transactions=["Genesis Block"], miner_address="genesis")
        self.chain.append(genesis_block)

    def create_block(self, transactions, miner_address):
        index = len(self.chain)
        previous_hash = self.chain[-1].hash if self.chain else '0'
        timestamp = time.time()
        nonce, merkle_root, block_hash = self.proof_of_work(index, previous_hash, timestamp, transactions)
        return Block(index, previous_hash, timestamp, transactions, nonce, merkle_root, block_hash, self.reward, miner_address)

    def proof_of_work(self, index, previous_hash, timestamp, transactions):
        nonce = 0
        merkle_tree = MerkleTree(transactions)
        merkle_root = merkle_tree.root
        difficulty_prefix = '0' * int(self.difficulty)
        while True:
            block_string = f"{index}{previous_hash}{timestamp}{merkle_root}{nonce}"
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block_hash.startswith(difficulty_prefix):
                return nonce, merkle_root, block_hash
            nonce += 1

    def add_block(self, transactions, miner_address):
        # Clean the miner address to remove extraneous newlines and spaces
        miner_address = self.clean_address(miner_address)
        block = self.create_block(transactions, miner_address)
        self.chain.append(block)
        self.difficulty += 0.1  # Gradually increase difficulty
        self.reward *= 0.95  # Decrease reward slightly each time

        if miner_address in self.balances:
            self.balances[miner_address] += block.reward
        else:
            self.balances[miner_address] = block.reward

    def clean_address(self, address):
        return address.replace("\r", "").replace("\n", "")

    def get_balance(self, miner_address):
        # Clean the miner address to remove extraneous newlines and spaces
        miner_address = self.clean_address(miner_address)
        return self.balances.get(miner_address, 0)

    def get_blocks_paginated(self, page, page_size):
        start = (page - 1) * page_size
        end = start + page_size
        total_pages = math.ceil(len(self.chain) / page_size)
        return self.chain[start:end], total_pages

    def get_block(self, index):
        if index < len(self.chain):
            return self.chain[index]
        return None

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.previous_hash != previous_block.hash:
                return False

            _, merkle_root, block_hash = self.proof_of_work(
                current_block.index,
                current_block.previous_hash,
                current_block.timestamp,
                current_block.transactions
            )
            if current_block.hash != block_hash:
                return False

        return True

    def print_chain(self):
        for block in self.chain:
            print(json.dumps(block.to_dict(), indent=4))

blockchain = Blockchain()

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    transactions = data.get('transactions', [])
    miner_address = data.get('miner_address', 'unknown')
    blockchain.add_block(transactions, miner_address)
    return jsonify({"message": "Block added successfully"}), 201

@app.route('/get_blocks', methods=['GET'])
def get_blocks():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    blocks, total_pages = blockchain.get_blocks_paginated(page, page_size)
    return jsonify({
        "blocks": [block.to_dict() for block in blocks],
        "total_pages": total_pages,
        "current_page": page
    })

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
