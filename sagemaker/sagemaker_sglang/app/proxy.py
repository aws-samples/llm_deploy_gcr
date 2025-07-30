import json
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()
base_url = "http://127.0.0.1:8000"

async def proxy_request(request: Request, target_url: str):
    try:
        # Get request body
        body = await request.body()
        
        # Get request headers
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        # Get query parameters
        params = dict(request.query_params)
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=params,
                timeout=None
            )
            
            # For streaming responses
            if "content-type" in response.headers and "text/event-stream" in response.headers["content-type"]:
                return StreamingResponse(
                    response.aiter_bytes(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
            # For regular responses
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except httpx.RequestError as e:
        return Response(
            content=f"Proxy Error: {str(e)}",
            status_code=502
        )

@app.post("/invocations")
async def invocations_handler(request: Request):
    data = await request.json()
    if "messages" in data:
        target_url = f"{base_url}/v1/chat/completions"
    else:
        target_url = f"{base_url}/v1/completions"
    return await proxy_request(request, target_url)

@app.post("/v1/chat/completions")
async def chat_completions_handler(request: Request):
    target_url = f"{base_url}/v1/chat/completions"
    return await proxy_request(request, target_url)

@app.post("/v1/completions")
async def completions_handler(request: Request):
    target_url = f"{base_url}/v1/completions"
    return await proxy_request(request, target_url)

@app.get("/ping")
@app.get("/health")
async def health_check_handler(request: Request):
    target_url = f"{base_url}/health"
    return await proxy_request(request, target_url)

if __name__ == "__main__":
    print("Proxy server started at http://127.0.0.1:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
