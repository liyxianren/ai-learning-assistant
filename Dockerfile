FROM nginx:alpine

# 复制前端静态文件
COPY frontend/ /usr/share/nginx/html

# 保持模板机制以支持 BACKEND_URL 环境变量替换
COPY nginx.conf /etc/nginx/templates/default.conf.template

# 默认后端地址，可在运行时覆盖
ENV BACKEND_URL=http://localhost:3000

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
