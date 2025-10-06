FROM node:20-alpine

WORKDIR /app

# Install deps separately for better caching
COPY package.json package-lock.json* yarn.lock* ./
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    else npm ci; fi

COPY . .

RUN npm run build || yarn build || true

EXPOSE 3000
CMD ["sh", "-lc", "yarn start -p 3000 || npm run start -- -p 3000"]


