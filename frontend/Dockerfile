FROM node:18 AS builder
WORKDIR /app
COPY package.json package-lock.json ./
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=http://localhost:8015
RUN npm install
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
