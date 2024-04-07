# Use the official Python image from Docker Hub
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Expose port 5000 for Flask
EXPOSE 5000

# Command to run the Flask application
CMD ["python3","-m","flask", "run", "--host","0.0.0.0"]
# CMD ["flask", "run", "--host","0.0.0.0"]