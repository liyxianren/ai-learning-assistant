# 使用 Nginx Alpine 轻量级镜像
FROM nginx:alpine

# 复制静态文件到 Nginx 默认目录
COPY . /usr/share/nginx/html

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口 (Zeabur 会自动识别)
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
