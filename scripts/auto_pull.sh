#!/bin/bash

# Charli3 Oracle Auto-Pull Automation
# This script updates the Gold and Silver price feeds on-chain every 8 minutes.

# Configuration
INTERVAL=480 # 8 minutes in seconds
CONFIG_GOLD="pull_gold.yaml"
CONFIG_SILVER="pull_silver.yaml"

# Ensure we are in the right directory
cd "$(dirname "$0")/.."

echo "==========================================="
echo "   🚀 Charli3 Oracle Auto-Pull Started"
echo "==========================================="
echo "• Gold Config:   $CONFIG_GOLD"
echo "• Silver Config: $CONFIG_SILVER"
echo "• Interval:      8 minutes ($INTERVAL seconds)"
echo "-------------------------------------------"

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$TIMESTAMP] 🟡 Starting Gold (XAU) update..."
    poetry run charli3 client send --config "$CONFIG_GOLD" --no-wait
    
    echo "[$TIMESTAMP] ⏳ Waiting 30s for mempool propagation..."
    sleep 30
    
    echo "[$TIMESTAMP] ⚪ Starting Silver (XAG) update..."
    poetry run charli3 client send --config "$CONFIG_SILVER" --no-wait
    
    echo ""
    echo "[$TIMESTAMP] ✅ Updates submitted. Sleeping for 8 minutes..."
    echo "-------------------------------------------"
    sleep $INTERVAL
done
