#!/bin/bash
# Fichier: ~/ros2_ws/src/my_robot_detection/scripts/setup_yolov8.sh

# Ce script configure l'environnement pour YOLOv8 dans votre projet ROS2

set -e  # Arrêter le script en cas d'erreur

# Vérifier si le chemin de l'environnement virtuel existe
VENV_PATH="/media/msi/128873F28873D329/venvs"
if [ ! -d "$VENV_PATH" ]; then
    echo "Création du répertoire pour l'environnement virtuel..."
    mkdir -p "$VENV_PATH"
fi

# Créer l'environnement virtuel YOLOv8
echo "Création de l'environnement virtuel pour YOLOv8..."
python3 -m venv "$VENV_PATH/yolov8_env"

# Activer l'environnement virtuel
source "$VENV_PATH/yolov8_env/bin/activate"

# Installer les dépendances Python requises
echo "Installation des dépendances Python..."
pip install --upgrade pip
pip install ultralytics
pip install opencv-python
pip install numpy
pip install torch torchvision
pip install rclpy

# Créer la structure des répertoires pour le package my_robot_detection s'ils n'existent pas déjà
WORKSPACE_DIR="$HOME/ros2_ws"
PACKAGE_DIR="$WORKSPACE_DIR/src/my_robot_detection"

if [ ! -d "$PACKAGE_DIR" ]; then
    echo "Création de la structure de répertoires pour le package my_robot_detection..."
    mkdir -p "$PACKAGE_DIR/my_robot_detection"
    mkdir -p "$PACKAGE_DIR/launch"
    mkdir -p "$PACKAGE_DIR/scripts"
    mkdir -p "$PACKAGE_DIR/resource"
    mkdir -p "$PACKAGE_DIR/test"
    
    # Créer le fichier __init__.py pour que Python reconnaisse le répertoire comme un module
    touch "$PACKAGE_DIR/my_robot_detection/__init__.py"
    
    # Créer le répertoire resource et le fichier qui indique que c'est un package ROS
    echo "my_robot_detection" > "$PACKAGE_DIR/resource/my_robot_detection"
fi

# Télécharger le modèle YOLOv8
echo "Téléchargement du modèle YOLOv8..."
python "$PACKAGE_DIR/scripts/download_model.py" --model yolov8n.pt --output-dir "$PACKAGE_DIR/models"

# Définir les permissions d'exécution pour les scripts Python
echo "Définition des permissions d'exécution..."
chmod +x "$PACKAGE_DIR/my_robot_detection/yolov8_node.py"
chmod +x "$PACKAGE_DIR/scripts/download_model.py"

# Désactiver l'environnement virtuel
deactivate

echo "Configuration terminée! Vous pouvez maintenant compiler votre workspace ROS2:"
echo "cd ~/ros2_ws && colcon build --packages-select my_robot_detection"
echo ""
echo "Après la compilation, n'oubliez pas de sourcer votre installation:"
echo "source ~/ros2_ws/install/setup.bash"
echo ""
echo "Pour lancer la démonstration complète:"
echo "ros2 launch my_robot_perception integrated_navigation_launch.py"