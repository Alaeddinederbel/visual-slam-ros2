#!/usr/bin/env python3

import sys
sys.path.insert(0, '/media/msi/128873F28873D329/venvs/yolov8_env/lib/python3.10/site-packages')

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
import datetime
from collections import defaultdict, Counter
import threading

class ObjectLoggerNode(Node):
    def __init__(self):
        super().__init__('object_logger_node')
        
        # Subscriber pour les détections YOLO
        self.detection_sub = self.create_subscription(
            String,
            '/yolo/detections',
            self.detection_callback,
            10
        )
        
        # Statistiques de détection
        self.detection_stats = defaultdict(int)
        self.detection_history = []
        self.stats_lock = threading.Lock()
        
        # Chemins des fichiers
        self.log_dir = os.path.join(os.path.expanduser('~'), 'ros2_ws/src/my_robot_navigation/logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.stats_file = os.path.join(self.log_dir, 'detection_statistics.json')
        self.summary_file = os.path.join(self.log_dir, 'mission_summary.txt')
        
        # Timer pour générer des rapports périodiques
        self.report_timer = self.create_timer(30.0, self.generate_periodic_report)
        
        self.get_logger().info('Object Logger Node initialized')
    
    def detection_callback(self, msg):
        """Traite les détections reçues et met à jour les statistiques"""
        try:
            detections = json.loads(msg.data)
            
            with self.stats_lock:
                timestamp = datetime.datetime.now()
                
                for detection in detections:
                    class_name = detection['class_name']
                    confidence = detection['confidence']
                    
                    # Mettre à jour les statistiques
                    self.detection_stats[class_name] += 1
                    
                    # Ajouter à l'historique
                    self.detection_history.append({
                        'timestamp': timestamp.isoformat(),
                        'class': class_name,
                        'confidence': confidence
                    })
                
                # Limiter l'historique pour éviter l'accumulation excessive
                if len(self.detection_history) > 1000:
                    self.detection_history = self.detection_history[-800:]
            
            self.get_logger().info(f'Processed {len(detections)} detections')
            
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Erreur de décodage JSON: {e}')
        except Exception as e:
            self.get_logger().error(f'Erreur lors du traitement des détections: {e}')
    
    def generate_periodic_report(self):
        """Génère un rapport périodique des statistiques"""
        with self.stats_lock:
            if not self.detection_stats:
                return
            
            # Sauvegarder les statistiques en JSON
            stats_data = {
                'last_updated': datetime.datetime.now().isoformat(),
                'total_detections': sum(self.detection_stats.values()),
                'detection_counts': dict(self.detection_stats),
                'recent_history': self.detection_history[-50:]  # Les 50 dernières détections
            }
            
            try:
                with open(self.stats_file, 'w') as f:
                    json.dump(stats_data, f, indent=2)
                
                # Générer un résumé textuel
                self.generate_text_summary(stats_data)
                
                self.get_logger().info('Rapport périodique généré')
                
            except Exception as e:
                self.get_logger().error(f'Erreur lors de la génération du rapport: {e}')
    
    def generate_text_summary(self, stats_data):
        """Génère un résumé textuel des détections"""
        try:
            with open(self.summary_file, 'w') as f:
                f.write("RÉSUMÉ DE LA MISSION - DÉTECTION D'OBJETS\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Dernière mise à jour: {stats_data['last_updated']}\n")
                f.write(f"Total des détections: {stats_data['total_detections']}\n\n")
                
                f.write("OBJETS DÉTECTÉS PAR CATÉGORIE:\n")
                f.write("-" * 30 + "\n")
                
                # Trier par nombre de détections (ordre décroissant)
                sorted_detections = sorted(
                    stats_data['detection_counts'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                for obj_class, count in sorted_detections:
                    percentage = (count / stats_data['total_detections']) * 100
                    f.write(f"{obj_class:<15}: {count:>3} détections ({percentage:.1f}%)\n")
                
                f.write("\nDÉTECTIONS RÉCENTES:\n")
                f.write("-" * 20 + "\n")
                
                for detection in stats_data['recent_history'][-10:]:  # Les 10 dernières
                    timestamp = datetime.datetime.fromisoformat(detection['timestamp'])
                    time_str = timestamp.strftime('%H:%M:%S')
                    f.write(f"{time_str} - {detection['class']} (conf: {detection['confidence']:.2%})\n")
                
                f.write(f"\nRapport généré le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
        except Exception as e:
            self.get_logger().error(f'Erreur lors de la génération du résumé: {e}')
    
    def shutdown_handler(self):
        """Génère un rapport final avant l'arrêt"""
        self.get_logger().info('Génération du rapport final...')
        self.generate_periodic_report()
        
        # Créer un rapport final détaillé
        final_report_file = os.path.join(
            self.log_dir, 
            f'final_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        
        try:
            with open(final_report_file, 'w') as f:
                f.write("RAPPORT FINAL DE MISSION\n")
                f.write("=" * 30 + "\n\n")
                
                with self.stats_lock:
                    f.write(f"Durée de la mission: Session complète\n")
                    f.write(f"Total des objets détectés: {sum(self.detection_stats.values())}\n")
                    f.write(f"Types d'objets différents: {len(self.detection_stats)}\n\n")
                    
                    f.write("DÉTAIL PAR OBJET:\n")
                    for obj_class, count in sorted(self.detection_stats.items()):
                        f.write(f"- {obj_class}: {count} fois\n")
            
            self.get_logger().info(f'Rapport final sauvegardé: {final_report_file}')
            
        except Exception as e:
            self.get_logger().error(f'Erreur lors de la génération du rapport final: {e}')

def main(args=None):
    rclpy.init(args=args)
    
    node = ObjectLoggerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interruption détectée, arrêt en cours...')
    finally:
        node.shutdown_handler()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()