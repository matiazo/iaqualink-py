# Home Assistant ICL Light RGB Color Support - Installation Instructions

## Problem

Your ICL lights show up in Home Assistant with only brightness control (no color picker) because the Home Assistant `iaqualink` integration doesn't check for RGB color support when determining the color mode.

## Solution

You need to update the Home Assistant integration's `light.py` file to detect and use RGB/RGBW color modes.

## Installation Steps

### Option 1: Custom Component (Recommended for Testing)

1. **Connect to your Home Assistant instance:**
   - If using SSH: `ssh user@your-ha-ip`
   - If using Docker exec: `docker exec -it homeassistant bash`
   - If using File Editor addon: Use the web UI

2. **Create custom component directory:**
   ```bash
   mkdir -p /config/custom_components/iaqualink
   ```

3. **Copy the updated light.py file:**
   - The file is in your repo: `homeassistant_integration_light.py`
   - Copy it to: `/config/custom_components/iaqualink/light.py`

4. **Copy other required files from the built-in integration:**
   ```bash
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/__init__.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/manifest.json /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/entity.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/utils.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/binary_sensor.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/climate.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/sensor.py /config/custom_components/iaqualink/
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/switch.py /config/custom_components/iaqualink/
   ```

5. **Restart Home Assistant:**
   - Developer Tools → Restart
   - Or: `docker restart homeassistant`

6. **Verify:**
   - Go to your ICL light in Home Assistant
   - You should now see the full color picker

### Option 2: Direct Edit (Advanced)

1. **Backup the original file:**
   ```bash
   cp /usr/src/homeassistant/homeassistant/components/iaqualink/light.py \
      /usr/src/homeassistant/homeassistant/components/iaqualink/light.py.backup
   ```

2. **Replace the file:**
   - Copy `homeassistant_integration_light.py` content to `/usr/src/homeassistant/homeassistant/components/iaqualink/light.py`

3. **Restart Home Assistant**

## What Changed

The updated `light.py` file now:

1. **Detects RGB/RGBW color modes:**
   ```python
   color_mode = ColorMode.ONOFF
   if dev.supports_rgb_color and dev.supports_white_value:
       color_mode = ColorMode.RGBW
   elif dev.supports_rgb_color:
       color_mode = ColorMode.RGB
   elif dev.supports_brightness:
       color_mode = ColorMode.BRIGHTNESS
   ```

2. **Adds RGB color properties:**
   - `rgb_color`: Returns device RGB color
   - `rgbw_color`: Returns device RGBW color (if white value supported)
   - `white_value`: Returns device white value

3. **Handles RGB color commands:**
   - `async_turn_on()` now handles `ATTR_RGB_COLOR`, `ATTR_RGBW_COLOR`, and `ATTR_WHITE_VALUE`

## Testing

After installation and restart:

1. Open your ICL light in Home Assistant
2. You should see:
   - Brightness slider ✓
   - Color picker (full color wheel) ✓
   - White value slider (if RGBW mode) ✓
   - Effect selector ✓

3. Test each feature:
   - Change color → Light should change
   - Change brightness → Light should dim/brighten
   - Change white value → White LEDs should adjust

## Troubleshooting

### Color picker still not showing

1. **Check Home Assistant logs:**
   ```
   Settings → System → Logs
   ```
   Look for errors related to "iaqualink" or "light"

2. **Verify the device properties:**
   - Developer Tools → States
   - Find your light entity (e.g., `light.pool_lights`)
   - Check `supported_color_modes` attribute
   - Should show: `["rgb"]` or `["rgbw"]`

3. **Force reload the integration:**
   ```
   Settings → Devices & Services → iaqualink → ⋮ → Reload
   ```

### Custom component not loading

1. **Check manifest.json version:**
   - Open `/config/custom_components/iaqualink/manifest.json`
   - Ensure `"version"` matches your iaqualink-py library version

2. **Check Home Assistant logs for import errors**

3. **Verify all required files are copied**

## Next Steps

Once you verify this works, you should:

1. **Contribute to Home Assistant:** Submit a PR to add RGB support to the official iaqualink integration
2. **Update iaqualink-py version:** Update manifest.json to use your fork with ICL support
3. **Document ICL support:** Add ICL light documentation to both repos

## Files Modified

- `homeassistant_integration_light.py` (this repo) → Copy to Home Assistant as `light.py`
