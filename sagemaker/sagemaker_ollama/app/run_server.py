#!/usr/bin/env python3
"""
FastAPI高并发代理服务器启动脚本
"""
import uvicorn
import multiprocessing

if __name__ == '__main__':
    # 获取CPU核心数
    cpu_count = multiprocessing.cpu_count()
    worker_count = min(cpu_count, 4)  # 限制最大进程数
    
    print(f"Starting FastAPI server with {worker_count} workers...")
    
    # 使用uvicorn启动，自动支持高并发
    uvicorn.run(
        "proxy:app",
        host="0.0.0.0",
        port=8080,
        workers=worker_count,
        access_log=False,
        loop="uvloop"
    )