#!/usr/bin/env python3
"""Test ICL light control using v1 API commands from GitHub issue #39."""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import iaqualink
sys.path.insert(0, str(Path(__file__).parent / "src"))

from iaqualink.client import AqualinkClient


async def main():
    # Read credentials
    creds_file = Path(__file__).parent / ".credentials"
    if not creds_file.exists():
        print("ERROR: .credentials file not found")
        print("Create a file named .credentials with format: username|password")
        return 1
    
    username, password = creds_file.read_text().strip().split("|")
    
    print("=" * 60)
    print("ICL Light Control Test - v1 API (GitHub issue #39)")
    print("=" * 60)
    
    # Login
    print("\n[1/6] Logging in...")
    async with AqualinkClient(username, password) as client:
        await client.login()
        print(f"    OK - Session ID: {client.client_id[:20]}...")
        
        # Get systems
        print("\n[2/6] Getting systems...")
        systems = await client.get_systems()
        if not systems or len(systems) == 0:
            print("    ERROR: No systems found")
            return 1
        
        system = list(systems.values())[0]
        print(f"    OK - Found system: {system.serial}")
        
        # Update to get devices
        print("\n[3/6] Updating system state...")
        await system.update()
        print(f"    OK - Found {len(system.devices)} devices")
        
        # Find ICL lights
        print("\n[4/6] Looking for ICL lights...")
        icl_lights = [d for d in system.devices.values() 
                     if d.__class__.__name__ == 'IaquaICLLight']
        
        if not icl_lights:
            print("    ERROR: No ICL lights found")
            print("\n    Available devices:")
            for name, device in system.devices.items():
                print(f"      - {name}: {device.__class__.__name__}")
            return 1
        
        print(f"    OK - Found {len(icl_lights)} ICL light(s)")
        for light in icl_lights:
            print(f"      - Zone {light.zone_id}: {light.zone_name}")
            print(f"        Status: {light.data.get('zoneStatus', 'unknown')}")
            print(f"        RGB: {light.rgb_color}")
            print(f"        Brightness: {light.brightness}%")
            print(f"        zoneColor: {light.data.get('zoneColor', 'unknown')}")
            print(f"        Full data: {light.data}")
        
        # Test turning light on/off
        light = icl_lights[0]
        zone_id = light.zone_id
        
        print(f"\n[5/6] Testing ICL light control (Zone {zone_id})...")
        
        # Test turn OFF
        print(f"\n    [a] Turning OFF zone {zone_id}...")
        try:
            await light.turn_off()
            print("        OK - Command sent successfully")
            await asyncio.sleep(2)
            await system.update()
            new_status = system.devices[f'icl_zone_{zone_id}'].data.get('zoneStatus', 'unknown')
            print(f"        Status after command: {new_status}")
        except Exception as e:
            print(f"        ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Test turn ON
        print(f"\n    [b] Turning ON zone {zone_id}...")
        try:
            await light.turn_on()
            print("        OK - Command sent successfully")
            await asyncio.sleep(2)
            await system.update()
            new_status = system.devices[f'icl_zone_{zone_id}'].data.get('zoneStatus', 'unknown')
            print(f"        Status after command: {new_status}")
        except Exception as e:
            print(f"        ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Test custom color
        print(f"\n    [c] Setting custom color (Magenta - RGB 255,0,255)...")
        try:
            await light.set_rgb_color(255, 0, 255)
            print("        OK - Command sent successfully")
            await asyncio.sleep(2)
            await system.update()
            new_rgb = system.devices[f'icl_zone_{zone_id}'].rgb_color
            print(f"        RGB after command: {new_rgb}")
        except Exception as e:
            print(f"        ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Test brightness
        print(f"\n    [d] Setting brightness to 50%...")
        try:
            await light.set_brightness(50)
            print("        OK - Command sent successfully")
            await asyncio.sleep(2)
            await system.update()
            new_brightness = system.devices[f'icl_zone_{zone_id}'].brightness
            print(f"        Brightness after command: {new_brightness}%")
        except Exception as e:
            print(f"        ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n[6/6] Test complete!")
        print("\n" + "=" * 60)
        print("Summary:")
        print("  - If all commands show 'OK', the v1 API is working!")
        print("  - Check your physical lights to confirm they respond")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
