#!/usr/bin/env python

import os
import pygame
from geometry_msgs.msg import Twist
from geometry_msgs.msg import TwistStamped
import rclpy
from rclpy.clock import Clock
from rclpy.qos import QoSProfile

BASE_CRUISE_VEL = 0.10  # Speed when cruising
BOOST_LINEAR_VEL = 0.22  # Speed when pressing W
REVERSE_VEL = -0.10     # Speed when reversing
CRUISE_ANGULAR_VEL = 1.0
TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'burger')

def check_linear_limit_velocity(velocity):
    MAX_VEL = 0.22 if TURTLEBOT3_MODEL == 'burger' else 0.26
    return max(-MAX_VEL, min(MAX_VEL, velocity))

def check_angular_limit_velocity(velocity):
    MAX_VEL = 2.84 if TURTLEBOT3_MODEL == 'burger' else 1.82
    return max(-MAX_VEL, min(MAX_VEL, velocity))

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption('TurtleBot3 Game Controls')
    clock = pygame.time.Clock()

    rclpy.init()
    ROS_DISTRO = os.environ.get('ROS_DISTRO')
    qos = QoSProfile(depth=10)
    node = rclpy.create_node('teleop_keyboard')
    
    if ROS_DISTRO == 'humble':
        pub = node.create_publisher(Twist, 'cmd_vel', qos)
    else:
        pub = node.create_publisher(TwistStamped, 'cmd_vel', qos)

    font = pygame.font.Font(None, 24)
    running = True
    cruise_on = True  # Cruise starts enabled
    
    print("Game controls active!")
    print("W: Accelerate | A: Left | D: Right | S: Brake/Stop")
    print("C: Toggle cruise | R (hold): Reverse")
    
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        cruise_on = not cruise_on
                        print(f"Cruise {'ON' if cruise_on else 'OFF'}")

            # Get currently pressed keys
            keys = pygame.key.get_pressed()
            
            # Calculate velocities
            # Default depends on cruise toggle
            linear_vel = BASE_CRUISE_VEL if cruise_on else 0.0
            
            # W accelerates
            if keys[pygame.K_w]:
                linear_vel = BOOST_LINEAR_VEL
            
            # S brakes/stops
            if keys[pygame.K_s]:
                linear_vel = 0.0
            
            # R reverses
            if keys[pygame.K_r]:
                linear_vel = REVERSE_VEL
            
            angular_vel = 0.0
            if keys[pygame.K_a]:
                angular_vel = CRUISE_ANGULAR_VEL
            elif keys[pygame.K_d]:
                angular_vel = -CRUISE_ANGULAR_VEL
            
            # Apply limits
            linear_vel = check_linear_limit_velocity(linear_vel)
            angular_vel = check_angular_limit_velocity(angular_vel)
            
            # Publish
            if ROS_DISTRO == 'humble':
                twist = Twist()
                twist.linear.x = linear_vel
                twist.angular.z = angular_vel
                pub.publish(twist)
            else:
                twist_stamped = TwistStamped()
                twist_stamped.header.stamp = Clock().now().to_msg()
                twist_stamped.twist.linear.x = linear_vel
                twist_stamped.twist.angular.z = angular_vel
                pub.publish(twist_stamped)
            
            # Display status
            screen.fill((0, 0, 0))
            if linear_vel < 0:
                mode = "REVERSE"
            elif linear_vel == 0:
                mode = "STOPPED"
            elif linear_vel > BASE_CRUISE_VEL:
                mode = "GAS"
            elif cruise_on:
                mode = "CRUISE"
            else:
                mode = "MANUAL"
            text1 = font.render(f'Mode: {mode}   Cruise: {"ON" if cruise_on else "OFF"}', True, (255, 255, 255))
            text2 = font.render(f'Linear: {linear_vel:.2f} Angular: {angular_vel:.2f}', True, (255, 255, 255))
            text3 = font.render('W:Gas A/D:Turn S:Stop C:Cruise R:Reverse', True, (150, 150, 150))
            screen.blit(text1, (10, 10))
            screen.blit(text2, (10, 40))
            screen.blit(text3, (10, 70))
            pygame.display.flip()
            
            clock.tick(20)  # 20 Hz
            
    finally:
        # Stop robot
        if ROS_DISTRO == 'humble':
            twist = Twist()
        else:
            twist_stamped = TwistStamped()
            twist_stamped.header.stamp = Clock().now().to_msg()
        
        pub.publish(twist if ROS_DISTRO == 'humble' else twist_stamped)
        pygame.quit()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
