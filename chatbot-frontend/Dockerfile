FROM node:24-alpine AS builder

# Set/create working directory inside the container
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy rest of frontend files and build
COPY . .
RUN npm run build -- --configuration production

FROM nginx:alpine

# Copy built static files from the builder stage into Nginx's public folder
COPY --from=builder /app/dist/chatbot-frontend/browser /usr/share/nginx/html

# Expose port 80 for web traffic
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
