# pip install bcrypt
"""
Docstring for backend.gateway.util.password
This project uses the 'bcrypt' algorithm directly to avoid passlib compatibility issues.
"""
import bcrypt

# verify the plain password: Verify whether the received password matches the stored hash value.
def verify_password(plain_password, hashed_password):
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        # bcrypt has a 72 byte limit. Truncate to prevent ValueError.
        if len(plain_password) > 72:
            plain_password = plain_password[:72]
            
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

# encrypt the plain password
def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if len(password) > 72:
        password = password[:72]
        
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt).decode('utf-8')