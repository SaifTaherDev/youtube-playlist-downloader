FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-privileged user to run the app (Security Best Practice)
RUN useradd -u 6769 appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /home/appuser/.cache/selenium \
    && chown -R appuser:appuser /home/appuser

USER appuser

EXPOSE 5000
CMD ["python", "main.py"]

# Useful for debugging:

# docker run --rm -it your-image-name /bin/bash

# docker run — start a new container
# --rm — automatically delete the container when you exit it (keeps things tidy)
# -i — interactive mode, keeps stdin open so you can type commands
# -t — allocates a terminal so the shell looks and behaves normally
# -it — these two are almost always combined together
# your-image-name — the name of the image to run (replace with your actual image name)
# /bin/bash — instead of running the default command (python main.py), open a bash shell instead

# ls -la /usr/bin/chromium

# ls — list files
# -l — long format, shows permissions, owner, size, date
# -a — show hidden files too (files starting with .)
# -la — combined, same as -l -a
# /usr/bin/chromium — the specific path to inspect, rather than listing a whole directory

# python --version        # confirm Python
# pip list                # confirm your packages installed
# which chromium          # confirm chromium is at /usr/bin/chromium
# which chromedriver      # confirm chromium is at /usr/bin/chromedriver
# chromium --version      # confirm chromium works
# chromedriver --version  # confirm chromedriver works

# When building docker image with a name:
# docker build -t my-image-name:v1 .