#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <deque>
#include <vector>
#include <algorithm>
#include <cmath>

class PoseTransformer : public rclcpp::Node
{
public:
    PoseTransformer() : Node("pose_transformer")
    {
        // Subscriber pour ORB-SLAM3 camera pose
        orb_pose_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
            "/orb_slam3/camera_pose", 10,
            std::bind(&PoseTransformer::orbPoseCallback, this, std::placeholders::_1));

        // Publisher pour la pose robot (pour monitoring uniquement)
        robot_pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("/robot_pose", 10);

        // Service pour relocalisation manuelle
        relocalize_service_ = this->create_service<std_srvs::srv::Trigger>(
            "relocalize_robot",
            std::bind(&PoseTransformer::relocalizeCallback, this,
                     std::placeholders::_1, std::placeholders::_2));

        // TF Components
        tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
        tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

        // Paramètres de transformation camera -> base_footprint
        this->declare_parameter("left_camera_to_base_x", 0.15);
        this->declare_parameter("left_camera_to_base_y", 0.0);
        this->declare_parameter("left_camera_to_base_z", 0.30);
        
        // CORRECTION: Paramètres TF optimisés pour éviter les conflits
        this->declare_parameter("tf_publish_rate", 30.0);  // Fréquence modérée
        this->declare_parameter("tf_timeout", 0.2);        // Timeout plus long
        this->declare_parameter("transform_tolerance", 0.1); // Tolérance augmentée
        this->declare_parameter("tf_future_dating", 0.1);  // NOUVEAU: projection future
        
        // Paramètres de filtrage optimisés
        this->declare_parameter("smoothing_alpha", 0.8);   // Plus lisse pour éviter les oscillations
        this->declare_parameter("min_pose_change_threshold", 0.02);
        this->declare_parameter("min_angle_change_threshold", 0.02);
        this->declare_parameter("max_velocity_threshold", 3.0);
        this->declare_parameter("pose_buffer_size", 5);
        this->declare_parameter("min_tracking_confidence", 0.7);
        this->declare_parameter("publish_frequency", 20.0);

        // Chargement des paramètres
        camera_to_base_x_ = this->get_parameter("left_camera_to_base_x").as_double();
        camera_to_base_y_ = this->get_parameter("left_camera_to_base_y").as_double();
        camera_to_base_z_ = this->get_parameter("left_camera_to_base_z").as_double();
        
        tf_publish_rate_ = this->get_parameter("tf_publish_rate").as_double();
        tf_timeout_ = this->get_parameter("tf_timeout").as_double();
        transform_tolerance_ = this->get_parameter("transform_tolerance").as_double();
        tf_future_dating_ = this->get_parameter("tf_future_dating").as_double();
        
        smoothing_alpha_ = this->get_parameter("smoothing_alpha").as_double();
        min_pose_change_ = this->get_parameter("min_pose_change_threshold").as_double();
        min_angle_change_ = this->get_parameter("min_angle_change_threshold").as_double();
        max_velocity_ = this->get_parameter("max_velocity_threshold").as_double();
        pose_buffer_size_ = this->get_parameter("pose_buffer_size").as_int();
        min_tracking_confidence_ = this->get_parameter("min_tracking_confidence").as_double();
        publish_frequency_ = this->get_parameter("publish_frequency").as_double();

        // Initialisation des variables d'état
        base_footprint_height_ = 0.0;
        pose_initialized_ = false;
        pose_available_ = false;
        first_valid_pose_received_ = false;
        pose_history_.clear();
        last_update_time_ = this->get_clock()->now();
        last_published_time_ = this->get_clock()->now();
        map_to_odom_initialized_ = false;

        // CORRECTION: Timer avec gestion des conflits TF
        int timer_period_ms = static_cast<int>(1000.0 / tf_publish_rate_);
        transform_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(timer_period_ms),
            std::bind(&PoseTransformer::publishTransforms, this));

        // NOUVEAU: Timer pour synchronisation avec Gazebo
        sync_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100), // 10Hz
            std::bind(&PoseTransformer::syncWithGazebo, this));

        RCLCPP_INFO(this->get_logger(), "=== Visual SLAM Pose Transformer Started (CORRECTED) ===");
        RCLCPP_INFO(this->get_logger(), "Mode TF: map_to_odom SYNCHRONISÉ avec Gazebo");
        RCLCPP_INFO(this->get_logger(), "TF Rate: %.1f Hz, Timeout: %.3f s", tf_publish_rate_, tf_timeout_);
        RCLCPP_INFO(this->get_logger(), "Camera offset: x=%.3f, y=%.3f, z=%.3f", 
                   camera_to_base_x_, camera_to_base_y_, camera_to_base_z_);
        RCLCPP_INFO(this->get_logger(), "Waiting for ORB-SLAM3 poses...");
    }

private:
    void orbPoseCallback(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
    {
        try {
            rclcpp::Time current_time = this->get_clock()->now();
            
            // Contrôle de fréquence
            double dt_publish = (current_time - last_published_time_).seconds();
            if (dt_publish < (1.0 / publish_frequency_)) {
                return;
            }
            
            // Validation du tracking ORB-SLAM3
            if (!isORBTrackingStable(msg)) {
                RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                                   "ORB-SLAM3 tracking instable - pose ignorée");
                return;
            }
            
            // Transformation de la pose caméra vers base_footprint
            geometry_msgs::msg::PoseStamped robot_pose = transformCameraToRobot(msg);
            
            // Validation de la pose
            if (!isValidRobotPose(robot_pose, current_time)) {
                return;
            }
            
            // Application du filtrage
            robot_pose = applySmoothingFilter(robot_pose);
            updatePoseHistory(robot_pose);
            
            if (!first_valid_pose_received_) {
                RCLCPP_INFO(this->get_logger(), 
                           "✓ Première pose ORB-SLAM3 reçue: x=%.2f, y=%.2f, yaw=%.2f°",
                           robot_pose.pose.position.x, robot_pose.pose.position.y,
                           getYawFromQuaternion(robot_pose.pose.orientation) * 180.0 / M_PI);
                first_valid_pose_received_ = true;
            }
            
            // Publication pour monitoring
            robot_pose_pub_->publish(robot_pose);
            
            // CORRECTION CRITIQUE: Stockage thread-safe avec timestamp cohérent
            {
                std::lock_guard<std::mutex> lock(pose_mutex_);
                current_robot_pose_ = robot_pose;
                current_robot_pose_.header.stamp = current_time;
                pose_available_ = true;
                last_pose_update_time_ = current_time;
            }
            
            last_update_time_ = current_time;
            last_published_time_ = current_time;
                                 
        } catch (const std::exception &e) {
            RCLCPP_ERROR(this->get_logger(), "Erreur dans orbPoseCallback: %s", e.what());
        }
    }

    geometry_msgs::msg::PoseStamped transformCameraToRobot(const geometry_msgs::msg::PoseStamped::SharedPtr &camera_msg)
    {
        geometry_msgs::msg::PoseStamped robot_pose;
        
        // Frame de référence: map
        robot_pose.header.stamp = camera_msg->header.stamp;
        robot_pose.header.frame_id = "map";

        // Transformation camera -> robot optimisée
        tf2::Transform camera_in_map;
        camera_in_map.setOrigin(tf2::Vector3(
            camera_msg->pose.position.x,
            camera_msg->pose.position.y,
            camera_msg->pose.position.z
        ));
        
        tf2::Quaternion camera_quat;
        tf2::fromMsg(camera_msg->pose.orientation, camera_quat);
        camera_in_map.setRotation(camera_quat);

        // Transformation left_camera_link -> base_footprint
        tf2::Transform camera_to_base;
        camera_to_base.setOrigin(tf2::Vector3(
            -camera_to_base_x_,
            -camera_to_base_y_,
            -camera_to_base_z_
        ));
        camera_to_base.setRotation(tf2::Quaternion::getIdentity());

        // Calcul final
        tf2::Transform base_in_map = camera_in_map * camera_to_base;

        // Position
        tf2::Vector3 base_position = base_in_map.getOrigin();
        robot_pose.pose.position.x = base_position.getX();
        robot_pose.pose.position.y = base_position.getY();
        robot_pose.pose.position.z = base_footprint_height_;

        // Orientation (yaw seulement pour la navigation)
        tf2::Quaternion base_orientation = base_in_map.getRotation();
        tf2::Matrix3x3 mat(base_orientation);
        double roll, pitch, yaw;
        mat.getRPY(roll, pitch, yaw);
        
        tf2::Quaternion yaw_only;
        yaw_only.setRPY(0, 0, yaw);
        robot_pose.pose.orientation = tf2::toMsg(yaw_only);

        return robot_pose;
    }

    // NOUVEAU: Synchronisation avec l'odométrie Gazebo
    void syncWithGazebo()
    {
        try {
            // Vérifier que Gazebo publie bien odom->base_footprint
            geometry_msgs::msg::TransformStamped gazebo_odom;
            gazebo_odom = tf_buffer_->lookupTransform(
                "odom", "base_footprint",
                tf2::TimePointZero,
                tf2::durationFromSec(0.1));
                
            // Stocker la dernière transform Gazebo
            {
                std::lock_guard<std::mutex> lock(gazebo_mutex_);
                last_gazebo_odom_ = gazebo_odom;
                gazebo_odom_available_ = true;
            }
            
        } catch (tf2::TransformException &ex) {
            // Gazebo n'est pas encore prêt
            gazebo_odom_available_ = false;
        }
    }

    void publishTransforms()
    {
        std::lock_guard<std::mutex> lock(pose_mutex_);
        
        if (!pose_available_ || !gazebo_odom_available_) {
            return;
        }

        // CORRECTION: Vérifier que la pose n'est pas trop ancienne
        rclcpp::Time now = this->get_clock()->now();
        double age = (now - last_pose_update_time_).seconds();
        if (age > 1.0) {  // Pose trop ancienne
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "Pose ORB-SLAM3 trop ancienne (%.2f s)", age);
            return;
        }

        try {
            publishMapToOdomTransform(now);
        } catch (const std::exception &ex) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 3000,
                               "Erreur publication transform: %s", ex.what());
        }
    }

    void publishMapToOdomTransform(const rclcpp::Time& now)
    {
        try {
            std::lock_guard<std::mutex> gazebo_lock(gazebo_mutex_);
            
            // CORRECTION CRITIQUE: Utiliser directement la transform Gazebo
            geometry_msgs::msg::TransformStamped odom_to_base = last_gazebo_odom_;
            
            // CORRECTION: Calcul map->odom avec la pose ORB-SLAM3
            tf2::Transform map_to_base, odom_to_base_tf;
            
            // Conversion des poses
            tf2::fromMsg(current_robot_pose_.pose, map_to_base);
            tf2::fromMsg(odom_to_base.transform, odom_to_base_tf);

            // Calcul: map->odom = map->base_footprint * base_footprint->odom
            tf2::Transform base_to_odom = odom_to_base_tf.inverse();
            tf2::Transform map_to_odom = map_to_base * base_to_odom;

            // CORRECTION CRITIQUE: Gestion de l'initialisation
            if (!map_to_odom_initialized_) {
                initial_map_to_odom_ = map_to_odom;
                map_to_odom_initialized_ = true;
                RCLCPP_INFO(this->get_logger(), "✓ Transform map->odom initialisée");
            }

            // NOUVEAU: Lissage de la transformation map->odom pour éviter les sauts
            tf2::Transform smoothed_map_to_odom = smoothTransform(initial_map_to_odom_, map_to_odom, 0.1);

            // CORRECTION CRITIQUE: Publication avec timestamp dans le futur
            rclcpp::Time tf_time = now + rclcpp::Duration::from_seconds(tf_future_dating_);
            
            geometry_msgs::msg::TransformStamped map_to_odom_msg;
            map_to_odom_msg.header.stamp = tf_time;
            map_to_odom_msg.header.frame_id = "map";
            map_to_odom_msg.child_frame_id = "odom";
            map_to_odom_msg.transform = tf2::toMsg(smoothed_map_to_odom);

            // Validation avant publication
            if (isValidTransform(map_to_odom_msg.transform)) {
                tf_broadcaster_->sendTransform(map_to_odom_msg);
                
                // Mise à jour de la référence
                initial_map_to_odom_ = smoothed_map_to_odom;
                
                // Debug périodique
                static int debug_counter = 0;
                if (++debug_counter % 150 == 0) {
                    RCLCPP_INFO(this->get_logger(), 
                                "TF map->odom: [%.2f, %.2f, %.2f°] | Robot dans map: [%.2f, %.2f]",
                                map_to_odom_msg.transform.translation.x,
                                map_to_odom_msg.transform.translation.y,
                                getYawFromTransform(map_to_odom_msg.transform) * 180.0 / M_PI,
                                current_robot_pose_.pose.position.x,
                                current_robot_pose_.pose.position.y);
                }
            } else {
                RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                                     "Transform map->odom invalide - non publié");
            }
            
        } catch (const std::exception &ex) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "Erreur calcul map->odom: %s", ex.what());
        }
    }

    // NOUVEAU: Lissage des transformations pour éviter les sauts
    tf2::Transform smoothTransform(const tf2::Transform& reference, const tf2::Transform& new_transform, double alpha)
    {
        tf2::Transform result;
        
        // Lissage de la translation
        tf2::Vector3 ref_origin = reference.getOrigin();
        tf2::Vector3 new_origin = new_transform.getOrigin();
        tf2::Vector3 smoothed_origin = ref_origin.lerp(new_origin, alpha);
        result.setOrigin(smoothed_origin);
        
        // Lissage de la rotation
        tf2::Quaternion ref_rot = reference.getRotation();
        tf2::Quaternion new_rot = new_transform.getRotation();
        tf2::Quaternion smoothed_rot = ref_rot.slerp(new_rot, alpha);
        result.setRotation(smoothed_rot);
        
        return result;
    }

    bool isValidTransform(const geometry_msgs::msg::Transform& transform) {
        // Vérifier les NaN et infinis
        if (std::isnan(transform.translation.x) || std::isnan(transform.translation.y) ||
            std::isnan(transform.translation.z) ||
            std::isinf(transform.translation.x) || std::isinf(transform.translation.y) ||
            std::isinf(transform.translation.z)) {
            return false;
        }
        
        // Vérifier le quaternion
        tf2::Quaternion q;
        tf2::fromMsg(transform.rotation, q);
        double norm = q.length();
        if (std::abs(norm - 1.0) > 0.1) {
            return false;
        }
        
        return true;
    }

    double getYawFromTransform(const geometry_msgs::msg::Transform& transform) {
        tf2::Quaternion q;
        tf2::fromMsg(transform.rotation, q);
        tf2::Matrix3x3 mat(q);
        double roll, pitch, yaw;
        mat.getRPY(roll, pitch, yaw);
        return yaw;
    }

    void relocalizeCallback(const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
                           std::shared_ptr<std_srvs::srv::Trigger::Response> response)
    {
        std::lock_guard<std::mutex> lock(pose_mutex_);
        
        if (pose_initialized_ && pose_available_) {
            // NOUVEAU: Réinitialiser la transformation map->odom
            map_to_odom_initialized_ = false;
            response->success = true;
            response->message = "Robot relocalisé avec succès - transform map->odom réinitialisée";
            RCLCPP_INFO(this->get_logger(), "✓ Relocalisation manuelle effectuée");
        } else {
            response->success = false;
            response->message = "Aucune pose valide disponible pour la relocalisation";
        }
    }

    // Méthodes de validation
    bool isORBTrackingStable(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
    {
        // Vérification des NaN et infinis
        if (std::isnan(msg->pose.position.x) || std::isnan(msg->pose.position.y) ||
            std::isnan(msg->pose.position.z) ||
            std::isinf(msg->pose.position.x) || std::isinf(msg->pose.position.y) ||
            std::isinf(msg->pose.position.z)) {
            return false;
        }

        // Validation du quaternion
        tf2::Quaternion q;
        tf2::fromMsg(msg->pose.orientation, q);
        if (std::abs(q.length() - 1.0) > 0.1) {
            return false;
        }

        return true;
    }

    bool isValidRobotPose(const geometry_msgs::msg::PoseStamped &pose, const rclcpp::Time &current_time)
    {
        // Vérification de base
        if (std::isnan(pose.pose.position.x) || std::isnan(pose.pose.position.y) ||
            std::isinf(pose.pose.position.x) || std::isinf(pose.pose.position.y)) {
            return false;
        }

        if (!pose_initialized_) {
            return true;
        }

        // Vérification de vitesse
        double dt = (current_time - last_update_time_).seconds();
        if (dt <= 0.001) return true;

        double dx = pose.pose.position.x - filtered_pose_.pose.position.x;
        double dy = pose.pose.position.y - filtered_pose_.pose.position.y;
        double velocity = std::sqrt(dx*dx + dy*dy) / dt;

        if (velocity > max_velocity_) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "Vitesse excessive détectée: %.2f m/s", velocity);
            return false;
        }

        return true;
    }

    geometry_msgs::msg::PoseStamped applySmoothingFilter(const geometry_msgs::msg::PoseStamped &raw_pose)
    {
        if (!pose_initialized_) {
            filtered_pose_ = raw_pose;
            pose_initialized_ = true;
            return filtered_pose_;
        }

        // Lissage de position
        filtered_pose_.pose.position.x = smoothing_alpha_ * raw_pose.pose.position.x +
                                        (1.0 - smoothing_alpha_) * filtered_pose_.pose.position.x;
        filtered_pose_.pose.position.y = smoothing_alpha_ * raw_pose.pose.position.y +
                                        (1.0 - smoothing_alpha_) * filtered_pose_.pose.position.y;
        filtered_pose_.pose.position.z = raw_pose.pose.position.z;

        // Interpolation sphérique pour l'orientation
        tf2::Quaternion current_q, new_q, filtered_q;
        tf2::fromMsg(filtered_pose_.pose.orientation, current_q);
        tf2::fromMsg(raw_pose.pose.orientation, new_q);
        
        filtered_q = current_q.slerp(new_q, smoothing_alpha_);
        filtered_pose_.pose.orientation = tf2::toMsg(filtered_q);

        filtered_pose_.header = raw_pose.header;
        return filtered_pose_;
    }

    void updatePoseHistory(const geometry_msgs::msg::PoseStamped &pose)
    {
        pose_history_.push_back(pose);
        if (pose_history_.size() > static_cast<size_t>(pose_buffer_size_)) {
            pose_history_.pop_front();
        }
    }

    double getYawFromQuaternion(const geometry_msgs::msg::Quaternion &q)
    {
        tf2::Quaternion tf_q;
        tf2::fromMsg(q, tf_q);
        tf2::Matrix3x3 mat(tf_q);
        double roll, pitch, yaw;
        mat.getRPY(roll, pitch, yaw);
        return yaw;
    }

    // Membres de classe
    rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr orb_pose_sub_;
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr robot_pose_pub_;
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr relocalize_service_;
    rclcpp::TimerBase::SharedPtr transform_timer_;
    rclcpp::TimerBase::SharedPtr sync_timer_;  // NOUVEAU: Timer de synchronisation

    std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    // CORRECTION: Mutex pour thread safety
    std::mutex pose_mutex_;
    std::mutex gazebo_mutex_;  // NOUVEAU: Mutex pour Gazebo

    // Paramètres de transformation
    double camera_to_base_x_, camera_to_base_y_, camera_to_base_z_;
    double base_footprint_height_;
    
    // Paramètres TF optimisés
    double tf_publish_rate_;
    double tf_timeout_;
    double transform_tolerance_;
    double tf_future_dating_;  // NOUVEAU: Projection dans le futur
    
    // Paramètres de filtrage
    double smoothing_alpha_;
    double min_pose_change_;
    double min_angle_change_;
    double max_velocity_;
    int pose_buffer_size_;
    double min_tracking_confidence_;
    double publish_frequency_;
    
    // Variables d'état
    bool pose_initialized_;
    bool first_valid_pose_received_;
    bool pose_available_;
    bool gazebo_odom_available_;      // NOUVEAU: État de Gazebo
    bool map_to_odom_initialized_;    // NOUVEAU: État de l'initialisation
    
    geometry_msgs::msg::PoseStamped filtered_pose_;
    geometry_msgs::msg::PoseStamped current_robot_pose_;
    geometry_msgs::msg::TransformStamped last_gazebo_odom_;  // NOUVEAU: Dernière transform Gazebo
    tf2::Transform initial_map_to_odom_;  // NOUVEAU: Transform de référence
    
    std::deque<geometry_msgs::msg::PoseStamped> pose_history_;
    rclcpp::Time last_update_time_;
    rclcpp::Time last_published_time_;
    rclcpp::Time last_pose_update_time_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PoseTransformer>();
    
    RCLCPP_INFO(node->get_logger(), "Démarrage du pipeline Visual SLAM CORRIGÉ (Gazebo sync)...");
    RCLCPP_INFO(node->get_logger(), "Mode: map->odom synchronisé avec l'odométrie Gazebo");
    
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}