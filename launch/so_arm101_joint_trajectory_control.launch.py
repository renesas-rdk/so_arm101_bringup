#!/usr/bin/env python3
# *********************************************************************************************************************
# Copyright [2026] Renesas Electronics Corporation and/or its licensors. All Rights Reserved.
#
# The contents of this file (the "contents") are proprietary and confidential to Renesas Electronics Corporation
# and/or its licensors ("Renesas") and subject to statutory and contractual protections.
#
# Unless otherwise expressly agreed in writing between Renesas and you: 1) you may not use, copy, modify, distribute,
# display, or perform the contents; 2) you may not use any name or mark of Renesas for advertising or publicity
# purposes or in connection with your use of the contents; 3) RENESAS MAKES NO WARRANTY OR REPRESENTATIONS ABOUT THE
# SUITABILITY OF THE CONTENTS FOR ANY PURPOSE; THE CONTENTS ARE PROVIDED "AS IS" WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NON-INFRINGEMENT; AND 4) RENESAS SHALL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL, OR CONSEQUENTIAL DAMAGES,
# INCLUDING DAMAGES RESULTING FROM LOSS OF USE, DATA, OR PROJECTS, WHETHER IN AN ACTION OF CONTRACT OR TORT, ARISING
# OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE CONTENTS. Third-party contents included in this file may
# be subject to different terms.
# *********************************************************************************************************************

"""
Launch file for SO ARM101 with joint trajectory control.

This launch file starts:
- ros2_control_node: Main controller manager for hardware interface
- robot_state_publisher: Publishes TF transforms from URDF
- joint_state_broadcaster: Publishes joint states from hardware
- joint_trajectory_controller: Provides joint space trajectory following
- gripper_controller: Provides gripper position control
- gpio_controller: Provides arm administrative control (torque enable/disable)
- foxglove_bridge: WebSocket bridge for Foxglove Studio visualization

Usage:
  # For physical robot with serial interface:
  ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py
  ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py serial_port:=/dev/ttyUSB1

  # For SIMULATION/TESTING without physical robot (RECOMMENDED for testing):
  ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py use_mock_hardware:=true

  Then connect Foxglove Studio to ws://<foxglove_bridge_ip>:8765

Test trajectory in another terminal with:
  ros2 action send_goal /so_arm101_joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{
    trajectory: {
      joint_names: [shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll],
      points: [
        { positions: [0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 2 } },
        { positions: [0.785, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 4 } },
        { positions: [0.785, 0.524, 0.0, 0.0, 0.0], time_from_start: { sec: 6 } },
        { positions: [0.785, 0.524, -0.524, 0.0, 0.0], time_from_start: { sec: 8 } },
        { positions: [0.0, 0.785, -0.785, 0.524, 0.0], time_from_start: { sec: 10 } },
        { positions: [0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 12 } }
      ]
    }
  }"

Test gripper commands:
  # Use standard gripper action interface (position = normalized opening 0-1):
  ros2 action send_goal /gripper_cmd control_msgs/action/ParallelGripperCommand "{command: {position: [0.5], effort: [10.0]}}"

  # Or use simple topic interface:
  ros2 topic pub /gripper_command control_msgs/msg/GripperCommand "{position: 0.5, max_effort: 10.0}"

  # Direct controller access (legacy):
  ros2 topic pub --once /so_arm101_gripper_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.5]}"

Test arm administrative control:
  # Enable arm torque (activate control)
  ros2 topic pub --once /so_arm101_gpio_controller/commands
    control_msgs/msg/DynamicInterfaceGroupValues
    "{interface_groups: ['arm_admin'], interface_values: [{interface_names: ['enable_torque'], values: [1.0]}]}"

  # Disable arm torque (safe mode - free-moving)
  ros2 topic pub --once /so_arm101_gpio_controller/commands
    control_msgs/msg/DynamicInterfaceGroupValues
    "{interface_groups: ['arm_admin'], interface_values: [{interface_names: ['enable_torque'], values: [0.0]}]}"

Or run the Python test script:
  python3 ros2_ws/install/so_arm101_bringup/share/so_arm101_bringup/test/test_joint_trajectory.py

Observe the arm moving in foxglove studio.

NOTE: Use 'use_mock_hardware:=true' for simulation or safe testing without physical hardware!
"""

import os
from typing import List

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import FrontendLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs) -> List[Node]:
    """Setup function to evaluate launch configurations at runtime."""
    # Get launch configurations
    serial_port_value = LaunchConfiguration('serial_port').perform(context)
    serial_baudrate_value = LaunchConfiguration('serial_baudrate').perform(context)
    use_mock_hardware_value = LaunchConfiguration('use_mock_hardware').perform(context)
    calibration_file_value = LaunchConfiguration('calibration_file').perform(context)

    # Get package directories
    pkg_share = get_package_share_directory('so_arm101_bringup')

    # Default calibration file path
    if calibration_file_value == '':
        calibration_file_value = os.path.join(pkg_share, 'config', 'so_arm101_calibration.yaml')

    # Robot description (always includes gripper)
    robot_description_xacro = os.path.join(
        pkg_share, 'urdf', 'so_arm101.urdf.xacro'
    )

    # Process XACRO file with parameters
    robot_description_raw = xacro.process_file(
        robot_description_xacro,
        mappings={
            'serial_port': serial_port_value,
            'serial_baudrate': serial_baudrate_value,
            'use_mock_hardware': use_mock_hardware_value,
            'calibration_file': calibration_file_value,
        }
    ).toxml()

    robot_description = {'robot_description': robot_description_raw}

    # Controller configurations
    controller_config = os.path.join(
        pkg_share, 'config', 'controller_manager.yaml'
    )

    joint_trajectory_config = os.path.join(
        pkg_share, 'config', 'so_arm101_joint_trajectory_controller.yaml'
    )

    gripper_config = os.path.join(
        pkg_share, 'config', 'so_arm101_gripper_position_controller.yaml'
    )

    gpio_config = os.path.join(
        pkg_share, 'config', 'so_arm101_gpio_controller.yaml'
    )

    # Foxglove bridge launch file
    foxglove_bridge_launch = os.path.join(
        get_package_share_directory('foxglove_bridge'),
        'launch',
        'foxglove_bridge_launch.xml'
    )

    # Nodes
    nodes: List[Node] = [
        # Controller manager
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            name='controller_manager',
            output='screen',
            parameters=[
                robot_description,
                controller_config,
                joint_trajectory_config,
                gripper_config,
                gpio_config,
            ],
            remappings=[
                ('/controller_manager/robot_description', '/robot_description'),
            ],
        ),
        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[robot_description],
        ),
        # Joint state broadcaster (always start)
        Node(
            package='controller_manager',
            executable='spawner',
            name='joint_state_broadcaster_spawner',
            output='screen',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        ),
        # Joint trajectory controller spawner
        Node(
            package='controller_manager',
            executable='spawner',
            name='joint_trajectory_controller_spawner',
            output='screen',
            arguments=[
                'so_arm101_joint_trajectory_controller',
                '--controller-manager', '/controller_manager',
            ],
        ),
        # Foxglove bridge for web-based visualization
        IncludeLaunchDescription(
            FrontendLaunchDescriptionSource(foxglove_bridge_launch)
        ),
        # Gripper controller (always included since gripper is integrated)
        Node(
            package='controller_manager',
            executable='spawner',
            name='gripper_controller_spawner',
            output='screen',
            arguments=[
                'so_arm101_gripper_position_controller',
                '--controller-manager', '/controller_manager',
            ],
        ),
        # GPIO controller for arm administrative control
        Node(
            package='controller_manager',
            executable='spawner',
            name='gpio_controller_spawner',
            output='screen',
            arguments=[
                'so_arm101_gpio_controller',
                '--controller-manager', '/controller_manager',
            ],
        ),
        # Gripper action adapter for standard gripper interfaces
        Node(
            package='so_arm101_utils',
            executable='gripper_action_adapter',
            name='gripper_action_adapter',
            output='screen',
            parameters=[{
                'action_server_name': 'gripper_cmd',
                'gripper_command_topic': 'gripper_command',
                'position_controller_topic': '/so_arm101_gripper_position_controller/commands',
                'max_gripper_width': 1.0,
            }],
        )
    ]

    return nodes


def generate_launch_description() -> LaunchDescription:
    """Generate launch description for SO ARM101 with joint trajectory control."""
    # Declare arguments
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyACM0',
        description='Serial port for hardware communication'
    )

    serial_baudrate_arg = DeclareLaunchArgument(
        'serial_baudrate',
        default_value='1000000',
        description='Serial baudrate for hardware communication'
    )

    use_mock_hardware_arg = DeclareLaunchArgument(
        'use_mock_hardware',
        default_value='false',
        description='Use mock hardware for testing (true/false)'
    )

    calibration_file_arg = DeclareLaunchArgument(
        'calibration_file',
        default_value='',
        description='Path to joint calibration file (optional)'
    )

    return LaunchDescription([
        serial_port_arg,
        serial_baudrate_arg,
        use_mock_hardware_arg,
        calibration_file_arg,
        OpaqueFunction(function=launch_setup)
    ])