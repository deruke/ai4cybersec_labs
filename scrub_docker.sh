#!/bin/bash
#
# scrub_docker.sh - Complete Docker cleanup script
# Removes all containers, images, volumes, and custom networks
#

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}"
echo "========================================"
echo "        DOCKER SCRUB WARNING"
echo "========================================"
echo -e "${NC}"
echo "This script will PERMANENTLY DELETE:"
echo ""
echo -e "  ${YELLOW}* All Docker containers (running and stopped)${NC}"
echo -e "  ${YELLOW}* All Docker images${NC}"
echo -e "  ${YELLOW}* All Docker volumes (INCLUDING DATA!)${NC}"
echo -e "  ${YELLOW}* All custom Docker networks${NC}"
echo ""
echo -e "${RED}This action cannot be undone!${NC}"
echo ""

# Show what will be deleted
echo "Current Docker usage:"
echo "  - Containers: $(docker ps -aq 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Images:     $(docker images -aq 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Volumes:    $(docker volume ls -q 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Networks:   $(docker network ls -q --filter type=custom 2>/dev/null | wc -l | tr -d ' ') (custom)"
echo ""

# Confirmation prompt
read -p "Are you sure you want to continue? Type 'yes' to confirm: " confirmation

if [ "$confirmation" != "yes" ]; then
    echo ""
    echo "Aborted. No changes made."
    exit 0
fi

echo ""
echo "Starting Docker cleanup..."
echo ""

# Step 1: Stop and remove containers
echo -e "${YELLOW}[1/4] Stopping and removing all containers...${NC}"
if [ -n "$(docker ps -aq 2>/dev/null)" ]; then
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm $(docker ps -aq) 2>/dev/null || true
    echo -e "${GREEN}      Containers removed${NC}"
else
    echo "      No containers to remove"
fi

# Step 2: Remove all images
echo -e "${YELLOW}[2/4] Removing all images...${NC}"
if [ -n "$(docker images -aq 2>/dev/null)" ]; then
    docker rmi $(docker images -aq) --force 2>/dev/null || true
    echo -e "${GREEN}      Images removed${NC}"
else
    echo "      No images to remove"
fi

# Step 3: Remove all volumes
echo -e "${YELLOW}[3/4] Removing all volumes...${NC}"
if [ -n "$(docker volume ls -q 2>/dev/null)" ]; then
    docker volume rm $(docker volume ls -q) 2>/dev/null || true
    echo -e "${GREEN}      Volumes removed${NC}"
else
    echo "      No volumes to remove"
fi

# Step 4: Remove custom networks
echo -e "${YELLOW}[4/4] Removing custom networks...${NC}"
if [ -n "$(docker network ls -q --filter type=custom 2>/dev/null)" ]; then
    docker network rm $(docker network ls -q --filter type=custom) 2>/dev/null || true
    echo -e "${GREEN}      Custom networks removed${NC}"
else
    echo "      No custom networks to remove"
fi

# Final cleanup with system prune
echo ""
echo -e "${YELLOW}Running final cleanup (docker system prune)...${NC}"
docker system prune -af --volumes 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================"
echo "        DOCKER SCRUB COMPLETE"
echo "========================================${NC}"
echo ""
echo "Remaining Docker resources:"
echo "  - Containers: $(docker ps -aq 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Images:     $(docker images -aq 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Volumes:    $(docker volume ls -q 2>/dev/null | wc -l | tr -d ' ')"
echo "  - Networks:   $(docker network ls -q --filter type=custom 2>/dev/null | wc -l | tr -d ' ') (custom)"
echo ""
echo "Docker is now clean. You can rebuild with:"
echo "  ./setup.sh --all --non-interactive"
echo ""
