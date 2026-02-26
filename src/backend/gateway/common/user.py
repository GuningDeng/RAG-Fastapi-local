
import os;

current_file_path = os.path.abspath(__file__)

current_dir_path = os.path.dirname(current_file_path)

import json;
# This uses simulated user data, while a database would be used in a production environment.
data_fp = os.path.join(current_dir_path, 'users.json')
with open(data_fp, 'r', encoding='utf-8') as file:
    users_db = json.load(file)

from pydantic import BaseModel
from typing import Union, Optional

class User(BaseModel):
    userid:str
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str
    
def get_user(username: str):
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None
'''
return UserInDB(**user_dict)

equals to

UserInDB(
    username = user_dict["username"],
    email = user_dict["email"],
    full_name = user_dict["full_name"],
    disabled = user_dict["disabled"],
    hashed_password = user_dict["hashed_password"],
) 

'''

from util.password import verify_password

# Authenticate user by username and password.
def authenticate_user( username: str, password: str):
    user = get_user( username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

"""
Handle token
"""
# token entity
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

# Use OAuth2's Password stream and Bearer tokens.
# tokenUrl="token"` points to a relative URL token that has not yet been created. This relative URL is `./token`.
# This setting will require the client to send its username and password to the URL specified by the API: http://127.0.0.1:8000/token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from util.token import decode_access_token

# Retrieve current user's data based on token.
# This method accepts a string type token and returns a User class from Pydantic.
async def get_current_user(token: str = Depends(oauth2_scheme)):
    '''
    Security and dependency code are injected once, and each endpoint can use the same security system.
    '''
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        userid = decode_access_token(token)
        if userid is None or userid == "":
            raise credentials_exception
        user = get_user(username=userid)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception
    
# Retrieve data for the currently logged-in user and check if the user has been disabled.
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    '''
    In the endpoint, if the current user exists, is verified, and is active, then the user's data can be retrieved.
    '''
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

