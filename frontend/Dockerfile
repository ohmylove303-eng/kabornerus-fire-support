# 카번개루스 프론트엔드 Dockerfile
# Stage 1: 빌드
FROM node:20-alpine AS builder

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:8000
ARG REACT_APP_CESIUM_ION_TOKEN=

ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_CESIUM_ION_TOKEN=$REACT_APP_CESIUM_ION_TOKEN

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# Stage 2: Nginx 서빙
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
