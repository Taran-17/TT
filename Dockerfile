FROM python:3.12-slim

# Set up user with UID 1000 for Hugging Face compatibility
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy code with correct ownership
COPY --chown=user . .

# Grant permissions to write SQLite database and .env in the app directory
RUN chown -R user:user /home/user/app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose default port
EXPOSE 7860

# Start FastAPI app
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
