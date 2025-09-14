#!/usr/bin/env python3
"""
Basic DMX512 test script for WaveShare 2-CH RS485 HAT
Tests port access and sends simple DMX frames
"""

import serial
import time

def test_port_access():
    """Test if we can access both serial ports"""
    print("=== Port Access Test ===")
    
    ports = ['/dev/ttySC0', '/dev/ttySC1']
    results = {}
    
    for port_name in ports:
        try:
            ser = serial.Serial(
                port=port_name,
                baudrate=9600,
                timeout=1
            )
            print(f"✓ {port_name} - accessible")
            ser.close()
            results[port_name] = True
        except Exception as e:
            print(f"✗ {port_name} - error: {e}")
            results[port_name] = False
    
    all_ok = all(results.values())
    if all_ok:
        print("✓ All ports accessible\n")
    else:
        print("✗ Some ports failed. Check:")
        print("  - sudo usermod -a -G dialout $USER")
        print("  - HAT connection")
        print("  - /boot/firmware/config.txt settings\n")
    
    return all_ok

class BasicDMXController:
    """Simple DMX controller for testing"""
    
    def __init__(self, port='/dev/ttySC0'):
        self.port = port
        self.serial_port = None
        
    def open(self):
        """Open serial port for DMX communication"""
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=250000,  # DMX512 standard baud rate
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=2,
                timeout=1
            )
            print(f"✓ DMX port {self.port} opened")
            return True
        except Exception as e:
            print(f"✗ Failed to open {self.port}: {e}")
            return False
    
    def send_break(self):
        """Send DMX break signal (88 microseconds)"""
        if not self.serial_port:
            return False
            
        # Lower baud rate to create break timing
        original_baud = self.serial_port.baudrate
        self.serial_port.baudrate = 83333  # Approximates 88µs break
        self.serial_port.write(b'\x00')
        self.serial_port.flush()
        
        # Restore normal baud rate
        self.serial_port.baudrate = original_baud
        
        # Mark After Break (MAB) - minimum 12µs
        time.sleep(0.000012)
        
    def send_frame(self, channel_data):
        """Send complete DMX frame"""
        if not self.serial_port:
            return False
            
        # Send break signal
        self.send_break()
        
        # Send start code (0x00 for DMX512)
        self.serial_port.write(b'\x00')
        
        # Prepare frame data (pad to 512 channels)
        frame = list(channel_data[:512])
        while len(frame) < 512:
            frame.append(0)
            
        # Send channel data
        self.serial_port.write(bytes(frame))
        self.serial_port.flush()
        
        return True
    
    def close(self):
        """Close serial port"""
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            print("DMX port closed")

def run_basic_test():
    """Run basic DMX output test"""
    print("=== Basic DMX Output Test ===")
    
    dmx = BasicDMXController()
    
    if not dmx.open():
        return False
    
    try:
        # Test pattern: first 8 channels with different values
        test_pattern = [255, 128, 64, 32, 16, 8, 4, 2]
        
        print("Sending DMX test frames...")
        for i in range(10):
            dmx.send_frame(test_pattern)
            print(f"  Frame {i+1}/10 sent")
            time.sleep(0.04)  # 25 FPS refresh rate
            
        print("✓ Basic test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    finally:
        dmx.close()

def run_channel_sweep():
    """Test by sweeping through channels 1-16"""
    print("=== Channel Sweep Test ===")
    
    dmx = BasicDMXController()
    
    if not dmx.open():
        return False
    
    try:
        channels = [0] * 512
        
        print("Sweeping channels 1-16...")
        for ch in range(1, 17):
            # Clear previous channel
            if ch > 1:
                channels[ch-2] = 0
            
            # Set current channel to full
            channels[ch-1] = 255
            
            # Send frame
            dmx.send_frame(channels)
            print(f"  Channel {ch} ON")
            time.sleep(0.2)
        
        # Turn all off
        channels = [0] * 512
        dmx.send_frame(channels)
        print("  All channels OFF")
        
        print("✓ Channel sweep completed")
        return True
        
    except Exception as e:
        print(f"✗ Sweep test failed: {e}")
        return False
    finally:
        dmx.close()

def main():
    """Main test function"""
    print("WaveShare 2-CH RS485 HAT - DMX512 Test")
    print("=" * 50)
    
    # Test port access first
    if not test_port_access():
        print("Cannot proceed - port access failed")
        return
    
    # Run basic output test
    if run_basic_test():
        print("\n🎉 Basic DMX test PASSED!")
        
        # Ask for channel sweep test
        response = input("\nRun channel sweep test? (y/N): ").lower()
        if response in ['y', 'yes']:
            run_channel_sweep()
    else:
        print("\n❌ Basic DMX test FAILED")
        print("Check hardware connections and DIP switch settings")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. Connect DMX devices to test output")
    print("2. Configure DIP switches for your setup")
    print("3. Set terminal resistors if at end of DMX line")

if __name__ == "__main__":
    main()
