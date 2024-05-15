import math
from bleak import BleakClient, BleakScanner


class BTSender:
    def __init__(
        self,
        device_name,
        SERVICE_UUID="FFE0",
        CHARACTERISTIC_UUID="FFE1",
        max_motor_speed=255,
    ):
        self.device_name = device_name
        self.max_motor_speed = max_motor_speed
        self.SERVICE_UUID = SERVICE_UUID
        self.CHARACTERISTIC_UUID = CHARACTERISTIC_UUID
        self.client = None

    async def connect(self):
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == self.device_name:
                self.client = BleakClient(device.address)
                return await self.client.connect()
        print("Did not find bluetooth name: ", self.device_name)
        return False
    
    def is_connected(self):
        return self.client and self.client.is_connected

    def angle_throttle_to_motor_speeds(self, angle, throttle):
        angle_rad = math.radians(angle)
        right_multiplier = math.cos(angle_rad) - math.sin(angle_rad)
        left_multiplier = math.cos(angle_rad) + math.sin(angle_rad)
        # Normalize multipliers to ensure maximum motor speed is not exceeded
        max_multiplier = max(abs(left_multiplier), abs(right_multiplier))
        left_multiplier /= max_multiplier
        right_multiplier /= max_multiplier
        # Apply throttle and limit to maximum motor speed
        left_speed = int(left_multiplier * throttle * self.max_motor_speed)
        right_speed = int(right_multiplier * throttle * self.max_motor_speed)
        return left_speed, right_speed

    async def send_bluetooth_message(self, message):
        await self.client.write_gatt_char(self.CHARACTERISTIC_UUID, message.encode())

    async def update_speed(self, angle, throttle):
        if self.client and self.client.is_connected:
            left_speed, right_speed = self.angle_throttle_to_motor_speeds(
                angle, throttle
            )
            assert (
                left_speed <= self.max_motor_speed
                and right_speed <= self.max_motor_speed
            )
            message = f"A#{left_speed}#{right_speed}#\n"
            await self.send_bluetooth_message(message)
        else:
            print("Client not connected.")

    async def stop(self):
        if self.client and self.client.is_connected:
            message = "B#\n"
            await self.send_bluetooth_message(message)
        else:
            print("Client not connected.")

    async def horn(self, val):
        if self.client and self.client.is_connected:
            assert val <= 2000
            message = f"D#{val}#\n"
            await self.send_bluetooth_message(message)
        else:
            print("Client not connected.")

    async def led(self, strip, rgb):
        if self.client and self.client.is_connected:
            message = f"C#{strip}#{rgb[0]}#{rgb[1]}#{rgb[2]}#\n"
            await self.send_bluetooth_message(message)
        else:
            print("Client not connected.")

    async def get_voltage(self):
        if self.client and self.client.is_connected:
            message = "I# /I#4100#\n"
            await self.send_bluetooth_message(message)
        else:
            print("Client not connected.")
