from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

# Remove direct import of blockchain instance to avoid circular imports
# from blockchain import blockchain

class Wallet:
    def __init__(self):
        self.key = RSA.generate(2048)
        self.private_key = self.key.export_key().decode('utf-8')
        self.public_key = self.key.publickey().export_key().decode('utf-8')
        self.address = self.generate_address()

    def generate_address(self):
        sha = SHA256.new(self.public_key.encode())
        return sha.hexdigest()

    @property
    def balance(self):
        """
        Get the current balance for this wallet from the blockchain.
        Returns 0 if the wallet address is not found in the blockchain.
        """
        # Import blockchain here to avoid circular imports
        from blockchain import blockchain
        return blockchain.get_balance(self.address)

    def get_keys(self):
        """
        Get the wallet keys and balance. Balance is fetched from blockchain.
        """
        # Import blockchain here to avoid circular imports
        from blockchain import blockchain
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'address': self.address,
            'balance': blockchain.get_balance(self.address)
        }

    def sign_transaction(self, sender, recipient, amount, timestamp):
        """
        Sign transaction data with the wallet's private key.
        Returns the signature as a hex string.
        """
        data = f"{sender}:{recipient}:{amount}:{timestamp}"
        h = SHA256.new(data.encode())
        signature = pkcs1_15.new(self.key).sign(h)
        return signature.hex()

    @staticmethod
    def verify_signature(public_key, sender, recipient, amount, timestamp, signature):
        """
        Verify the signature of transaction data using the provided public key.
        Returns True if valid, False otherwise.
        """
        from Crypto.PublicKey import RSA
        from Crypto.Signature import pkcs1_15
        from Crypto.Hash import SHA256

        data = f"{sender}:{recipient}:{amount}:{timestamp}"
        h = SHA256.new(data.encode())
        try:
            key = RSA.import_key(public_key.encode())
            pkcs1_15.new(key).verify(h, bytes.fromhex(signature))
            return True
        except (ValueError, TypeError):
            return False

def generate_keys():
    wallet = Wallet()
    return wallet.get_keys()
