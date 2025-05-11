#!/bin/bash

CONFIG_PATH="/data/homeserver.yaml"
REG_LINE="  - /data/registration.yaml"

echo "[AutonomousSphere] Checking for registration file reference..."

# If the app_service_config_files block is missing, add it
if ! grep -q "app_service_config_files:" "$CONFIG_PATH"; then
  echo "[AutonomousSphere] Adding app_service_config_files block..."
  echo -e "\napp_service_config_files:\n$REG_LINE" >> "$CONFIG_PATH"
else
  # Check if our registration file is already listed
  if ! grep -q "$REG_LINE" "$CONFIG_PATH"; then
    echo "[AutonomousSphere] Adding registration.yaml to config..."
    sed -i "/app_service_config_files:/a\\$REG_LINE" "$CONFIG_PATH"
  else
    echo "[AutonomousSphere] Registration file already listed."
  fi
fi

# Hand off to Synapse
exec python -m synapse.app.homeserver \
  --config-path "$CONFIG_PATH"
