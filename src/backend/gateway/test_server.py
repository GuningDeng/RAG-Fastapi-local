#!/usr/bin/env python
"""Test version of API gateway to debug issues"""
import sys
import traceback

print("Step 1: Importing modules...")
try:
    from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import OAuth2PasswordRequestForm
    from config.config import config
    from common.user import authenticate_user, Token
    from util.token import create_access_token
    from util.ttlcache import Cache, Error
    from util.captcha import generate_captcha
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    import uvicorn
    print("[OK] All imports successful")
except Exception as e:
    print(f"[FAILED] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Creating FastAPI app...")
try:
    app = FastAPI()
    custom_header_name = "X-Captcha-ID"
    
    # CORS configuration
    origins = config["origins"]
    print(f"  CORS origins: {origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[custom_header_name, "Cache-Control"],
    )
    print("✓ App created with CORS middleware")
except Exception as e:
    print(f"✗ App creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Setting up cache...")
try:
    _cache = Cache(max_size=300, ttl=300)
    print("✓ Cache initialized")
except Exception as e:
    print(f"✗ Cache setup failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Setting up routes...")
try:
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    @app.get("/captcha")
    async def get_captcha():
        if _cache.is_full():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
        
        captcha_id, captcha_text, captcha_image = generate_captcha()
        print(f"Generated captcha: {captcha_id}")
        
        result = _cache.add(captcha_id, (captcha_text, captcha_image))
        if result != Error.OK:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
        
        buffer = BytesIO()
        captcha_image.save(buffer, format="PNG")
        buffer.seek(0)
        headers = {custom_header_name: captcha_id, "Cache-Control": "no-store"}
        return StreamingResponse(buffer, headers=headers, media_type="image/png")
    
    @app.post("/token")
    async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        remember: bool | None = Body(None),
        captcha_id: str | None = Body(None),
        captcha_input: str | None = Body(None),
    ) -> Token:
        print(f"Login attempt: {form_data.username}")
        try:
            # Verify captcha
            error, value = _cache.get(captcha_id)
            if error != Error.OK or value is None:
                print(f"  Captcha check failed: error={error}, value={value}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired captcha ID")
            
            captcha_text = value[0]
            if not captcha_text:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired captcha ID")
            
            if captcha_text.upper() != captcha_input.upper():
                print(f"  Captcha mismatch: {captcha_text} != {captcha_input}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect captcha")
            
            print(f"  Captcha verified")
            
            # Authenticate user
            user = authenticate_user(form_data.username, form_data.password)
            if not user:
                print(f"  Authentication failed")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Username or password incorrect",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            print(f"  User authenticated: {user.username}")
            
            # Generate token
            m = ACCESS_TOKEN_EXPIRE_MINUTES if remember else 0
            access_token = create_access_token(data={"sub": user.username}, encrypted_text=user.userid, expire_minutes=m)
            print(f"  Token created")
            
            return Token(access_token=access_token, token_type="bearer")
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    
    print("✓ Routes configured")
except Exception as e:
    print(f"✗ Route setup failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Starting server...")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = config["token"]["expires_time"]
    print(f"✓ Ready to start server on 0.0.0.0:8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)
except Exception as e:
    print(f"✗ Server start failed: {e}")
    traceback.print_exc()
    sys.exit(1)
