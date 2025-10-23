# Docker Compose Installation Guide

## Quick Install

### Ubuntu/Debian
```bash
# Install Docker Compose plugin (recommended)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker compose version
```

### Alternative: Standalone Docker Compose
```bash
# Download latest version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

## After Installation

Once Docker Compose is installed, run:
```bash
./run_complete_system.sh
```

## Troubleshooting

### Permission Denied
If you get permission errors:
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, then test
docker ps
```

### Command Not Found
If `docker compose` command is not found:
```bash
# Check Docker installation
docker --version

# Install Docker if needed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## More Information
- Official Docker Compose docs: https://docs.docker.com/compose/install/
- Docker installation: https://docs.docker.com/engine/install/
