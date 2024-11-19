# Stage 1: Build the Go binary
FROM golang:1.23 AS builder

# Set the working directory
WORKDIR /app

# Copy the Go module files first to leverage Docker caching
COPY go.mod go.sum ./
RUN go mod tidy && go mod download

# Copy the rest of the application source code
COPY . .

# Build the Go application
RUN CGO_ENABLED=0 GOOS=linux go build -o controller .

# Stage 2: Create the final runtime image
FROM gcr.io/distroless/static:nonroot

# Set the working directory inside the container
WORKDIR /

# Copy the Go binary from the builder stage
COPY --from=builder /app/controller .

# Specify a non-root user for security
USER nonroot:nonroot

# Set the entry point for the container
ENTRYPOINT ["/controller"]
