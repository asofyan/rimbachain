from abc import ABC, abstractmethod
import hashlib
import json
import time
import math
import threading
from collections import deque

class ConsensusMechanism(ABC):
    """
    Abstract base class for consensus mechanisms.

    Expected interface:
    - mine_block(index, previous_hash, timestamp, transactions, target): Should return (nonce, merkle_root, block_hash)
    - validate_block(block, target): Should return True if the block is valid according to the consensus rules

    To add a new consensus mechanism, subclass ConsensusMechanism and implement these methods.
    """

    @abstractmethod
    def mine_block(self, index, previous_hash, timestamp, transactions, target):
        """
        Perform the consensus-specific block mining/creation process.

        Args:
            index (int): Block index.
            previous_hash (str): Hash of the previous block.
            timestamp (float): Timestamp for the new block.
            transactions (list): List of serialized transactions.
            target (int): Target value for mining (difficulty).

        Returns:
            tuple: (nonce, merkle_root, block_hash)
        """
        pass

    @abstractmethod
    def validate_block(self, block, target):
        """
        Validate a block according to the consensus rules.

        Args:
            block (Block): The block to validate.
            target (int): The target value for validation.

        Returns:
            bool: True if valid, False otherwise.
        """
        pass

class PoWConsensus(ConsensusMechanism):
    """
    Proof-of-Work consensus mechanism implementation.
    """

    def mine_block(self, index, previous_hash, timestamp, transactions, target):
        nonce = 0
        merkle_tree = MerkleTree(transactions)
        merkle_root = merkle_tree.root
        while True:
            block_string = f"{index}{previous_hash}{timestamp}{merkle_root}{nonce}"
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if int(block_hash, 16) <= target:
                return nonce, merkle_root, block_hash
            nonce += 1

    def validate_block(self, block, target):
        block_string = f"{block.index}{block.previous_hash}{block.timestamp}{block.merkle_root}{block.nonce}"
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()
        return int(block_hash, 16) <= target and block.hash == block_hash

class PoSConsensus(ConsensusMechanism):
    """
    Proof-of-Stake consensus mechanism (stub).

    Methods should be implemented to support:
    - Stake validation: Ensure validators have sufficient stake.
    - Leader selection: Select a validator to propose the next block.
    - Block validation: Validate blocks according to PoS rules.
    """

    def mine_block(self, index, previous_hash, timestamp, transactions, target):
        """
        Stub for PoS block creation.
        Should implement leader selection and block proposal logic.
        """
        raise NotImplementedError("PoS mining not implemented yet.")

    def validate_block(self, block, target):
        """
        Stub for PoS block validation.
        Should implement stake and block validation logic.
        """
        raise NotImplementedError("PoS validation not implemented yet.")

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None, signature=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = signature

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature
        }

    def serialize(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self):
        return hashlib.sha256(self.serialize().encode()).hexdigest()

    def is_rimbachain(self):
        return self.sender == "RIMBACHAIN"

    def is_valid(self):
        if self.amount <= 0:
            return False
        if not self.is_rimbachain() and not self.signature:
            return False
        return True

    def __eq__(self, other):
        return isinstance(other, Transaction) and self.hash() == other.hash()

    def __hash__(self):
        return hash(self.hash())

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
    DIFFICULTY_BLOCK_WINDOW = 10  # Number of blocks to average for difficulty adjustment
    TARGET_BLOCK_TIME = 10        # Target block time in seconds
    MAX_TARGET = 0x00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff  # Lower = harder

    def __init__(self, consensus_mechanism=None):
        self.chain = []
        self.target = self.MAX_TARGET  # Difficulty as a target value
        self.reward = 50  # Initial reward
        self.balances = {}  # Dictionary to keep track of balances
        self.transaction_pool = []
        self.tx_pool_lock = threading.Lock()
        # Use PoWConsensus as default if not provided
        self.consensus_mechanism = consensus_mechanism if consensus_mechanism is not None else PoWConsensus()
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = self.create_block(transactions=["Genesis Block"], miner_address="genesis")
        self.chain.append(genesis_block)

    def add_transaction(self, transaction):
        if isinstance(transaction, dict):
            transaction = Transaction(**transaction)
        if not transaction.is_valid():
            return False
        with self.tx_pool_lock:
            # Deduplication: do not add if already in pool
            if transaction in self.transaction_pool:
                return False
            self.transaction_pool.append(transaction)
        return True

    def remove_transaction(self, transaction):
        with self.tx_pool_lock:
            self.transaction_pool = [tx for tx in self.transaction_pool if tx != transaction]

    def list_pending_transactions(self):
        with self.tx_pool_lock:
            return [tx.to_dict() for tx in self.transaction_pool]

    def create_block(self, transactions, miner_address):
        index = len(self.chain)
        previous_hash = self.chain[-1].hash if self.chain else '0'
        timestamp = time.time()
        # Transactions must be serialized for MerkleTree
        tx_serialized = [tx.serialize() if isinstance(tx, Transaction) else str(tx) for tx in transactions]
        nonce, merkle_root, block_hash = self.consensus_mechanism.mine_block(index, previous_hash, timestamp, tx_serialized, self.target)
        # Store transactions as dicts for block serialization
        tx_dicts = [tx.to_dict() if isinstance(tx, Transaction) else tx for tx in transactions]
        # Store target in block for auditability
        return Block(index, previous_hash, timestamp, tx_dicts, nonce, merkle_root, block_hash, self.reward, miner_address)

    # proof_of_work method removed; handled by consensus_mechanism

    def add_block(self, transactions, miner_address):
        # Clean the miner address to remove extraneous newlines and spaces
        miner_address = self.clean_address(miner_address)

        # Collect valid transactions from pool if not provided
        if not transactions:
            with self.tx_pool_lock:
                # Only include valid and unique transactions
                unique_txs = []
                seen_hashes = set()
                for tx in self.transaction_pool:
                    if tx.is_valid():
                        h = tx.hash()
                        if h not in seen_hashes:
                            unique_txs.append(tx)
                            seen_hashes.add(h)
                transactions = unique_txs

        # Add rimbachain transaction for mining reward
        rimbachain_tx = Transaction(
            sender="RIMBACHAIN",
            recipient=miner_address,
            amount=self.reward,
            timestamp=time.time(),
            signature=None
        )
        transactions = [rimbachain_tx] + transactions

        block = self.create_block(transactions, miner_address)
        self.chain.append(block)
        # Difficulty adjustment
        self.adjust_difficulty()
        self.reward *= 0.95  # Decrease reward slightly each time

        # Update balances for all transactions in block
        for tx in transactions:
            if isinstance(tx, dict):
                tx = Transaction(**tx)
            elif isinstance(tx, str):
                # Skip balance updates for string transactions
                continue
                
            if tx.is_rimbachain():
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
            else:
                self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
                self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount

        # Remove included transactions from pool (except rimbachain)
        with self.tx_pool_lock:
            self.transaction_pool = [tx for tx in self.transaction_pool if tx not in transactions]

        # Always update the miner's balance with the block reward
        if miner_address in self.balances:
            self.balances[miner_address] += block.reward
        else:
            self.balances[miner_address] = block.reward

    def adjust_difficulty(self):
        # Only adjust if enough blocks
        if len(self.chain) < self.DIFFICULTY_BLOCK_WINDOW + 1:
            return
        window = self.chain[-self.DIFFICULTY_BLOCK_WINDOW:]
        timestamps = [block.timestamp for block in window]
        actual_time = timestamps[-1] - timestamps[0]
        expected_time = self.TARGET_BLOCK_TIME * self.DIFFICULTY_BLOCK_WINDOW

        # Avoid division by zero
        if actual_time == 0:
            actual_time = 1

        # Adjust target
        ratio = actual_time / expected_time
        new_target = int(self.target * ratio)
        # Clamp target to [1, MAX_TARGET]
        self.target = max(1, min(new_target, self.MAX_TARGET))

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

            # Use the stored target for each block if available, else fallback to current
            target = getattr(self, 'target', self.MAX_TARGET)
            _, merkle_root, block_hash = self.consensus_mechanism.mine_block(
                current_block.index,
                current_block.previous_hash,
                current_block.timestamp,
                [json.dumps(tx, sort_keys=True) for tx in current_block.transactions],
                target
            )
            if current_block.hash != block_hash:
                return False

        return True

    def print_chain(self):
        for block in self.chain:
            print(json.dumps(block.to_dict(), indent=4))

# Create a default blockchain instance that can be imported by other modules
blockchain = Blockchain()
