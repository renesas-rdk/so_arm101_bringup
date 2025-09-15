# so_arm101_bringup

ROS 2 package that provides launch files, controller configurations, robot descriptions, and test scripts for the SO ARM101 robotic arm. This package contains everything needed to bring up and operate the robot.

## Features
- Launch files for different control modes (joint trajectory, joint position, Cartesian motion)
- Controller configurations for all supported control modes
- Complete robot URDF descriptions (arm-only and arm+gripper configurations)
- Test scripts for validating robot functionality
- Foxglove Studio configuration for visualization

## Related Packages
- **so_arm101_ros2_control**: Contains the hardware interface implementation for serial communication
- **so_arm101_description**: Contains the robot's visual and collision meshes, joint definitions

## Package layout
- `launch/`: Launch files for different control modes
- `config/`: Controller and controller_manager YAML configurations
- `urdf/`: Complete robot URDF descriptions
- `test/`: Example scripts for testing robot functionality

## Prerequisites
- ROS 2 (Jazzy or newer) with `ros2_control` and `ros2_controllers` ecosystem
- A colcon workspace (e.g., `~/ros2_ws`)
- `so_arm101_ros2_control` package for hardware interface
- `so_arm101_description` package for robot description

## Launch Modes

### Joint Trajectory Control
Provides FollowJointTrajectory action interface for smooth trajectory execution:
```bash
ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py
```

### Joint Position Control
Provides direct joint position command interface:
```bash
ros2 launch so_arm101_bringup so_arm101_joint_position_control.launch.py
```

### Cartesian Motion Control
Provides Cartesian space motion control:
```bash
ros2 launch so_arm101_bringup so_arm101_cartesian_motion_control.launch.py
```

## Launch Arguments
All launch files support the following arguments:
- `serial_port`: Serial port for hardware communication (default: "/dev/ttyACM0")
- `serial_baudrate`: Serial baudrate for hardware communication (default: "1000000")
- `use_mock_hardware`: Use mock hardware for testing (default: "false")

### Examples
```bash
# For physical robot with serial port /dev/ttyUSB1
ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py serial_port:=/dev/ttyUSB1

# For simulation/testing without physical robot
ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py use_mock_hardware:=true

# With custom baudrate
ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py serial_baudrate:=115200
```

## Controllers
Controller configurations are provided in `config/`:
- `controller_manager.yaml`: Controller manager settings and available controllers
- `so_arm101_joint_trajectory_controller.yaml`: Joint trajectory controller parameters
- `so_arm101_joint_position_controller.yaml`: Joint position controller parameters
- `so_arm101_gripper_position_controller.yaml`: Gripper position controller parameters
- `so_arm101_cartesian_motion_controller.yaml`: Cartesian motion controller parameters
- `so_arm101_motion_control_handle.yaml`: Motion control handle configuration

## Robot Descriptions
Complete robot URDF file in `urdf/`:
- `so_arm101.urdf.xacro`: Complete SO ARM101 with integrated gripper

## Joint Names
The SO ARM101 has the following joints:
- `shoulder_pan`: Base rotation joint
- `shoulder_lift`: Shoulder joint
- `elbow_flex`: Elbow joint
- `wrist_flex`: Wrist pitch joint
- `wrist_roll`: Wrist roll joint
- `gripper`: Gripper joint

## Testing
### Joint Trajectory Test
Run the included test script to validate joint trajectory control:
```bash
# Terminal 1: Launch trajectory controller
ros2 launch so_arm101_bringup so_arm101_joint_trajectory_control.launch.py use_mock_hardware:=true

# Terminal 2: Run test script
python3 /home/ubuntu/ros2_ws/src/robots/so_arm101/so_arm101_bringup/test/test_joint_trajectory.py
```

### Manual Commands
Test different control modes manually:

**Joint Trajectory Control:**
```bash
ros2 action send_goal /so_arm101_joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{
  trajectory: {
    joint_names: [shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper],
    points: [
      { positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 2 } },
      { positions: [0.785, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 4 } }
    ]
  }
}"
```

**Joint Position Control:**
```bash
ros2 topic pub --once /so_arm101_joint_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.785, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

**Cartesian Motion Control:**
```bash
ros2 topic pub --once /so_arm101_cartesian_motion_controller/target_frame geometry_msgs/msg/PoseStamped "{
  header: {frame_id: 'base_link'},
  pose: {
    position: {x: 0.2, y: 0.0, z: 0.2},
    orientation: {x: 0.0, y: 1.0, z: 0.0, w: 0.0}
  }
}"
```

**Gripper Control:**
```bash
ros2 topic pub --once /so_arm101_gripper_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.5]}"
```

## Hardware Configuration
The hardware interface uses the following parameters:
- `serial_port`: Device path for serial communication (e.g., /dev/ttyACM0)
- `serial_baudrate`: Communication speed in bps (default: 1000000)
- `enable_torque`: Enable servo torque on startup (default: true)
- `calibration_file`: Optional path to calibration data file

## Introspection
After launching, you can inspect the system:
```bash
ros2 control list_hardware_interfaces
ros2 control list_controllers
ros2 topic list
ros2 service list
```

## Foxglove Studio
An optional layout is available at `config/foxglove/arm_ros2_control.json`. Import it into Foxglove Studio to visualize:
- Joint states
- Controller feedback
- Robot model
- Control topics

Connect Foxglove Studio to `ws://localhost:8765` after launching any of the control modes.

## Safety Notes
- Always use `use_mock_hardware:=true` for initial testing
- Ensure proper serial connections and permissions before using physical hardware
- Monitor joint limits and workspace boundaries
- Test movements at slow speeds initially

## Troubleshooting
1. **Serial Communication Issues:**
   - Check device permissions: `sudo chmod 666 /dev/ttyACM0`
   - Verify correct port and baudrate settings
   - Ensure no other processes are using the serial port

2. **Controller Startup Issues:**
   - Check that all required packages are built and sourced
   - Verify joint names match between URDF and controller config
   - Monitor controller manager logs for specific errors

3. **Mock Hardware Testing:**
   - Use `use_mock_hardware:=true` to test without physical robot
   - Verify all topics and services are available

## License and maintainers
Refer to `package.xml` for license and maintainer information.