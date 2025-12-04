import can
import struct
import time
import math

class CyberGearMotor:
    def __init__(self, interface='slcan', channel='COM16', bitrate=1000000):
        """
        Initialize CyberGear motor with USB-CAN adapter on Windows
        """
        try:
            self.bus = can.interface.Bus(
                channel=channel,
                interface=interface,
                bitrate=bitrate,
                ttyBaudrate=115200
            )
            print(f"✓ Connected to {interface}:{channel} at {bitrate} bps")
        except Exception as e:
            raise Exception(f"Failed to connect to CAN bus: {e}")
        
        self.master_id = 0x00FD
        self.last_positions = {}
    
    def send_can_frame(self, cmd_id, motor_id, data, retry=3):
        """Send CAN frame with retry logic"""
        can_id = (cmd_id << 24) | (self.master_id << 8) | motor_id
        
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=True
        )
        
        for attempt in range(retry):
            try:
                self.bus.send(msg)
                time.sleep(0.015)
                return True
            except Exception as e:
                if attempt == retry - 1:
                    print(f"Error sending CAN frame after {retry} attempts: {e}")
                    return False
                time.sleep(0.05)
        return False
    
    def enable_motor(self, motor_id):
        """Enable motor - Command ID: 0x03"""
        data = [0x00] * 8
        self.send_can_frame(0x03, motor_id, data)
        time.sleep(0.3)
        print(f"  ✓ Motor {motor_id} enabled")
    
    def disable_motor(self, motor_id):
        """Disable motor - Command ID: 0x04"""
        data = [0x00] * 8
        self.send_can_frame(0x04, motor_id, data)
        time.sleep(0.3)
        print(f"  ✓ Motor {motor_id} disabled")
    
    def stop_motor(self, motor_id):
        """Stop motor immediately"""
        data = [0x00] * 8
        self.send_can_frame(0x00, motor_id, data)
        time.sleep(0.1)
        print(f"  ✓ Motor {motor_id} stopped")
    
    def reset_position(self, motor_id):
        """Reset position to zero - Command ID: 0x06"""
        data = [0x01] + [0x00] * 7
        self.send_can_frame(0x06, motor_id, data)
        self.last_positions[motor_id] = 0.0
        time.sleep(0.3)
        print(f"  ✓ Motor {motor_id} position reset to zero")
    
    def set_position_control_mode(self, motor_id):
        """Set motor to position control mode"""
        data = [0x05, 0x70, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00]
        self.send_can_frame(0x12, motor_id, data)
        time.sleep(0.2)
        print(f"  ✓ Motor {motor_id} set to position control mode")
    
    def set_limit_speed(self, motor_id, speed_rad_s):
        """Set speed limit"""
        speed_bytes = struct.pack('<f', speed_rad_s)
        data = [0x17, 0x70, 0x00, 0x00] + list(speed_bytes)
        self.send_can_frame(0x12, motor_id, data)
        time.sleep(0.05)
    
    def set_limit_torque(self, motor_id, torque_nm):
        """Set torque limit"""
        torque_bytes = struct.pack('<f', torque_nm)
        data = [0x18, 0x70, 0x00, 0x00] + list(torque_bytes)
        self.send_can_frame(0x12, motor_id, data)
        time.sleep(0.05)
    
    def set_target_position(self, motor_id, radians):
        """Set target position"""
        pos_bytes = struct.pack('<f', radians)
        data = [0x16, 0x70, 0x00, 0x00] + list(pos_bytes)
        success = self.send_can_frame(0x12, motor_id, data)
        
        if success:
            self.last_positions[motor_id] = radians
        
        time.sleep(0.05)
        return success
    
    def move_to_degrees(self, motor_id, degrees, speed_rad_s=5.0, torque_nm=12.0):
        """Move motor to target position in degrees"""
        radians = math.radians(degrees)
        self.set_limit_torque(motor_id, torque_nm)
        self.set_limit_speed(motor_id, speed_rad_s)
        self.set_target_position(motor_id, radians)
    
    def close(self):
        """Close CAN connection"""
        if hasattr(self, 'bus'):
            self.bus.shutdown()
            print("✓ CAN connection closed")


def main():
    # Configuration for Windows
    INTERFACE = 'slcan'
    CHANNEL = 'COM16'  # Change this to your COM port (COM3, COM4, COM5, etc.)
    MOTOR_ID = 1
    SPEED = 2.0
    MAX_TORQUE = 12.0
    
    print("\n" + "="*60)
    print("CyberGear Single Motor Controller - Windows")
    print("="*60)
    print(f"Interface: {INTERFACE}")
    print(f"COM Port: {CHANNEL}")
    print(f"Motor ID: {MOTOR_ID}")
    print("Test: 15° Clockwise and Anti-clockwise")
    print("="*60 + "\n")
    
    motor = None
    
    try:
        motor = CyberGearMotor(interface=INTERFACE, channel=CHANNEL)
        
        print("[Initialization]")
        motor.enable_motor(MOTOR_ID)
        time.sleep(0.5)
        
        motor.reset_position(MOTOR_ID)
        time.sleep(0.5)
        
        motor.set_position_control_mode(MOTOR_ID)
        time.sleep(0.5)
        
        print("\n✓ Motor initialized at 0°")
        
        # Move 15° clockwise
        print("\n[Moving 15° Clockwise]")
        motor.move_to_degrees(MOTOR_ID, 15, SPEED, MAX_TORQUE)
        print("  → Motor moving to 15°...")
        time.sleep(3)
        
        # Move back to 0°
        print("\n[Returning to 0°]")
        motor.move_to_degrees(MOTOR_ID, 0, SPEED, MAX_TORQUE)
        print("  → Motor moving to 0°...")
        time.sleep(3)
        
        # Move 15° anti-clockwise (negative)
        print("\n[Moving 15° Anti-clockwise]")
        motor.move_to_degrees(MOTOR_ID, -15, SPEED, MAX_TORQUE)
        print("  → Motor moving to -15°...")
        time.sleep(3)
        
        # Return to 0°
        print("\n[Returning to 0°]")
        motor.move_to_degrees(MOTOR_ID, 0, SPEED, MAX_TORQUE)
        print("  → Motor moving to 0°...")
        time.sleep(3)
        
        print("\n✓ Test sequence completed")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Shutdown initiated by user")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if your USB-CAN adapter is connected")
        print("2. Verify the correct COM port in Device Manager")
        print("3. Update CHANNEL variable (e.g., 'COM3', 'COM4', 'COM5')")
        print("4. Ensure python-can is installed: pip install python-can")
        import traceback
        traceback.print_exc()
        
    finally:
        if motor:
            try:
                print("\n[Shutdown Sequence]")
                motor.stop_motor(MOTOR_ID)
                time.sleep(0.3)
                motor.disable_motor(MOTOR_ID)
                time.sleep(0.3)
                motor.close()
                print("\n✓ Shutdown completed successfully")
            except Exception as shutdown_error:
                print(f"✗ Error during shutdown: {shutdown_error}")
        
        print("\n" + "="*60)
        print("Program ended")
        print("="*60)


if __name__ == "__main__":
    main()