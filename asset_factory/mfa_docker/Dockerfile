FROM continuumio/miniconda3:22.11.1

# 设置工作目录
WORKDIR /app

# 1. 补充底层编译依赖 (build-essential)，防止某些 pip 包现场编译时报错
RUN apt-get update && apt-get install -y ffmpeg curl wget build-essential && apt-get clean

# 2. 彻底接管 Conda 源，强制使用清华源，并移除极慢的 defaults 源
RUN conda config --remove channels defaults || true && \
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/ && \
    conda config --set show_channel_urls yes

# 3. 基础 Python 环境 + 安装 mamba (C++ 重写的极速包管理器，拯救 OOM)
RUN conda install python=3.9 pip mamba -n base -c conda-forge -y

# 4. 【核心修复】使用官方源强装 MFA，绕过清华源的 404 缺失问题！
RUN mamba install -c conda-forge montreal-forced-aligner=2.2.17 -y --override-channels

# 5. 安装纯 Python 依赖 (给 pip 也加上清华源加速)
RUN pip install joblib==1.2.0 pgvector textgrid fastapi uvicorn python-multipart \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 确保MFA目录存在
RUN mkdir -p /root/Documents/MFA/
ENV MFA_ROOT=/root/Documents/MFA/

# 6. 【核心修复】使用最新的官方模型名称：mandarin_mfa 和 mandarin_pinyin
RUN for i in 1 2 3; do \
        mfa model download acoustic mandarin_mfa && break || \
        (echo "Acoustic model failed, retrying in 5s..." && sleep 5); \
    done && \
    for i in 1 2 3; do \
        mfa model download dictionary mandarin_pinyin && break || \
        (echo "Dictionary failed, retrying in 5s..." && sleep 5); \
    done

# 把本地的微服务代码复制进容器
COPY server.py /app/server.py

# 暴露给宿主机调用的端口
EXPOSE 8000

# 启动微服务
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]