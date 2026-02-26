"""
FastAPI service for the consulting service. RAG application with local embedding model and LLM.
RAG (Retrieval-Augmented Generation) is a technique that combines the power of retrieval-based models and generative models to generate more accurate and contextually relevant responses.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import httpx
import uvicorn
import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncIterator, Union

# Configuration for Ollama API
OLLAMA_API_BASE_URL = os.environ.get("OLLAMA_API_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "YOUR_LLM_NAME")

try:
    from db_operators import collection
except ImportError:
    from db_operators import collection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class ConsultingRequest(BaseModel):
    question: str
    history: list[dict] = []
    stream: bool = True

@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    # Ensure the files directory exists
    os.makedirs("uploads", exist_ok=True)
    
    try:
        file_location = os.path.join("uploads", file.filename)
        
        # Save the file
        content = await file.read()
        with open(file_location, "wb") as file_object:
            file_object.write(content)
        
        # Process the file
        from file_handlers import process_file
        # Update the file location to the processed file
        # file_location = file_location.replace(".", "_processed.")
        try:
            from db_operators import collection
        except ImportError:
            from db_operators import collection
        
        # Process the file to get chunks
        chunks = process_file(file_location)

        # Add chunks to the collection
        collection.add(
            ids=[f"{file.filename}-{i}" for i in range(len(chunks))],
            documents=[chunk.page_content for chunk in chunks],
            metadatas=[{"source": file.filename}] * len(chunks)
        )

        return JSONResponse(
            status_code=200,
            content={"info": f"File '{file.filename}' processed and added to the knowledge base"}
        )
            
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# Define API description
app.title = "RAG API"
app.description = "A FastAPI application for Retrieval-Augmented Generation (RAG)"
app.version = "1.0.0"

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []

class StreamChunk(BaseModel):
    text: str
    done: bool = False
    sources: List[Dict[str, Any]] = []

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ConsultingRequest):
    try:
        # Check if the collection is initialized
        if collection is None:
            raise HTTPException(status_code=503, detail="Vector database is not initialized. Please check server logs.")

        # Check if the collection is empty
        try:
            collection_count = collection.count()
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error accessing vector database: {str(e)}")

        if collection_count == 0:
            raise HTTPException(status_code=400, detail="No documents found. Please upload a document first.")

        # Query the collection
        result = collection.query(
            query_texts=[request.question],
            n_results=3
        )

        if not result or not result.get("documents") or len(result['documents'][0]) == 0:
            return ChatResponse("I couldn't find relevant information to answer your question.")

        context = "\n".join(result['documents'][0])

        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in request.history])

        prompt = f"""
        You are a helpful AI assistant. Use the following context to answer the question.
        Context: {context}
        Chat History: {history_str}
        Question: {request.question}
        Answer:"""

        sources = [
            {"content": doc, "source": meta.get("source", "unknown")}
            for doc, meta in zip(result['documents'][0], result['metadatas'][0])
        ]

        if request.stream:
            return StreamingResponse(
                content=stream_llm_response(prompt, sources),
                media_type="text/event-stream"
            )
        else:

            max_retries = 3
            retry_delay = 1 # seconds

            for attempt in range(max_retries):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    try:
                        try:
                            health_check = await client.get(f"{OLLAMA_API_BASE_URL}/api/version")
                            if health_check.status_code != 200:
                                raise HTTPException(status_code=503, detail=f"Ollama service is not responding properly. Please ensure it's running at {OLLAMA_API_BASE_URL}")
                        except httpx.RequestError:
                            raise HTTPException(status_code=503, detail=f"Cannot connect to Ollama service at {OLLAMA_API_BASE_URL}")

                        response = await client.post(
                            f"{OLLAMA_API_BASE_URL}/api/generate",
                            json={
                                "model": OLLAMA_MODEL,
                                "prompt": prompt,
                                "max_tokens": 512,
                                "temperature": 0.3,
                                "top_p": 0.9,
                                "stream": False,
                            }
                        )

                        if response.status_code == 200:
                            llm_response = response.json()
                            answer_text = llm_response.get("text", "")
                            
                            return ChatResponse(answer=answer_text, sources=sources) 
                        else:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            raise HTTPException(status_code=response.status_code, detail=f"Ollama service returned an error: {response.text}")
                        
                    except httpx.HTTPStatusError as e:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        raise HTTPException(status_code=503, detail=f"Ollama service returned an error: {e.response.text}")

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": app.version}



# Streaming response function
async def stream_llm_response(prompt: str, sources: List[Dict[str, Any]]) -> AsyncIterator[str]:
    """Stream the LLM response from Ollama API"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Check if Ollama is running
            try:
                health_check = await client.get(f"{OLLAMA_API_BASE_URL}/api/version")
                if health_check.status_code != 200:
                    error_msg = json.dumps({"error": f"Ollama service is not responding properly"})
                    yield f"data: {error_msg}\n\n"
                    return
            except httpx.RequestError:
                error_msg = json.dumps({"error": f"Cannot connect to Ollama service"})
                yield f"data: {error_msg}\n\n"
                return
            
            # Make streaming request to Ollama
            async with client.stream(
                "POST",
                f"{OLLAMA_API_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "max_tokens": 512,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "stream": True,
                },
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    error_msg = json.dumps({"error": f"LLM API error: {response.status_code}"})
                    yield f"data: {error_msg}\n\n"
                    return
                
                # Process the streaming response
                full_text = ""
                async for chunk in response.aiter_lines():
                    if not chunk.strip():
                        continue
                    
                    try:
                        chunk_data = json.loads(chunk)
                        text_chunk = chunk_data.get("text", "")
                        full_text += text_chunk
                        
                        # Send the chunk with done=False
                        stream_chunk = StreamChunk(
                            text=text_chunk,
                            done=False,
                            sources=[] if chunk_data.get("done", False) else []
                        )
                        yield f"data: {json.dumps(stream_chunk.model_dump())}\n\n"
                        
                        # If this is the final chunk, send a done message with sources
                        if chunk_data.get("done", False):
                            final_chunk = StreamChunk(
                                text="",
                                done=True,
                                sources=sources
                            )
                            yield f"data: {json.dumps(final_chunk.model_dump())}\n\n"
                            break
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
        
        except Exception as e:
            error_msg = json.dumps({"error": f"Error streaming response: {str(e)}"})
            yield f"data: {error_msg}\n\n"



# Error handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": f"An unexpected error occurred: {str(exc)}"},
    )


if __name__ == "__main__":
    # Create files directory if it doesn't exist
    os.makedirs("files", exist_ok=True)

    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5001))

    # Run the application with a different port to avoid conflicts
    # Access API docs at: http://127.0.0.1:{port}/docs/ or http://127.0.0.1:{port}/redoc/
    # Start the FastAPI server
    print(f"Starting server on port {port}")    
    uvicorn.run(app, host="0.0.0.0", port=port)