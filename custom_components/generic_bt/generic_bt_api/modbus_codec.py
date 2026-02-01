"""Modbus-RTU codec for SRNE Inverter."""

def calculate_crc16(data):
    """Standard CRC-16 (Modbus) check."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def build_read_request(slave_id, address, count):
    """Build a Modbus-RTU read request (Function Code 03H)."""
    frame = bytearray([
        slave_id,
        0x03,
        (address >> 8) & 0xFF,
        address & 0xFF,
        (count >> 8) & 0xFF,
        count & 0xFF
    ])
    crc = calculate_crc16(frame)
    frame.append(crc & 0xFF)
    frame.append((crc >> 8) & 0xFF)
    return bytes(frame)

def build_write_request(slave_id, address, value):
    """Build a Modbus-RTU write single register request (Function Code 06H)."""
    frame = bytearray([
        slave_id,
        0x06,
        (address >> 8) & 0xFF,
        address & 0xFF,
        (value >> 8) & 0xFF,
        value & 0xFF
    ])
    crc = calculate_crc16(frame)
    frame.append(crc & 0xFF)
    frame.append((crc >> 8) & 0xFF)
    return bytes(frame)

def parse_response(data, slave_id, function_code):
    """Parse a Modbus-RTU response."""
    if len(data) < 5:
        raise ValueError("Response too short")

    # Verify CRC
    received_crc = data[-2] | (data[-1] << 8)
    calculated_crc = calculate_crc16(data[:-2])
    if received_crc != calculated_crc:
        raise ValueError(f"CRC mismatch")

    if data[0] != slave_id:
        raise ValueError(f"Slave ID mismatch")

    if data[1] != function_code:
        # Check for error code
        if data[1] == (function_code | 0x80):
            error_code = data[2]
            raise ValueError(f"Modbus error: {error_code}")
        raise ValueError(f"Function code mismatch")

    if function_code == 0x03:
        byte_count = data[2]
        if len(data) != byte_count + 5:
            raise ValueError("Data length mismatch")

        registers = []
        for i in range(0, byte_count, 2):
            registers.append((data[3 + i] << 8) | data[4 + i])
        return registers

    elif function_code == 0x06:
        # For write single register, response is a copy of request
        address = (data[2] << 8) | data[3]
        value = (data[4] << 8) | data[5]
        return [address, value]

    return []
