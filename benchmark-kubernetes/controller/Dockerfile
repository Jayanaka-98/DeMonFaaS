# Build stage
FROM golang:1.22-alpine AS builder

# Install necessary build tools
RUN apk add --no-cache git gcc musl-dev

# Set working directory
WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build the application with CGO enabled for certain dependencies
RUN CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build -o /api-routing-controller \
    -ldflags="-w -s" \
    -a -installsuffix cgo .

# Final stage
FROM alpine:3.19

# Install necessary runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy the binary from builder
COPY --from=builder /api-routing-controller .

# Set ownership
RUN chown -R appuser:appgroup /app

# Create necessary directories for controller-runtime
RUN mkdir -p /tmp/k8s-webhook-server/serving-certs && \
    chown -R appuser:appgroup /tmp/k8s-webhook-server

# Switch to non-root user
USER appuser

# Expose port for HTTP server
EXPOSE 8080

# Run the application
ENTRYPOINT ["./api-routing-controller"]