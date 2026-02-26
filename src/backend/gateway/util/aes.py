"""
AES encryption/decryption utilities for backend.gateway.util
Requires: pip install pycryptodome
"""

import base64
import sys
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Load configuration
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.config import config

# Initialize AES key and IV once
_KEY = config['secret']["aes_key"].encode('utf-8')
_IV = config['secret']["aes_iv"].encode('utf-8')
"""
These keys and IVs are just examples and should not be used in a production environment. 
"""

def encrypt(text: str) -> str:
    """
    Encrypt plaintext using AES-CBC encryption.
    
    Args:
        text: Plaintext string to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    try:
        cipher = AES.new(_KEY, AES.MODE_CBC, _IV)
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Error in aes.encrypt: {e}")
        raise


def decrypt(encrypted_text: str) -> str:
    """
    Decrypt AES-CBC encrypted text.
    
    Args:
        encrypted_text: Base64-encoded encrypted string
        
    Returns:
        Decrypted plaintext string
    """
    cipher = AES.new(_KEY, AES.MODE_CBC, _IV)
    decoded_data = base64.b64decode(encrypted_text)
    decrypted = unpad(cipher.decrypt(decoded_data), AES.block_size)
    return decrypted.decode('utf-8')



if __name__ == "__main__":
    text = "hello_world"
    encrypted_text = encrypt(text)
    decrypted_text = decrypt(encrypted_text)

    print(f"Original text:   {text}")
    print(f"Encrypted text:  {encrypted_text}")
    print(f"Decrypted text:  {decrypted_text}")
    print(f"Match: {text == decrypted_text}")
