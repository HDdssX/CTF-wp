FROM node:18-bullseye

WORKDIR /app

# Install system dependencies required by headless Chrome (Puppeteer)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ca-certificates \
		fonts-liberation \
		libasound2 \
		libatk-bridge2.0-0 \
		libatk1.0-0 \
		libc6 \
		libcairo2 \
		libcups2 \
		libdbus-1-3 \
		libexpat1 \
		libfontconfig1 \
		libgcc1 \
		libglib2.0-0 \
		libgbm1 \
		libnss3 \
		libnspr4 \
		libdrm2 \
		libxkbcommon0 \
		libxcomposite1 \
		libxdamage1 \
		libxfixes3 \
		libxrandr2 \
		libx11-6 \
		libx11-xcb1 \
		libxcb1 \
		libxext6 \
		libxss1 \
		libxtst6 \
		wget \
		xdg-utils \
	&& rm -rf /var/lib/apt/lists/*

# Copy dependency manifests and tsconfig first
COPY package*.json tsconfig.json ./

# Install all dependencies (including dev) so we can build TypeScript and run puppeteer
RUN npm install

# Now copy source code and public assets
COPY src ./src
COPY public ./public

# Build TypeScript and then prune devDependencies for smaller runtime image
RUN npm run build \
	&& npm prune --production

ENV PORT=3000

EXPOSE 3000

CMD ["npm", "start"]
