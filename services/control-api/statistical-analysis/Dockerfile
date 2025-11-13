FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the statistical engine code
COPY statistical_engine.py .
COPY __init__.py .

# Create __tests__ directory but don't copy tests (they're for development)
RUN mkdir -p __tests__

# Health check
RUN echo '#!/bin/bash\npython3 -c "import statistical_engine; print(\"Statistical Engine OK\")"' > /healthcheck.sh && chmod +x /healthcheck.sh
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD ["/healthcheck.sh"]

# Expose no ports (this is a library service used by other services)
CMD ["python3", "-c", "print('Statistical Analysis Engine Ready')"]