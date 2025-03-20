ARG VLLM_REPO
ARG VLLM_VERSION
FROM $VLLM_REPO:$VLLM_VERSION

# 设置工作目录
WORKDIR /app

# 复制当前目录下的内容到容器内的/app
COPY app/ /app

# 修改restapi
RUN \
python3 -m pip install s5cmd sagemaker-ssh-helper requests boto3 --no-cache-dir; \
chmod +x /app/serve

# 让端口8080在容器外可用
EXPOSE 8080

# 定义环境变量
ENV PATH="/app:${PATH}"

# 运行serve
ENTRYPOINT []
CMD ["serve"]

