FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory
WORKDIR /app

# Install only essential packages
RUN apt-get update && \
    apt-get install -y \
    python3-venv \
    procps \
    supervisor && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Make the startup script executable
COPY all_commands.sh /app/all_commands.sh
RUN chmod +x /app/all_commands.sh

# Expose Django port
EXPOSE 8001

# Run the startup script
CMD ["/app/all_commands.sh"]
