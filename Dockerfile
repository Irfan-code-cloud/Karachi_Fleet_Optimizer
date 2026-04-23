# 1. Use an official, lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (this makes future builds much faster)
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your app's code into the container
COPY . .

# 6. Expose Port 8080 (This is the specific port Google Cloud Run looks for)
EXPOSE 8080

# 7. The command to launch your Streamlit app on the correct port
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]