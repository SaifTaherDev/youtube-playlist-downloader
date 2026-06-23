<div align="center">
  <h1>youtube-playlist-downloader</h1>
  <p>Effortlessly download entire YouTube playlists locally, ensuring offline access to your favorite content.</p>
  
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge&logo=github)](https://github.com/your-username/youtube-playlist-downloader/actions)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)
</div>

---

## Overview

Many users struggle with unreliable online downloaders, lost content due to platform changes, or the inability to access their favorite YouTube playlists offline. Traditional methods can be cumbersome, slow, and often lead to incomplete downloads or corrupted files, leaving users frustrated and their content inaccessible when needed most.

The `youtube-playlist-downloader` project provides a robust, containerized Python solution to reliably download all videos from any YouTube playlist directly to your local server. By leveraging a battle-tested scraping service and Docker, it offers a secure, efficient, and self-hosted method for preserving your digital media library, ensuring continuous offline access and complete control over your downloaded content. This solution empowers users to curate their own media archives, independent of internet connectivity or platform availability.

## Key Features

*   ⬇️ **Seamless Playlist Downloads**: Download all videos from a specified YouTube playlist with a single, straightforward command.
*   🔒 **Self-Hosted & Private**: Run the application entirely on your local network, maintaining full control over your data and downloaded content.
*   🐳 **Dockerized Deployment**: Enjoy easy setup, isolated execution, and consistent performance across various Linux server environments thanks to Docker containerization.
*   🚀 **High Reliability**: Leverages the robust `app.ytdown.to/en27/` service for consistent and effective video scraping and downloading.
*   💻 **Server-Optimized**: Engineered to run efficiently from a Linux server on your local network, ideal for long-term media archiving.
*   ✨ **Automated Content Preservation**: Effortlessly build and maintain a local archive of your favorite YouTube content, safeguarding it against platform changes or internet outages.

## Technical Architecture

The `youtube-playlist-downloader` is built on a lean yet powerful stack designed for efficiency and reliability in a self-hosted environment.

### Tech Stack

| Technology               | Purpose                                      | Key Benefit                                     |
| :----------------------- | :------------------------------------------- | :---------------------------------------------- |
| **Python**               | Core application logic and orchestration     | Rapid development, extensive libraries, readability |
| **Docker**               | Application containerization                 | Isolated, consistent, and portable execution    |
| **`app.ytdown.to/en27/`** | External scraping and download service       | Reliable and robust video content acquisition   |
| **Linux Server**         | Primary deployment and execution environment | Stability, performance, and control             |

### Directory Structure

```
.
├── 📁 .vscode/                  # VS Code configuration files
├── 📁 playlist_downloads/       # Default directory for downloaded videos
├── 📁 zip/                     # Temporary directory for zipped downloads (if applicable)
├── 📄 .gitignore               # Specifies intentionally untracked files to ignore
├── 📄 .python-version          # Specifies Python version for pyenv/asdf
├── 📄 README.md                # Project documentation
├── 📄 dockerfile               # Docker image definition
├── 📄 main.py                  # Main application script
├── 📄 pyproject.toml           # Project metadata and build system configuration
├── 📄 requirements.txt         # Python package dependencies
└── 📄 uv.lock                  # Lock file for uv dependency manager
```

## Operational Setup

### Prerequisites

To run this application, you will need:

*   **Docker**: For containerized deployment (recommended for server environments).
*   **Python 3.x**: For local development or direct execution without Docker.

### Installation (Docker - Recommended)

For the most robust and consistent deployment on your Linux server, Docker is the recommended approach.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/youtube-playlist-downloader.git
    cd youtube-playlist-downloader
    ```

2.  **Build the Docker Image**:
    ```bash
    docker build -t youtube-downloader .
    ```

3.  **Run the Docker Container**:
    Execute the container, mounting the `playlist_downloads` directory to persist your downloaded videos outside the container.
    ```bash
    docker run -v "$(pwd)/playlist_downloads:/app/playlist_downloads" youtube-downloader python main.py
    ```
    *Once the app is running, it is constantly listening for POST requests. Make a POST request containing the URL of the playlist from anywhere on your local network to download the playlist.*

### Installation (Local Python Environment - For Development)

If you prefer to run the application directly or contribute to its development, follow these steps to set up a local Python environment.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/youtube-playlist-downloader.git
    cd youtube-playlist-downloader
    ```

2.  **Create and Activate a Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    Using `uv` (as indicated by `uv.lock`) or `pip`:
    ```bash
    # If uv is installed:
    uv sync
    # Otherwise, using pip:
    pip install -r requirements.txt
    ```

### Usage

Once installed, you can run the `main.py` script to download a YouTube playlist. Just make a POST request containing the URL of the playlist from a device your local network.

```bash
# From within the activated virtual environment (local setup)
python main.py

# Or via Docker (server setup)
docker run -v "$(pwd)/playlist_downloads:/app/playlist_downloads" youtube-downloader python main.py
```
