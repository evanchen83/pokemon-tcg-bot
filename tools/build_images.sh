#!/bin/bash

# Function to build a Docker image
build_image() {
    local image_name=$1
    local dockerfile_path=$2
    local context_path=$3

    echo "Building Docker image: $image_name"
    docker build -t $image_name -f $dockerfile_path $context_path

    # Check if the build was successful
    if [ $? -eq 0 ]; then
        echo "Successfully built $image_name"
    else
        echo "Failed to build $image_name"
        exit 1
    fi
}

# Navigate to the project root (assuming /tools is one level down)
cd "$(dirname "$0")/.." || exit 1

# Build the pokemon-tcg-bot image with the correct build context
build_image "pokemon-tcg-bot" "docker/pokemon-tcg-bot/Dockerfile" "."
# The context is set to the project root (.) to ensure pyproject.toml and poetry.lock are accessible

# Build the postgres-init image for Liquibase
build_image "postgres-init" "docker/postgres-init/Dockerfile" "docker/postgres-init"

echo "All images built successfully."
