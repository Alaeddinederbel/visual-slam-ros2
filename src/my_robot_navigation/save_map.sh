#!/bin/bash

# Script pour sauvegarder manuellement la carte RTABMap
# Usage: ./save_map.sh [nom_de_carte]

# Configuration
MAP_DIR="$HOME/robot_maps"
DEFAULT_MAP_NAME="rtabmap_map_$(date +%Y%m%d_%H%M%S)"

# Créer le répertoire s'il n'existe pas
mkdir -p "$MAP_DIR"

# Nom de la carte
MAP_NAME="${1:-$DEFAULT_MAP_NAME}"
MAP_PATH="$MAP_DIR/$MAP_NAME"

echo "Sauvegarde de la carte en cours..."
echo "Répertoire: $MAP_DIR"
echo "Nom de fichier: $MAP_NAME"

# Méthode 1: Utiliser map_saver_cli de Nav2
echo "Méthode 1: Sauvegarde avec Nav2 map_saver..."
ros2 run nav2_map_server map_saver_cli -f "$MAP_PATH" --ros-args --log-level info

if [ $? -eq 0 ]; then
    echo "✓ Carte sauvegardée avec succès: $MAP_PATH.yaml et $MAP_PATH.pgm"
    
    # Copier comme carte par défaut
    cp "$MAP_PATH.yaml" "$MAP_DIR/map.yaml"
    cp "$MAP_PATH.pgm" "$MAP_DIR/map.pgm"
    echo "✓ Carte par défaut mise à jour"
    
    # Afficher les informations de la carte
    echo ""
    echo "Informations de la carte:"
    echo "------------------------"
    head -10 "$MAP_PATH.yaml"
    
else
    echo "✗ Échec de la sauvegarde avec Nav2"
    
    # Méthode 2: Essayer d'exporter directement depuis RTABMap
    echo "Méthode 2: Export depuis RTABMap..."
    
    # Appeler le service RTABMap pour obtenir la carte
    echo "Appel du service RTABMap get_map..."
    ros2 service call /rtabmap/get_map rtabmap_msgs/srv/GetMap "{global_map: true, optimized: true, graph_only: false}"
    
    # Attendre un peu et essayer de sauvegarder à nouveau
    sleep 2
    ros2 run nav2_map_server map_saver_cli -f "$MAP_PATH" --ros-args --log-level info
    
    if [ $? -eq 0 ]; then
        echo "✓ Carte sauvegardée avec RTABMap export"
    else
        echo "✗ Impossible de sauvegarder la carte"
        exit 1
    fi
fi

# Méthode 3: Sauvegarder aussi la base de données RTABMap
echo ""
echo "Sauvegarde de la base de données RTABMap..."
RTABMAP_DB_PATH="$HOME/.ros/rtabmap.db"
if [ -f "$RTABMAP_DB_PATH" ]; then
    cp "$RTABMAP_DB_PATH" "$MAP_DIR/${MAP_NAME}_rtabmap.db"
    echo "✓ Base de données RTABMap sauvegardée: ${MAP_NAME}_rtabmap.db"
else
    echo "! Base de données RTABMap non trouvée à $RTABMAP_DB_PATH"
fi

# Créer un fichier de métadonnées
echo ""
echo "Création des métadonnées..."
cat > "$MAP_PATH"_info.txt << EOF
Carte RTABMap générée le: $(date)
Nom: $MAP_NAME
Répertoire: $MAP_DIR

Fichiers générés:
- ${MAP_NAME}.yaml (configuration de la carte)
- ${MAP_NAME}.pgm (image de la carte)
- ${MAP_NAME}_rtabmap.db (base de données RTABMap)
- ${MAP_NAME}_info.txt (ce fichier)

Pour utiliser cette carte avec Nav2:
ros2 launch nav2_bringup navigation_launch.py map:=$MAP_PATH.yaml

EOF

echo "✓ Métadonnées créées: ${MAP_PATH}_info.txt"

echo ""
echo "==================================="
echo "Sauvegarde terminée avec succès!"
echo "Fichiers dans: $MAP_DIR"
echo "Nom de base: $MAP_NAME"
echo "==================================="

# Lister les fichiers créés
echo ""
echo "Fichiers créés:"
ls -la "$MAP_DIR"/${MAP_NAME}*
