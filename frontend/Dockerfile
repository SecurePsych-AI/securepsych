FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci

COPY . .
# VITE_API_BASE_URL is baked into the JS bundle at build time.
# For LAN deployment (users on different machines), override with the server IP:
#   docker-compose build --build-arg VITE_API_BASE_URL=http://192.168.1.50:8000 frontend
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
