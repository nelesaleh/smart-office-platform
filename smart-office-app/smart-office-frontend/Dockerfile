# --- Stage 1: Build ---
FROM node:20-alpine as builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine
# نسخ ملفات البناء من المرحلة الأولى
COPY --from=builder /app/dist /usr/share/nginx/html
# نسخ إعدادات Nginx الخاصة بنا
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]