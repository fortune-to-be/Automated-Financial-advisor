# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent

# Copy source and build
COPY frontend/ ./
RUN npm run build --silent

# Production stage: serve with nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx conf if provided (optional)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
