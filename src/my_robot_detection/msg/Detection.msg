# Fichier: ros2_ws/src/my_robot_detection/msg/Detection.msg
# Ce message représente une détection individuelle par YOLOv8

int32 id                  # ID de la détection
string class_name         # Nom de la classe détectée
int32 class_id            # ID de la classe détectée
float32 confidence        # Confiance de la détection (0-1)

# Coordonnées de la boîte englobante dans l'image
float32 x_min             # Coin supérieur gauche x
float32 y_min             # Coin supérieur gauche y 
float32 x_max             # Coin inférieur droit x
float32 y_max             # Coin inférieur droit y

# Centre estimé de l'objet
float32 x_center          # Centre x de la boîte
float32 y_center          # Centre y de la boîte

# Information de profondeur (si disponible)
float32 depth             # Profondeur estimée en mètres

