import math
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose


class RectangleTurtle(Node):

    def __init__(self):
        super().__init__('rectangle_turtle')

        # FSM başlangıç durumu
        self.state = 'INIT'

        # Robotun başlangıç konumu
        self.start_x = None
        self.start_y = None
        self.start_theta = None

        # Pose topic'ine abone ol
        self.pose_subscriber = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.get_logger().info('Rectangle Turtle başlatıldı.')


                # Dikdörtgenin kenar uzunlukları
        self.edges = [3.0, 2.0, 3.0, 2.0]
        self.edge_index = 0

        # Mesafe toleransı
        self.DIST_TOLERANCE = 0.02

        # İlerleme hızı
        self.LINEAR_SPEED = 1.0

        # Robotun anlık konumu
        self.current_pose = None

        # dönüş toleransı ve açısal hız
        self.ANGLE_TOLERANCE = 0.02
        self.ANGULAR_SPEED = 1.0
        self.target_theta = None

        # Hız komutlarını yayınlayan Publisher
        self.velocity_publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        # Kontrol döngüsü (20 Hz)
        self.timer = self.create_timer(
            0.05,
            self.control_loop
        )

    def pose_callback(self, msg):

        self.current_pose = msg

        if self.state == 'INIT':

            self.start_x = msg.x
            self.start_y = msg.y
            self.start_theta = msg.theta


            # İlk kenarın referans konumu
            self.ref_x = msg.x
            self.ref_y = msg.y

            self.get_logger().info(
                f'Başlangıç konumu: '
                f'x={self.start_x:.2f}, '
                f'y={self.start_y:.2f}, '
                f'theta={self.start_theta:.2f}'
            )

            self.state = 'MOVE_FORWARD'

    def control_loop(self):

        if self.current_pose is None:
            return

        cmd = Twist()

        if self.state == 'MOVE_FORWARD':

            # Robotun mevcut konumu
            x = self.current_pose.x
            y = self.current_pose.y

            # Kenarın başlangıcından itibaren gidilen mesafe
            distance = math.hypot(
                x - self.ref_x,
                y - self.ref_y
            )

            # Hedef kenar uzunluğu
            target_distance = self.edges[self.edge_index]

            # Kalan mesafe hatası
            distance_error = target_distance - distance

            if distance_error > self.DIST_TOLERANCE:

                cmd.linear.x = self.LINEAR_SPEED
                cmd.angular.z = 0.0

            else:

                cmd.linear.x = 0.0
                cmd.angular.z = 0.0

                self.state = 'ROTATE'

                self.target_theta = (
                    self.start_theta
                    + (self.edge_index + 1) * (math.pi / 2)
                )

                self.get_logger().info(
                    f'{self.edge_index + 1}. kenar tamamlandı.'
                )

        elif self.state == 'ROTATE':

            current_theta = self.current_pose.theta

            angle_error = math.atan2(
                math.sin(self.target_theta - current_theta),
                math.cos(self.target_theta - current_theta)
            )

            if abs(angle_error) > self.ANGLE_TOLERANCE:

                cmd.linear.x = 0.0

                cmd.angular.z = (
                    self.ANGULAR_SPEED
                    if angle_error > 0
                    else -self.ANGULAR_SPEED
                )

            else:

                cmd.linear.x = 0.0
                cmd.angular.z = 0.0

                if self.edge_index < 3:

                    self.edge_index += 1

                    self.ref_x = self.current_pose.x
                    self.ref_y = self.current_pose.y

                    self.state = 'MOVE_FORWARD'

                else:
                    self.state = 'DONE'

                    self.get_logger().info(
                        'Dikdörtgen tamamlandı.'
                    )

        elif self.state == 'DONE':

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        elif self.state == 'DONE':

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0


        
        # Tüm durum kontrollerinden sonra hız komutunu yayınla
        self.velocity_publisher.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = RectangleTurtle()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()