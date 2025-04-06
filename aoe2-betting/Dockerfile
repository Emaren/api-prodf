# Frontend Dockerfile for Next.js
FROM node:18-alpine

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

EXPOSE 3000

# 👇 Default to production, but allow overriding
ENV NODE_ENV=production

CMD ["sh", "-c", "if [ \"$NODE_ENV\" = 'development' ]; then npm run dev; else npm start; fi"]
