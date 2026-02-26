"""
Docstring for backend.gateway.api gateway
@description:
"""
from io import BytesIO
from fastapi import Body, Depends, FastAPI, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm

from typing import Annotated

from config.config import config
ACCESS_TOKEN_EXPIRE_MINUTES = config["token"]["expires_time"]

app = FastAPI()

custom_header_name = "X-Captcha-ID"

# CORS allow 
from fastapi.middleware.cors import CORSMiddleware
origins = config["origins"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[custom_header_name,"Cache-Control"],  # These are the headers that the frontend is allowed to access; otherwise, the client will not be able to obtain this header information. 
)

# print log request, used for debug with client
async def log_request_details(request: Request):
    client_host = request.client.host
    client_port = request.client.port
    method = request.method
    url = request.url
    headers = request.headers
    body = None
    if request.form:    
        body = await request.form()
    elif request.body:
        body = await request.body()

    print(f"Client: {client_host}:{client_port}")
    print(f"Method: {method} URL: {url}")
    print(f"Headers: {headers}")
    print(f"Body: {body if body else 'No Body'}")

"""
captcha
"""
from util.captcha import generate_captcha
from util.ttlcache import Cache,Error
_cache = Cache(max_size=300, ttl=300)    # 300 caches, each cache 5 mints


@app.get("/captcha")
def get_captcha():

    if _cache.is_full():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
    
    captcha_id,captcha_text,captcha_image =  generate_captcha()
    print(f"generate captcha: {captcha_id} {captcha_text}")
    result = _cache.add(captcha_id,(captcha_text,captcha_image))
    if result != Error.OK:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    # return image stream
    buffer = BytesIO()
    captcha_image.save(buffer, format="PNG")
    buffer.seek(0)
    headers = {custom_header_name: captcha_id,"Cache-Control": "no-store"}
    #print(headers)
    return StreamingResponse(buffer, headers=headers, media_type="image/png")

"""
user verify
""" 

from util.token import create_access_token
from common.user import authenticate_user,Token,User,get_current_active_user

# log in and get access token
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),remember: bool|None=Body(None),
    captcha_id: str|None=Body(None), captcha_input: str|None=Body(None),log_details: None = Depends(log_request_details))-> Token:
    '''
    OAuth2PasswordRequestForm : This class is a helper provided by fastapi.security module to handle from data for OAuth2 password flow.

    username
    password
    scope、grant_type、client_id.etc are optional fields.
    '''
    try:
        # verify captcha   
        error, value = _cache.get(captcha_id)
        if error != Error.OK or value is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired captcha ID")
        
        captcha_text = value[0]

        if not captcha_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired captcha ID")

        if captcha_text.upper() != captcha_input.upper():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect captcha")
        
        # account verify
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username or password incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
        m = 0
        if remember:
            m = ACCESS_TOKEN_EXPIRE_MINUTES
            
        # In the JWT specification, the value of the 'sub key' is the subject of the token.
        access_token = create_access_token(data={"sub": user.username},encrypted_text=user.userid, expire_minutes=m)

        # In this example, we are wsing Bearer token, so the token type should be bearer.
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


# Get current user info
@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    '''
    In dependency injection systeem handles security mechanisms.
    Here, the type of current_user is declared as Pydantic's User model, which helps with code completion and type checking within the function.
    The get_current_user dependency receives a str type token from the sub-dependency oauth2_scheme.
    FastAPI validates the Authorization header in the request, checking if its value consists of a Bearer and a token, and returns the token string. If the Authorization header is not found, or if its value is not a Bearer and a token, FastAPI directly returns a 401 error status code (UNAUTHORIZED).
    '''
    return current_user

'''
APIGateway Service
'''

import httpx

time_out = config["time_out"]
services = config["services"]

'''
The key of services is the service name.The client passes in the service name when requesting, and the gateway finds the corresponding service address according to the service name.  
'''

# Receive client requests and forward them to backend services
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(service: str, path: str, request: Request,current_user: Annotated[User, Depends(get_current_active_user)]):
    '''
    !Attention: The gateway does not forward headers to the backend service, which is simpler.
    '''
    
    if service not in services:
        raise HTTPException(status_code=401, detail="The service does not found")
    
    headers = {"userid":current_user.userid}

    # To get data from client request
    client_request_data = await request.json()
        
    service_url = services[service]
    url = f"{service_url}/{path}"   

    # use async httpx to forward request to backend service, non-blocking.
    async with httpx.AsyncClient() as client:
        '''
        !Attention: The default timeout for httpx.AsyncClient is 5 seconds. When calling backend services based on LLMs, it often times out, so the timeout here is set to 30 seconds.
        '''
        response = await client.post(url=url, json=client_request_data,headers=headers,timeout=time_out)
        #print(response)
        return response.json()

if __name__ == "__main__":
    import uvicorn
    import sys

    print("Starting API Gateway...")
    print(f"Origins configured: {config['origins']}")
    
    try:
        # API documentation:
        # http://127.0.0.1:8000/docs/ 
        # http://127.0.0.1:8000/redoc/
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)