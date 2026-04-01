#!/usr/bin/env python3
# Fichier: ~/ros2_ws/src/my_robot_detection/scripts/download_model.py

import os
import sys
import argparse

# Ajouter le chemin de l'environnement virtuel pour importer ultralytics
venv_path = '/media/msi/128873F28873D329/venvs/yolov8_env/lib/python3.10/site-packages'
if venv_path not in sys.path:
    sys.path.append(venv_path)

from ultralytics import YOLO

def download_model(model_name='yolov8n.pt', output_dir=None):
    """
    Télécharge un modèle YOLOv8 pré-entraîné.
    
    Args:
        model_name: Nom du modèle YOLOv8 à télécharger ('yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt')
        output_dir: Répertoire de sortie pour le modèle (si None, utilise le répertoire par défaut)
    """
    print(f"Téléchargement du modèle YOLOv8 {model_name}...")
    
    try:
        # Charger le modèle (YOLO le téléchargera automatiquement s'il n'existe pas)
        model = YOLO(model_name)
        
        # Si un répertoire de sortie est spécifié, copier le modèle
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, model_name)
            # Le modèle est déjà téléchargé dans le cache ~/.cache/ultralytics ou chargé localement
            # Le sauvegarder dans le répertoire spécifié
            print(f"Sauvegarde du modèle dans {output_path}")
            model.export(format="pt", imgsz=640)
            
        print(f"Modèle YOLOv8 {model_name} téléchargé avec succès.")
    except Exception as e:
        print(f"Erreur lors du téléchargement du modèle: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharger un modèle YOLOv8 pré-entraîné")
    parser.add_argument('--model', type=str, default='yolov8n.pt', 
                        help='Nom du modèle (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)')
    parser.add_argument('--output-dir', type=str, default=None, 
                        help='Répertoire de sortie pour le modèle')
    
    args = parser.parse_args()
    download_model(args.model, args.output_dir)