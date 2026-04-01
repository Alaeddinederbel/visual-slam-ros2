#!/bin/bash

# Script pour sauvegarder la carte générée par RTAB-Map
# Usage: ./save_map.sh [nom_de_la_carte]

# Répertoire de sauvegarde
MAP_DIR="$HOME/ros2_ws/src/my_robot_navigation/maps"

# Nom de la carte (par défaut: my_map avec timestamp)
if [ -z "$1" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    MAP_NAME="map_$TIMESTAMP"
else
    MAP_NAME="$1"
fi

# Créer le répertoire s'il n'existe pas
mkdir -p "$MAP_DIR"

echo "Sauvegarde de la carte en cours..."
echo "Nom de la carte: $MAP_NAME"
echo "Répertoire: $MAP_DIR"

# Sauvegarder la carte avec map_saver_cli
cd "$MAP_DIR"
ros2 run nav2_map_server map_saver_cli -f "$MAP_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Carte sauvegardée avec succès!"
    echo "Fichiers créés:"
    echo "  - $MAP_DIR/$MAP_NAME.yaml"
    echo "  - $MAP_DIR/$MAP_NAME.pgm"
    
    # Créer un lien symbolique vers la dernière carte
    ln -sf "$MAP_NAME.yaml" "$MAP_DIR/latest_map.yaml"
    echo "  - Lien symbolique: $MAP_DIR/latest_map.yaml -> $MAP_NAME.yaml"
else
    echo "❌ Erreur lors de la sauvegarde de la carte"
    exit 1
fi

echo ""
echo "Pour utiliser cette carte en navigation:"
echo "ros2 launch my_robot_navigation navigation_phase.launch.py map:=$MAP_DIR/$MAP_NAME.yaml"