FROM golang:1.25-alpine AS builder

WORKDIR /src
COPY . .

ENV GOPROXY=https://goproxy.cn,direct
RUN go build -o app

FROM alpine:latest

RUN apk add --no-cache bash curl


WORKDIR /app

COPY --from=builder /src/app .
COPY --from=builder /src/start.sh ./start.bash
COPY --from=builder /src/templates ./templates

EXPOSE 8080

CMD ["bash", "/app/start.bash"]