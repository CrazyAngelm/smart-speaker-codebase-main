# Set profile directory
PROFILE_DIR="$HOME/.config/rhasspy/profiles"

#Create profile directory
mkdir -p $PROFILE_DIR

# Copy profile
cp -r ./profiles/ru $PROFILE_DIR

# Up docker containers
docker compose -f docker-compose.yaml up -d
