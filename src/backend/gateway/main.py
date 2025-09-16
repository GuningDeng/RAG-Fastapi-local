from crypt import methods
import http
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

services = {
    "consulting": "http://localhost:8001",
    "translation": "http://localhost:8002",
    # "llm": "http://localhost:8003"
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, request: Request):
    if service not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    url = f"{services[service]}/{path}"
    # headers = {key: value for key, value in request.headers.items()}
    if request.method == "POST":
        body = await request.json()
    else:
        body = None
    # response = requests.request(
    #     method=request.method,
    #     url=url,
    #     headers=headers,
    #     json=body
    # )
    # return response.json()
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            json=body
        )
        return response.json()

    if __name__ == "__main__":
        # http://localhost:8000/docs/
        uvicorn.run(app, host="0.0.0.0", port=8000)