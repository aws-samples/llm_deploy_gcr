import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
import json

app = FastAPI()
base_url = "http://127.0.0.1:8000"

# 全局HTTP客户端，自动管理连接池
client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=100, max_connections=1000),
    timeout=httpx.Timeout(300.0, connect=10.0)
)

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

async def proxy_request(request: Request, target_path: str):
    """通用代理请求处理"""
    try:
        # 读取请求体
        body = await request.body()
        
        # 构建目标URL
        target_url = f"{base_url}{target_path}"
        
        # 流式返回响应
        async def generate():
            # 使用stream=True进行真正的流式请求
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
        raise HTTPException(status_code=502, detail=f"Proxy Error: {str(e)}")

@app.post("/invocations")
async def invocations(request: Request):
    return await proxy_request(request, "/v1/chat/completions")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # 检查请求体决定路由
    body = await request.body()
    try:
        payload = json.loads(body)
        if "messages" in payload:
            target_path = "/v1/chat/completions"
        else:
            target_path = "/v1/completions"
    except:
        target_path = "/v1/chat/completions"
    
    # 重新构建请求对象
    class ProxyRequest:
        def __init__(self, original_request, body):
            self.method = original_request.method
            self.headers = original_request.headers
            self.query_params = original_request.query_params
            self._body = body
        
        async def body(self):
            return self._body
    
    proxy_req = ProxyRequest(request, body)
    return await proxy_request(proxy_req, target_path)

@app.post("/v1/completions")
async def completions(request: Request):
    return await proxy_request(request, "/v1/completions")

@app.get("/ping")
async def ping(request: Request):
    return await proxy_request(request, "/")

@app.get("/health")
async def health(request: Request):
    return await proxy_request(request, "/")

if __name__ == "__main__":
    import uvicorn
    print("FastAPI Proxy server started at http://127.0.0.1:8080")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        workers=1,
        access_log=False
    )
