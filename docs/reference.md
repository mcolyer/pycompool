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

**3x00/3830 Systems:**
- Bit 0: Spa state
- Bit 1: Pool state  
- Bit 2: Aux1 state
- Bit 3: Aux2 state
- Bit 4: Aux3 state
- Bit 5: Aux4 state
- Bit 6: Aux5 state
- Bit 7: Aux6 state

**3810 Systems (Single body, dual temperature):**
- Bit 0: High temperature circuit
- Bit 1: Low temperature circuit
- Bits 2-7: Aux1-Aux6

**3820 Systems:**
- Bits 0-7: Aux1-Aux8

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
# Create command packet
packet = create_command_packet(
    pool_temp=celsius_to_byte(26.67),  # 80°F
    enable_bits=1 << 5  # Enable pool temperature field
)

# Parse heartbeat packet
parsed = parse_heartbeat_packet(raw_packet_bytes)
if parsed:
    print(f"Pool temp: {parsed['pool_water_temp_f']:.1f}°F")
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

### Status Monitoring
```python
# Get current status
status = controller.get_status()
if status:
    print(f"Pool: {status['pool_water_temp_f']:.1f}°F")
    print(f"Spa: {status['spa_water_temp_f']:.1f}°F")
    print(f"Heater: {'ON' if status['heater_on'] else 'OFF'}")
    print(f"Solar: {'ON' if status['solar_on'] else 'OFF'}")
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