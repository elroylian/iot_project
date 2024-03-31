# Use a base image with Python and an operating system
FROM python:3

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install any necessary dependencies from requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your Flask application will run on (default is 5000)
EXPOSE 5000

# Define the command to run your Flask application
CMD ["python3", "app.py"]