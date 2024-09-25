# Filament Manager

A terminal application for managing 3D printer filaments using Textual, Poetry, and Docker.

## Features

- Add new filaments to inventory
- View existing filament inventory
- Persistent storage using JSON (can be replaced with a database)

## Requirements

- Docker
- (For local development) Python 3.9 or higher
- (For local development) Poetry

## Running with Docker

```bash
docker build -t filament-manager .
docker run -it --rm filament-manager

