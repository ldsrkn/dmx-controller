#!/usr/bin/env python3
"""
Working DMX512 controller for problematic SC16IS752 driver
Avoids flush() and explicit close() operations that cause hanging
"""

import serial
import time
import atexit

class WorkingDMXController:
    def __init__(self, port='/dev/ttySC0'):
        self.port = port
        self.dmx_port = None
        self.frame_count = 0
        
    def open(self):
        """Open DMX port with minimal settings"""
        try:
            self.dmx_port = serial.Serial(
                port=self.port,
                baudrate=250000,  # DMX standard
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=2,
                timeout=0.01,
                write_timeout=0.01
            )
            print(f"DMX port {self.port} opened successfully")
            return True
        except Exception as e:
            print(f"Failed to open {self.port}: {e}")
            return False
    
    def send_dmx_frame_simple(self, channels):
        """Send DMX frame without flush or close"""
        if not self.dmx_port:
            return False
            
        try:
            # Create DMX frame: start code + 512 channels
            frame = bytearray(513)
            frame[0] = 0x00  # DMX start code
            
            # Copy channel data
            for i, value in enumerate(channels[:512]):
                frame[i + 1] = int(value) & 0xFF
            
            # Send frame (no flush!)
            self.dmx_port.write(frame)
            self.frame_count += 1
            return True
            
        except Exception as e:
            print(f"Frame send error: {e}")
            return False
    
    def test_pattern(self):
        """Test with simple pattern"""
        if not self.open():
            return False
            
        print("Sending test pattern...")
        
        try:
            # Simple test pattern
            channels = [255, 128, 64, 32, 16, 8, 4, 2] + [0] * 504
            
            for i in range(10):
                if self.send_dmx_frame_simple(channels):
                    print(f"Frame {i+1}: sent")
                else:
                    print(f"Frame {i+1}: failed")
                    break
                time.sleep(0.04)  # 25 FPS
                
            print(f"Test completed. Sent {self.frame_count} frames total.")
            
            # Don't call close() - let Python handle cleanup
            return True
            
        except KeyboardInterrupt:
            print("Test interrupted")
            return False

def main():
    dmx = WorkingDMXController()
    dmx.test_pattern()

if __name__ == "__main__":
    main()