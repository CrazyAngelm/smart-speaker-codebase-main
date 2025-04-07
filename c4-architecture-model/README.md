# Structurizr Lite Docker Setup
This guide explains how to run Structurizr Lite using Docker, which allows to visualize and edit C4 model diagrams locally.

## Prerequisites
Before running Structurizr Lite in Docker, ensure the following:

- Docker is installed and running on your system.
- You have a C4 model defined in Structurizr DSL format (workspace.dsl).

## Steps to Run Structurizr Lite Docker Image
### 1. Pull the Structurizr Lite Docker Image
Pull the official Structurizr Lite Docker image from Docker Hub:

```bash
docker pull structurizr/lite
```
### 2. Run Structurizr Lite Docker Container
After pulling the image, run it as follows:

```bash
docker run -it --rm -p 8080:8080 -v $(pwd):/usr/local/structurizr structurizr/lite
```

If you're using Windows, replace $(pwd) with your full directory path, like:

```powershell
docker run -it --rm -p 8080:8080 -v C:\path\to\your\workspace\smart-speaker-codebase\c4-architecture-model:/usr/local/structurizr structurizr/lite
```

### 3. Access Structurizr Lite in Your Browser
Once the container is running, open your web browser and go to:

```
http://localhost:8080
```
This will load the Structurizr Lite UI, where you can view and edit C4 model.