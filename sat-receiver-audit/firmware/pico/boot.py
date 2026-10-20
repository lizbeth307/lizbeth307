"""Safe states before application imports. Requires genuine non-wireless Pico."""
from machine import Pin

Pin(17, Pin.OUT, value=1)   # Assert common MCP RESET via Q306, never LOW at boot.
Pin(16, Pin.OUT, value=0)   # Display supply OFF.
Pin(18, Pin.OUT, value=1)   # DC fan ON; no PWM on this three-wire fan.
Pin(19, Pin.OUT, value=1)   # Two-wire blower ON.
Pin(13, Pin.OUT, value=0)   # No unintended Pololu OFF pulse.
Pin(12, Pin.OUT, value=0)   # PMIC key transistor OFF.
Pin(20, Pin.OUT, value=0)   # Piezo silent.
Pin(21, Pin.OUT, value=1)   # Safe/fault indicator.
Pin(0, Pin.IN)             # Q6A-bound TX high impedance until its 3V3 is present.
Pin(1, Pin.IN)
Pin(8, Pin.IN)             # IMU UART not implemented; do not send unframed bytes.
Pin(9, Pin.IN)
Pin(15, Pin.IN)            # SAFE_BOOT also high impedance while Q6A is off.
