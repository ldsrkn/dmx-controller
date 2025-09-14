#!/usr/bin/env python3
"""
Safe DMX512 test script for WaveShare 2-CH RS485 HAT
Avoids problematic operations that can cause hanging
"""

import serial
import time
import sys

def test_basic_port_access():
    """Test basic port access without closing operations"""
    print("=== Basic Port Access Test ===")
    
    ports = ['/dev/ttySC0', '/dev/ttySC1']
    success_count = 0
    
    for port_name in ports:
        try:
            # Open with minimal timeout to avoid hanging
            ser = serial.Serial(
                port=port_name,
                baudrate=9600,
                timeout=0.01,
                write_timeout=0.01
            )
            print(f"✓ {port_name} - accessible")
            # Let Python garbage collector handle cleanup
            del ser
            success_count += 1
            
        except Exception as e:
            print(f"✗ {port_name} - error: {e}")
    
    if success_count == 2:
        print("✓ Both ports accessible")
        return True
    else:
        print("✗ Some ports failed")
        return False

def test_dmx_basic_output():
    """Test basic DMX output without baud rate manipulation"""
    print("\n=== Basic DMX Output Test ===")
    
    try:
        # Open DMX port with standard settings
        dmx_port = serial.Serial(
            port='/dev/ttySC0',
            baudrate=250000,  # Standard DMX512 baud rate
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=2,
            timeout=0.01,
            write_timeout=0.01
        )
        
        print("✓ DMX port opened successfully")
        print("  Port: /dev/ttySC0")
        print("  Baud: 250000")
        print("  Config: 8N2")
        
        # Create test DMX frame
        test_frame = bytearray(513)  # Start code + 512 channels
        test_frame[0] = 0x00  # DMX start code
        
        # Set some test channels
        test_frame[1] = 255   # Channel 1: Full brightness
        test_frame[2] = 128   # Channel 2: Half brightness  
        test_frame[3] = 64    # Channel 3: Quarter brightness
        test_frame[4] = 32    # Channel 4: Low brightness
        test_frame[5] = 255   # Channel 5: Full brightness
        test_frame[6] = 0     # Channel 6: Off
        test_frame[7] = 255   # Channel 7: Full brightness
        test_frame[8] = 0     # Channel 8: Off
        
        print("\nSending DMX test frames...")
        
        # Send multiple frames
        for frame_num in range(5):
            try:
                bytes_written = dmx_port.write(test_frame)
                dmx_port.flush()
                print(f"  Frame {frame_num + 1}: {bytes_written} bytes sent")
                time.sleep(0.04)  # 25 FPS refresh rate
                
            except Exception as e:
                print(f"  Frame {frame_num + 1}: Failed - {e}")
                break
        
        print("✓ DMX output test completed")
        
        # Let garbage collector handle cleanup
        del dmx_port
        return True
        
    except Exception as e:
        print(f"✗ DMX output test failed: {e}")
        return False

def test_pattern_output():
    """Send a recognizable pattern for testing with DMX devices"""
    print("\n=== Pattern Output Test ===")
    
    try:
        dmx_port = serial.Serial('/dev/ttySC0', 250000, 8, 'N', 2, timeout=0.01)
        print("✓ DMX port ready for pattern test")
        
        # Create different patterns
        patterns = [
            [255, 0, 0, 0],      # Red only
            [0, 255, 0, 0],      # Green only  
            [0, 0, 255, 0],      # Blue only
            [255, 255, 255, 0],  # White
            [0, 0, 0, 0]         # All off
        ]
        
        for i, pattern in enumerate(patterns):
            frame = bytearray(513)
            frame[0] = 0x00  # Start code
            
            # Apply pattern to first 4 channels
            for ch, value in enumerate(pattern):
                frame[ch + 1] = value
            
            dmx_port.write(frame)
            dmx_port.flush()
            
            pattern_name = ['Red', 'Green', 'Blue', 'White', 'Off'][i]
            print(f"  Pattern {i + 1}: {pattern_name} - sent")
            time.sleep(1.0)  # Hold each pattern for 1 second
        
        print("✓ Pattern test completed")
        del dmx_port
        return True
        
    except Exception as e:
        print(f"✗ Pattern test failed: {e}")
        return False

def check_system_info():
    """Display system information for debugging"""
    print("\n=== System Information ===")
    
    try:
        # Check if user is in dialout group
        import subprocess
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        
        if 'dialout' in groups:
            print("✓ User is in dialout group")
        else:
            print("✗ User NOT in dialout group")
            print("  Run: sudo usermod -a -G dialout $USER")
        
        # Check kernel driver
        try:
            with open('/proc/modules', 'r') as f:
                modules = f.read()
                if 'sc16is7xx' in modules:
                    print("✓ SC16IS7xx driver loaded")
                else:
                    print("✗ SC16IS7xx driver not found")
        except:
            print("? Could not check kernel modules")
            
        print(f"✓ Python serial library available")
        
    except Exception as e:
        print(f"✗ System check failed: {e}")

def main():
    """Main test sequence"""
    print("WaveShare 2-CH RS485 HAT - Safe DMX512 Test")
    print("=" * 50)
    
    # System information
    check_system_info()
    
    # Basic port test
    if not test_basic_port_access():
        print("\n❌ FAILED: Cannot access serial ports")
        print("\nTroubleshooting:")
        print("1. Check HAT is properly connected")
        print("2. Verify /boot/firmware/config.txt has: dtoverlay=sc16is752-spi1,int_pin=24")
        print("3. Ensure user is in dialout group")
        print("4. Try reboot if driver issues persist")
        return
    
    # DMX output test
    if test_dmx_basic_output():
        print("\n🎉 SUCCESS: Basic DMX output working!")
        
        # Ask for pattern test
        try:
            response = input("\nRun pattern test? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                test_pattern_output()
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        except:
            print("\nSkipping pattern test")
    else:
        print("\n❌ FAILED: DMX output not working")
        print("\nCheck:")
        print("1. DIP switches on HAT (try A=0, B=1 for auto mode)")
        print("2. Terminal resistors if at end of DMX line")
        print("3. Physical DMX connections")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. Connect actual DMX devices to test")
    print("2. Create full DMX controller scripts")
    print("3. Implement both OUT/IN and OUT/OUT modes")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
