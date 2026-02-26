'''
Docstring for backend.gateway.util.token
pip install pyjwt
'''

import math
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

sys.path.append(str(Path(__file__).resolve().parent))

from aes import encrypt, decrypt
from config.config import config

separator = "\u2016"

# for JWT signing
SECRET_KEY = config['secret']["jwt_key"]

# The algorithm for JWT encoding and decoding
ALGORITHM = "HS256"

DEFAULT_TOKEN_EXPIRE_MINUTES = config['token']["default_expires_time"]   #default expire time in minutes

# encode signing: userid + timestamp
def get_sign(encrypted_text,access_token_expires):
    try:
        t = str(math.floor(access_token_expires.timestamp()))
        #print(f"access_token_expires is {t}")
        src_text = encrypted_text + separator + t
        return encrypt(src_text)
    except Exception as e:
        print(f"Error in get_sign: {e}")
        raise

# generate jwt token
def create_access_token(data: dict,encrypted_text: str=None, expire_minutes: int | None = None):
    try:
        to_encode = data.copy()
        if expire_minutes is not None and expire_minutes > 0:
            expires_delta = timedelta(minutes=expire_minutes) 
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_TOKEN_EXPIRE_MINUTES)
        if encrypted_text is not None and encrypted_text != "": #encrypt signing
            sign = get_sign(encrypted_text,expire)
            to_encode.update({"sign": sign})
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Error in create_access_token: {e}")
        raise


# parse and validate JWT
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # validate JWT integrity
        sub:str = payload.get("sub")
        if sub is None or sub == "":
            raise InvalidTokenError
        sign:str = payload.get("sign")
        if sign is None or sign == "":
            raise InvalidTokenError
        exp:int = payload.get("exp")
        if exp is None or exp == 0:
            raise InvalidTokenError
        
        # determine if JWT has expired
        now = math.floor(datetime.now(timezone.utc).timestamp())
        if now > exp:
            raise ExpiredSignatureError
        
        # validate encrypted signature
        plain_sign = decrypt(sign)
        if plain_sign is None:
            raise InvalidTokenError
        arr = plain_sign.split(separator)
        if len(arr) != 2:
            raise InvalidTokenError
        userid = arr[0]
        timestamp = int(arr[1])
        if timestamp != exp:
            raise InvalidTokenError        
        return userid    
    except Exception:
        raise InvalidTokenError
