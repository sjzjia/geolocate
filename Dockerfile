# 使用官方的 Python 基础镜像
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 拷贝依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝应用代码和模板
COPY app.py .
COPY templates/ templates/

# 拷贝 GeoLite2-Country.mmdb 文件
# 直接拷贝到容器内，如果文件非常大，可以考虑通过 Docker Volume 挂载
COPY GeoLite2-Country.mmdb .
COPY GeoLite2-ASN.mmdb .
COPY GeoLite2-City.mmdb .

# 暴露 Flask 默认端口
EXPOSE 80

# 定义容器启动命令
CMD ["python", "app.py"]
