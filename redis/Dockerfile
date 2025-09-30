FROM redis:7-alpine

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Create Redis data directory
RUN mkdir -p /data && chown redis:redis /data

# Set working directory
WORKDIR /data

# Expose Redis port
EXPOSE 6379

# Use custom configuration file
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]