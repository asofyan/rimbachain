from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256

class Wallet:
    def __init__(self):
        self.key = RSA.generate(2048)
        self.private_key = self.key.export_key().decode('utf-8')
        self.public_key = self.key.publickey().export_key().decode('utf-8')
        self.address = self.generate_address()

    def generate_address(self):
        sha = SHA256.new(self.public_key.encode())
        return sha.hexdigest()

    def get_keys(self):
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'address': self.address
        }

def generate_keys():
    wallet = Wallet()
    return wallet.get_keys()
