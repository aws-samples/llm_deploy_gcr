import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
import json

app = FastAPI()
base_url = "http://127.0.0.1:8000"

# Global HTTP client with automatic connection pool management
client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=100, max_connections=1000),
    timeout=httpx.Timeout(300.0, connect=10.0)
)

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

async def endpoint_request(request: Request, target_path: str):
    """Generic SageMaker endpoint request handler"""
    try:
        # Read request body
        body = await request.body()
        
        # Build target URL
        target_url = f"{base_url}{target_path}"
        
        # Stream response
        async def generate():
            # Use stream=True for real streaming requests
            async with client.stream(
                method=request.method,
                url=target_url,
                content=body,
                headers=dict(request.headers),
                params=dict(request.query_params)
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
            
        return StreamingResponse(
            generate()
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gateway Timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Endpoint Error: {str(e)}")

@app.post("/invocations")
async def invocations(request: Request):
    return await endpoint_request(request, "/v1/chat/completions")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # Check request body to determine routing
    body = await request.body()
    try:
        payload = json.loads(body)
        if "messages" in payload:
            target_path = "/v1/chat/completions"
        else:
            target_path = "/v1/completions"
    except:
        target_path = "/v1/chat/completions"
    
    # Rebuild request object
    class EndpointRequest:
        def __init__(self, original_request, body):
            self.method = original_request.method
            self.headers = original_request.headers
            self.query_params = original_request.query_params
            self._body = body
        
        async def body(self):
            return self._body
    
    endpoint_req = EndpointRequest(request, body)
    return await endpoint_request(endpoint_req, target_path)

@app.post("/v1/completions")
async def completions(request: Request):
    return await endpoint_request(request, "/v1/completions")

@app.get("/ping")
async def ping(request: Request):
    return await endpoint_request(request, "/")

@app.get("/health")
async def health(request: Request):
    return await endpoint_request(request, "/")

if __name__ == "__main__":
    import uvicorn
    print("FastAPI SageMaker Endpoint server started at http://127.0.0.1:8080")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        workers=1,
        access_log=False
    )
