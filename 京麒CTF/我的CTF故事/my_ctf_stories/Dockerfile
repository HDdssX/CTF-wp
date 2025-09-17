FROM node:18-alpine AS builder
WORKDIR /my_ctf_stories
COPY package*.json ./
RUN npm install                          
COPY .storybook .storybook
COPY src ./src
RUN npm run build-storybook        

FROM node:18-alpine AS runtime      
WORKDIR /my_ctf_stories
COPY package*.json ./
RUN npm install --production              

COPY --from=builder /my_ctf_stories/storybook-static ./storybook-static  
COPY server.js ./server.js

EXPOSE 80

CMD ["node", "server.js"]
