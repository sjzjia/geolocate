# 使用官方的 Python 基础镜像
FROM python:3.9-slim-buster
# 系统更新
RUN apt update -y

# 安装wget下载工具
RUN apt install -y wget

# 设置工作目录
WORKDIR /app

# 拷贝依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝应用代码和模板
COPY app.py .
COPY templates/ templates/

# 下载GeoLite2文件
RUN wget -P /app https://git.io/GeoLite2-Country.mmdb
RUN wget -P /app https://git.io/GeoLite2-ASN.mmdb
RUN wget -P /app https://git.io/GeoLite2-City.mmdb

# 暴露 Flask 默认端口
EXPOSE 80

# 定义容器启动命令
CMD ["python", "app.py"]
