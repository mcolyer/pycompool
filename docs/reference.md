# PyCompool Library Reference

This document provides comprehensive reference documentation for LLMs using the PyCompool library to control Pentair/Compool LX3xxx pool and spa systems via RS-485 serial communication.

## Quick Start

```python
from pycompool import PoolController, PoolMonitor

# Create controller instance
controller = PoolController()

# Set pool temperature
controller.set_pool_temperature('80f')

# Set spa temperature  
controller.set_spa_temperature('104f')

# Set heater mode
controller.set_heater_mode('heater', 'pool')

# Control auxiliary equipment (smart toggle)
controller.set_aux_equipment(1, True)  # Turn on aux1 (only if currently off)

# Direct toggle operations
controller.toggle_aux_equipment(1)  # Always toggle aux1 regardless of state

# Get system status
status = controller.get_status()

# Start monitoring
monitor = PoolMonitor()
monitor.start(verbose=True)
```

## Core Classes

### PoolController

High-level interface for controlling Compool LX3xxx pool systems.

#### Constructor

```python
PoolController(port: Optional[str] = None, baud: Optional[int] = None)
```

**Parameters:**
- `port`: Serial port or URL (defaults to `COMPOOL_PORT` env var or `/dev/ttyUSB0`)
- `baud`: Baud rate (defaults to `COMPOOL_BAUD` env var or `9600`)

**Port Examples:**
- `/dev/ttyUSB0` - Linux USB serial adapter
- `COM3` - Windows serial port
- `socket://192.168.1.50:8899` - Network serial bridge
- `rfc2217://192.168.1.50:8899` - RFC2217 network serial

#### Methods

##### set_pool_temperature(temperature: str, verbose: bool = False) -> bool

Set the desired pool temperature.

**Parameters:**
- `temperature`: Temperature string like `'80f'` or `'26.7c'`
- `verbose`: Enable verbose packet output

**Returns:** `True` if ACK received, `False` otherwise

**Example:**
```python
success = controller.set_pool_temperature('80f')
```

##### set_spa_temperature(temperature: str, verbose: bool = False) -> bool

Set the desired spa temperature.

**Parameters:**
- `temperature`: Temperature string like `'104f'` or `'40c'`
- `verbose`: Enable verbose packet output

**Returns:** `True` if ACK received, `False` otherwise

##### set_heater_mode(mode: str, target: str, verbose: bool = False) -> bool

Set the heater/solar mode for pool or spa.

**Parameters:**
- `mode`: Heating mode - one of:
  - `'off'`: No heating allowed
  - `'heater'`: Heater on (will also use solar if available)
  - `'solar-priority'`: Solar priority (uses heater if solar unavailable)
  - `'solar-only'`: Solar only (no heating if solar unavailable)
- `target`: Target system - `'pool'` or `'spa'`
- `verbose`: Enable verbose packet output

**Returns:** `True` if ACK received, `False` otherwise

##### set_aux_equipment(aux_num: int, state: bool, verbose: bool = False) -> bool

Set the state of an auxiliary equipment circuit using intelligent toggle logic.

The hardware only supports toggling circuits, so this method reads the current state from heartbeat packets and only sends a toggle command if the current state differs from the desired state.

**Parameters:**
- `aux_num`: Auxiliary circuit number (1-8)
- `state`: `True` to turn on, `False` to turn off
- `verbose`: Enable verbose packet output

**Returns:** `True` if ACK received or no action needed, `False` if command failed

**Behavior:**
- Reads current aux state from heartbeat packet (`aux{N}_on` field)
- Only sends toggle command if current state ≠ desired state
- Returns `True` immediately if already in desired state (no-op)
- Shows status transition: `"Aux1 OFF → ON — ✓ ACK"`

**Example:**
```python
# Turn on aux1 (only if currently off)
success = controller.set_aux_equipment(1, True)

# Turn off aux2 with verbose output  
success = controller.set_aux_equipment(2, False, verbose=True)

# If aux1 is already on, this returns True immediately with no command sent
success = controller.set_aux_equipment(1, True)  # "Aux1 already ON — no action needed"
```

##### toggle_aux_equipment(aux_num: int, verbose: bool = False) -> bool

Toggle an auxiliary equipment circuit regardless of current state.

This method always sends a toggle command without checking current state, matching the Node.js reference implementation behavior.

**Parameters:**
- `aux_num`: Auxiliary circuit number (1-8)  
- `verbose`: Enable verbose packet output

**Returns:** `True` if ACK received, `False` otherwise

**Example:**
```python
# Always toggle aux1 (turns on if off, off if on)
success = controller.toggle_aux_equipment(1)

# Toggle aux3 with verbose packet output
success = controller.toggle_aux_equipment(3, verbose=True)
```

##### get_status(timeout: float = 10.0) -> Optional[dict]

Listen for a single heartbeat packet and return parsed status data.

**Parameters:**
- `timeout`: Maximum time to wait for heartbeat packet in seconds

**Returns:** Dictionary containing parsed heartbeat data, or `None` if no packet received

#### Properties

- `port`: Get the configured serial port
- `baud`: Get the configured baud rate

### PoolMonitor

Monitor for pool controller heartbeat packets sent every ~2.5 seconds.

#### Constructor

```python
PoolMonitor(port: Optional[str] = None, baud: Optional[int] = None)
```

Same parameters as `PoolController`.

#### Methods

##### start(verbose: bool = False) -> None

Start monitoring heartbeat packets until Ctrl-C is pressed.

**Parameters:**
- `verbose`: Enable verbose debug output showing raw packet data

### SerialConnection

Low-level serial connection management with RS-485 support.

#### Constructor

```python
SerialConnection(port: Optional[str] = None, baud: Optional[int] = None)
```

#### Methods

##### send_packet(packet_data: bytes, ack_timeout: float = 2.0) -> bool

Send a packet and wait for ACK response.

##### read_packets(packet_size: int = 24, timeout: float = 1.0) -> Generator[bytes, None, None]

Generator that yields packets as they are received.

## Heartbeat Packet Structure

The controller sends 24-byte heartbeat packets every ~2.5 seconds containing system status. The parsed packet contains the following fields:

### Packet Format

| Byte | Field | Description |
|------|-------|-------------|
| 0-1 | Sync | Always `0xFF 0xAA` |
| 2 | Destination | Always `0x0F` |
| 3 | Version | Firmware version (e.g., 10 = v1.0) |
| 4 | Opcode | Always `0x02` |
| 5 | Length | Always `0x10` (16 bytes data) |
| 6 | Minutes | Current time minutes (0-59) |
| 7 | Hours | Current time hours (0-23) |
| 8 | Primary Equipment | Equipment state bits |
| 9 | Secondary Equipment | System state bits |
| 10 | Heat Source | Heat source configuration |
| 11 | Pool Water Temp | Pool water temperature (0.25°C increments) |
| 12 | Pool Solar Temp | Pool solar temperature (0.5°C increments) |
| 13 | Spa Water Temp | Spa water temperature (0.25°C increments, 3830 only) |
| 14 | Spa Solar Temp | Spa solar temperature (0.5°C increments, 3830 only) |
| 15 | Desired Pool Temp | Desired pool temperature (0.25°C increments) |
| 16 | Desired Spa Temp | Desired spa temperature (0.25°C increments) |
| 17 | Air Temperature | Air temperature (0.5°C increments) |
| 18-19 | Reserved | Spare/future use |
| 20 | Equipment Status | Equipment and sensor status |
| 21 | Product Type | Product type and additional status |
| 22-23 | Checksum | 16-bit checksum |

### Parsed Heartbeat Fields

When using `parse_heartbeat_packet()` or `get_status()`, the following fields are available:

#### Basic Information
- `type`: Always `PacketType.HEARTBEAT`
- `version`: Firmware version number
- `time`: Current time as `"HH:MM"` string

#### Equipment State (Primary Equipment - Byte 8)
Bit values indicate if circuits are ON (1) or OFF (0):

**Parsed Fields:**
- `aux1_on`: Auxiliary circuit 1 state (boolean)
- `aux2_on`: Auxiliary circuit 2 state (boolean)
- `aux3_on`: Auxiliary circuit 3 state (boolean)
- `aux4_on`: Auxiliary circuit 4 state (boolean)
- `aux5_on`: Auxiliary circuit 5 state (boolean)
- `aux6_on`: Auxiliary circuit 6 state (boolean)
- `aux7_on`: Auxiliary circuit 7 state (boolean)
- `aux8_on`: Auxiliary circuit 8 state (boolean)

**3820 Systems (Current Implementation):**
- Bit 0: Aux1 state
- Bit 1: Aux2 state
- Bit 2: Aux3 state
- Bit 3: Aux4 state
- Bit 4: Aux5 state
- Bit 5: Aux6 state
- Bit 6: Aux7 state
- Bit 7: Aux8 state

**Alternative System Layouts:**
- **3x00/3830**: Spa/Pool in bits 0-1, Aux1-Aux6 in bits 2-7
- **3810**: High/Low temp in bits 0-1, Aux1-Aux6 in bits 2-7

#### System State (Secondary Equipment - Byte 9)
- `primary_equip`: Raw primary equipment byte as hex string
- `secondary_equip`: Raw secondary equipment byte as hex string
- `service_mode`: Service mode active (boolean)
- `heater_on`: Pool heater active (boolean)
- `solar_on`: Pool solar active (boolean)
- `remotes_enabled`: Spa-side remotes enabled (boolean)
- `freeze_mode`: Freeze protection active (boolean)

**Secondary Equipment Bit Details:**
- Bit 0: Service mode (1 = ON, all commands ignored)
- Bit 1: Heater state (1 = ON, pool heater for 3830)
- Bit 2: Solar state (1 = ON, pool solar for 3830)
- Bit 3: Remotes enable (1 = ON, spa-side remote enabled)
- Bit 4: C/F display toggle (1 = Celsius, 0 = Fahrenheit)
- Bit 5: Solar present (1 = YES, pool solar present for 3830)
- Bit 6: Aux7 state (1 = ON)
- Bit 7: Freeze mode (1 = ON, protective freeze mode)

#### Heat Source Configuration (Byte 10)
Heat source settings use bits 4-7:
- Bits 4-5: Pool heat source
- Bits 6-7: Spa heat source

**Heat Source Values:**
- `00`: Heat source OFF (no heating)
- `01`: Heater ON (will use solar if available)
- `10`: Solar Priority (uses heater if solar unavailable)
- `11`: Solar Only (no heating if solar unavailable)

#### Temperature Fields
All temperatures provided in both Celsius and Fahrenheit:

- `pool_water_temp`: Pool water temperature (°C)
- `pool_water_temp_f`: Pool water temperature (°F)
- `pool_solar_temp`: Pool solar temperature (°C)
- `spa_water_temp`: Spa water temperature (°C, 3830 only)
- `spa_water_temp_f`: Spa water temperature (°F, 3830 only)
- `spa_solar_temp`: Spa solar temperature (°C, 3830 only)
- `desired_pool_temp`: Desired pool temperature (°C)
- `desired_pool_temp_f`: Desired pool temperature (°F)
- `desired_spa_temp`: Desired spa temperature (°C)
- `desired_spa_temp_f`: Desired spa temperature (°F)
- `air_temp`: Air temperature (°C)
- `air_temp_f`: Air temperature (°F)

**Temperature Encoding:**
- Water temperatures: 0.25°C increments (byte value ÷ 4)
- Solar temperatures: 0.5°C increments (byte value ÷ 2)
- Air temperature: 0.5°C increments (byte value ÷ 2)
- Range: 0-255 byte values (0-63.75°C for water, 0-127.5°C for solar/air)

#### Equipment and Sensor Status (Byte 20)
- Bit 0: Backwash state (1 = ON, programmed backwash cycle active)
- Bit 1: Floor cleaner (1 = ON, floor cleaner system active)
- Bit 2: Aux3 dimmer (1 = YES, Aux3 configured as dimmer)
- Bit 3: Aux4 dimmer (1 = YES, Aux4 configured as dimmer)
- Bit 4: Water sensor (1 = OK, water sensor functioning)
- Bit 5: Solar sensor (1 = OK, solar sensor functioning)
- Bit 6: Air sensor (1 = OK, freeze sensor functioning)
- Bit 7: Freeze present (1 = YES, freeze protection configured)

#### Product Type and Status (Byte 21)
- Bit 0: Error 5 (1 = TRUE, spa-side remote error, disabled)
- Bit 1: Error 6 (1 = TRUE, not used)
- Bit 2: Spa heater (1 = ON, 3830 only)
- Bit 3: Spa solar (1 = ON, 3830 only)
- Bits 4-7: Product type identifier

**Product Type Values:**
- `0000` (0): 3400 System
- `0010` (2): 3410 System (not used)
- `0100` (4): 3600 System
- `0110` (6): 3610 System (not used)
- `1000` (8): 3800 System
- `1010` (10): 3810 System
- `1100` (12): 3820 System
- `1110` (14): 3830 System

## Auxiliary Equipment Protocol Details

### Toggle-Based Hardware Protocol

The Compool LX3xxx controllers use a **toggle-based protocol** for auxiliary equipment control, not absolute ON/OFF commands. Understanding this is crucial for proper implementation:

**How Toggle Protocol Works:**
1. **Command packets contain toggle bits** - Set bits indicate "toggle these circuits"
2. **Hardware toggles the specified circuits** - ON circuits turn OFF, OFF circuits turn ON  
3. **No absolute state setting** - You cannot directly set "all circuits to this exact state"

**Packet Format for Aux Commands:**
- **Primary Equipment Byte (byte 8)**: Contains toggle bits for aux1-aux8
- **Enable Bits (byte 14)**: Bit 2 must be set to enable primary equipment field
- **Only set bits for circuits to toggle** - Leave other bits as 0

**Example Toggle Commands:**
```python
# Toggle aux1 only (bit 0)
primary_equip = 0x01  # Binary: 00000001
enable_bits = 0x04    # Bit 2 set

# Toggle aux3 only (bit 2) 
primary_equip = 0x04  # Binary: 00000100
enable_bits = 0x04    # Bit 2 set

# Toggle aux1 and aux4 simultaneously (bits 0 and 3)
primary_equip = 0x09  # Binary: 00001001
enable_bits = 0x04    # Bit 2 set
```

**Why Smart Toggle Logic is Needed:**
Since hardware only supports toggling, the library implements intelligent behavior:
1. **Read current state** from heartbeat packets (`aux1_on`, `aux2_on`, etc.)
2. **Compare with desired state** to determine if toggle is needed
3. **Send toggle command** only if current ≠ desired
4. **Skip command** if already in desired state (no-op)

This provides the expected "set to ON/OFF" behavior while working with toggle-only hardware.

## Protocol Functions

### Temperature Conversion

```python
# Convert temperature string to celsius
celsius = tempstr_to_celsius('80f')  # Returns 26.67

# Convert celsius to protocol byte
byte_val = celsius_to_byte(26.67)  # Returns 107

# Convert protocol byte to celsius
celsius = byte_to_celsius(107)  # Returns 26.75

# Convert celsius to fahrenheit
fahrenheit = celsius_to_fahrenheit(26.67)  # Returns 80.0
```

### Packet Creation and Parsing

```python
# Create command packet for temperature
packet = create_command_packet(
    pool_temp=celsius_to_byte(26.67),  # 80°F
    enable_bits=1 << 5  # Enable pool temperature field
)

# Create command packet for auxiliary equipment (toggle aux3)
packet = create_command_packet(
    primary_equip=0x04,  # Toggle aux3 (bit 2 set)
    enable_bits=1 << 2   # Enable primary equipment field (bit 2)
)

# Parse heartbeat packet
parsed = parse_heartbeat_packet(raw_packet_bytes)
if parsed:
    print(f"Pool temp: {parsed['pool_water_temp_f']:.1f}°F")
    for i in range(1, 9):  # aux1-aux8
        aux_status = "ON" if parsed.get(f'aux{i}_on', False) else "OFF"
        print(f"Aux{i}: {aux_status}")
```

## Environment Variables

- `COMPOOL_PORT`: Serial device or PySerial URL (default: `/dev/ttyUSB0`)
- `COMPOOL_BAUD`: Baud rate (default: `9600`)

## Error Handling

### Connection Errors
```python
from pycompool import ConnectionError

try:
    controller = PoolController()
    controller.set_pool_temperature('80f')
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

### Protocol Errors
```python
from pycompool import ProtocolError

try:
    celsius = tempstr_to_celsius('invalid')
except ValueError as e:
    print(f"Invalid temperature format: {e}")
```

## Command Line Interface

The library includes a CLI tool `compoolctl`:

```bash
# Set temperatures
compoolctl set-pool 80f
compoolctl set-spa 104f --verbose

# Set heater modes
compoolctl set-heater heater pool
compoolctl set-heater solar-only spa

# Control auxiliary equipment (smart toggle - only sends command if needed)
compoolctl set-aux aux1 on      # Turn on aux1 (only if currently off)
compoolctl set-aux aux2 off --verbose  # Turn off aux2 (only if currently on)

# Monitor heartbeat packets
compoolctl monitor --verbose

# Use custom port
compoolctl set-pool 80f --port socket://192.168.1.50:8899
```

## Common Usage Patterns

### Basic Temperature Control
```python
controller = PoolController()

# Set pool to 80°F
if controller.set_pool_temperature('80f'):
    print("Pool temperature set successfully")

# Set spa to 104°F
if controller.set_spa_temperature('104f'):
    print("Spa temperature set successfully")
```

### Heater Management
```python
# Enable pool heater
controller.set_heater_mode('heater', 'pool')

# Enable spa solar-only heating
controller.set_heater_mode('solar-only', 'spa')

# Turn off pool heating
controller.set_heater_mode('off', 'pool')
```

### Auxiliary Equipment Control
```python
# Smart toggle - only sends command if current state differs from desired
controller.set_aux_equipment(1, True)   # Turn on aux1 (only if off)
controller.set_aux_equipment(3, True)   # Turn on aux3 (only if off)

# Turn off auxiliary equipment
controller.set_aux_equipment(2, False)  # Turn off aux2 (only if on)

# Direct toggle - always sends toggle command
controller.toggle_aux_equipment(1)      # Always toggle aux1
controller.toggle_aux_equipment(4)      # Always toggle aux4

# Check result (True = success or no-op, False = command failed)
if controller.set_aux_equipment(1, True):
    print("Aux1 is now on (or was already on)")

# Get status to see what actually happened
status = controller.get_status()
if status:
    aux1_state = "ON" if status.get('aux1_on', False) else "OFF"
    print(f"Aux1 is currently {aux1_state}")
```

### Status Monitoring
```python
# Get current status
status = controller.get_status()
if status:
    print(f"Pool: {status['pool_water_temp_f']:.1f}°F")
    print(f"Spa: {status['spa_water_temp_f']:.1f}°F")
    print(f"Heater: {'ON' if status['heater_on'] else 'OFF'}")
    print(f"Solar: {'ON' if status['solar_on'] else 'OFF'}")
    
    # Check auxiliary equipment status
    for i in range(1, 9):  # aux1-aux8
        aux_status = "ON" if status.get(f'aux{i}_on', False) else "OFF"
        print(f"Aux{i}: {aux_status}")
```

### Continuous Monitoring
```python
# Start real-time monitoring
monitor = PoolMonitor()
monitor.start(verbose=True)  # Press Ctrl-C to stop
```

### Network Serial Connections
```python
# Connect via network serial bridge
controller = PoolController(port='socket://192.168.1.50:8899')
controller.set_pool_temperature('80f')
```

## Troubleshooting

### Common Issues

1. **No ACK Response**: Check serial connection, baud rate, and RS-485 adapter
2. **Parse Errors**: Verify packet sync bytes (`0xFF 0xAA`) and checksum
3. **Temperature Conversion**: Use proper format (`'80f'` or `'26.7c'`)
4. **Network Delays**: Use longer timeouts for network serial bridges
5. **Buffered Packets**: Monitor reads 24-byte chunks to handle buffering
6. **Aux Equipment Not Responding**: 
   - Ensure you're using the correct toggle protocol (enable bit 2, not bit 0)
   - Verify current state reading from heartbeat packets
   - Use `toggle_aux_equipment()` to test direct toggle commands
7. **Unexpected Aux Behavior**:
   - Remember hardware only supports toggling, not absolute states
   - Use `get_status()` to verify actual equipment state after commands
   - Check for "no action needed" messages when already in desired state

### Debug Output
Enable verbose mode to see raw packet data:
```python
controller.set_pool_temperature('80f', verbose=True)
# Output: → ff aa 00 01 82 09 00 00 00 00 00 6b 00 00 20 03 17

monitor.start(verbose=True)
# Shows packet timing and content
```

### Serial Connection Issues
- Ensure proper RS-485 adapter with 1000Ω termination
- Check RJ45 pinout: Pin 3 (+Data), Pin 4 (-Data)
- Verify controller is powered and responding
- Test with different timeout values for network bridges