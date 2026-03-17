# Phase 5: Frontend Dockerfile (dev mode)
# Runs Vite dev server with proxy to backend
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# VITE_API_BACKEND is set by docker-compose to proxy /api to backend
CMD ["npm", "run", "dev"]
