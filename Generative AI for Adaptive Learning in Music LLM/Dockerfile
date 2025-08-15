FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    fluidsynth \
    libsndfile1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Download soundfonts
RUN mkdir -p /app/soundfonts && \
    wget -O /app/soundfonts/Trumpet.sf2 https://github.com/FluidSynth/fluidsynth/raw/master/sf2/Trumpet.sf2 && \
    wget -O /app/soundfonts/Piano.sf2 https://musical-artifacts.com/artifacts/2719/GeneralUser_GS_1.471.sf2 && \
    wget -O /app/soundfonts/Violin.sf2 https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2 && \
    wget -O /app/soundfonts/Clarinet.sf2 https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2 && \
    wget -O /app/soundfonts/Flute.sf2 https://musical-artifacts.com/artifacts/2744/SalC5Light.sf2

# Create static directory for audio files
RUN mkdir -p /app/static

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]