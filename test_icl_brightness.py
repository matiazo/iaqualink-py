#!/usr/bin/env python3
"""Test ICL brightness control with visual feedback."""

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
    print("ICL Brightness Test - Watch Your Lights!")
    print("=" * 60)
    
    # Login
    print("\n[1/2] Logging in...")
    async with AqualinkClient(username, password) as client:
        await client.login()
        print(f"    OK - Session ID: {client.client_id[:20]}...")
        
        # Get systems
        print("\n[2/2] Getting system...")
        systems = await client.get_systems()
        if not systems or len(systems) == 0:
            print("    ERROR: No systems found")
            return 1
        
        system = list(systems.values())[0]
        await system.update()
        
        # Find ICL lights
        icl_lights = [d for d in system.devices.values() 
                     if d.__class__.__name__ == 'IaquaICLLight']
        
        if not icl_lights:
            print("    ERROR: No ICL lights found")
            return 1
        
        light = icl_lights[0]
        zone_id = light.zone_id
        
        print(f"\n    Found ICL light: Zone {zone_id} - {light.zone_name}")
        print("\n" + "=" * 60)
        print("Starting Brightness Test Sequence")
        print("Watch your pool lights - they should change brightness")
        print("=" * 60)
        
        # Set to RED first so it's clearly visible
        print(f"\n[Step 1] Setting light to RED (255, 0, 0)...")
        try:
            await light.set_rgb_color(255, 0, 0)
            await asyncio.sleep(2)
            print("    OK - Light should now be RED")
        except Exception as e:
            print(f"    ERROR: {e}")
            return 1
        
        # Turn ON if not already
        print(f"\n[Step 2] Ensuring light is ON...")
        try:
            await light.turn_on()
            await asyncio.sleep(2)
            print("    OK - Light is ON")
        except Exception as e:
            print(f"    ERROR: {e}")
        
        # Test brightness levels - increasing from dim to bright
        brightness_levels = [25, 50, 75, 100]
        
        print(f"\n[Step 3] Testing brightness levels (watch the light!)...")
        print("    The light should get progressively BRIGHTER")
        print()
        
        for i, brightness in enumerate(brightness_levels, 1):
            print(f"    [{i}/{len(brightness_levels)}] Setting brightness to {brightness}%...")
            try:
                await light.set_brightness(brightness)
                print(f"        -> Brightness command sent: {brightness}%")
                print(f"        -> Waiting 3 seconds (watch the light change)...")
                await asyncio.sleep(3)
                
                # Update system to see new state
                await system.update()
                current_brightness = system.devices[f'icl_zone_{zone_id}'].brightness
                print(f"        -> Current brightness from API: {current_brightness}%")
                print()
            except Exception as e:
                print(f"        ERROR: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # Now decrease brightness
        print(f"\n[Step 4] Testing decreasing brightness (watch it dim)...")
        print("    The light should get progressively DIMMER")
        print()
        
        brightness_levels_down = [75, 50, 25]
        
        for i, brightness in enumerate(brightness_levels_down, 1):
            print(f"    [{i}/{len(brightness_levels_down)}] Setting brightness to {brightness}%...")
            try:
                await light.set_brightness(brightness)
                print(f"        -> Brightness command sent: {brightness}%")
                print(f"        -> Waiting 3 seconds (watch the light change)...")
                await asyncio.sleep(3)
                
                # Update system to see new state
                await system.update()
                current_brightness = system.devices[f'icl_zone_{zone_id}'].brightness
                print(f"        -> Current brightness from API: {current_brightness}%")
                print()
            except Exception as e:
                print(f"        ERROR: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # Return to full brightness
        print(f"\n[Step 5] Returning to full brightness (100%)...")
        try:
            await light.set_brightness(100)
            await asyncio.sleep(2)
            print("    OK - Back to full brightness")
        except Exception as e:
            print(f"    ERROR: {e}")
        
        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print("\nDid you see the light change brightness?")
        print("  - YES: Brightness control is working!")
        print("  - NO: There may be an issue with the API")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
