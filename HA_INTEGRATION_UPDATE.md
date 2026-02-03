# Home Assistant Integration Update - RGB Color Support

## What Was Done

Successfully updated the Home Assistant iaqualink custom integration to support RGB/RGBW color modes for ICL lights.

## Files Modified

### 1. `ha_custom_component/light.py`
- **Added imports**: `ATTR_RGB_COLOR`, `ATTR_RGBW_COLOR`, `ATTR_WHITE_VALUE`
- **Updated `__init__` method**: Now detects RGB/RGBW color modes based on device capabilities
  - Priority: RGBW > RGB > BRIGHTNESS > ONOFF
  - Checks `dev.supports_rgb_color` and `dev.supports_white_value`
- **Updated `async_turn_on` method**: Now handles RGB/RGBW color commands
  - RGB color setting via `set_rgb_color(red, green, blue)`
  - RGBW color setting via `set_rgb_color()` + `set_white_value()`
  - White value adjustment
  - Maintains backward compatibility with effects and brightness
- **Added properties**:
  - `rgb_color`: Returns current RGB color tuple
  - `rgbw_color`: Returns current RGBW color tuple (if white supported)
  - `white_value`: Returns current white value
- **Fixed `brightness` property**: Now returns `None` if brightness not available

## Scripts Created

### `copy_from_server.ps1`
Downloads the current iaqualink custom integration from your Home Assistant server.
```powershell
.\copy_from_server.ps1
```
- Source: `master@dell7050:/home/master/homeassistant/custom_components/iaqualink`
- Destination: `.\ha_custom_component\`

### `copy_to_server.ps1`
Uploads the updated integration back to your Home Assistant server.
```powershell
.\copy_to_server.ps1
```
- Copies updated `light.py` from `homeassistant_integration_light.py`
- Creates backup on server before uploading
- Source: `.\ha_custom_component\`
- Destination: `master@dell7050:/home/master/homeassistant/custom_components/iaqualink`

## Status: ✅ UPLOADED

The updated integration has been successfully uploaded to your server at:
`master@dell7050:/home/master/homeassistant/custom_components/iaqualink`

## Next Steps

1. **Restart Home Assistant:**
   ```bash
   ssh master@dell7050 'docker restart homeassistant'
   ```
   Or use: Developer Tools → Restart in Home Assistant UI

2. **Verify RGB Support:**
   - Open your ICL light entity (e.g., "Pool lights")
   - You should now see:
     - ✅ Brightness slider
     - ✅ Full color picker (color wheel)
     - ✅ White value slider (if RGBW mode)
     - ✅ Effect selector

3. **Test RGB Color Control:**
   - Select different colors from the color picker
   - Verify the physical lights change color
   - Test brightness at different color settings
   - Test white value adjustment

4. **Check Device Attributes:**
   - Go to Developer Tools → States
   - Find your light entity (e.g., `light.pool_lights`)
   - Verify attributes:
     - `supported_color_modes: ["rgb"]` or `["rgbw"]`
     - `color_mode: "rgb"` or `"rgbw"`
     - `rgb_color: [r, g, b]`

## Troubleshooting

### ⚠️ CRITICAL: Installing Custom Python Packages in Home Assistant

**RULE OF THUMB: ALWAYS use `--no-deps` when installing ANY custom Python package in Home Assistant.**

Home Assistant has carefully pinned dependency versions. Installing packages without `--no-deps` can upgrade core dependencies and break HA entirely.

```bash
# ✅ CORRECT - Always use --no-deps
docker exec home-assistant pip install --no-deps "git+https://github.com/user/repo.git@branch"
docker exec home-assistant pip install --no-deps some-package

# ❌ WRONG - May break Home Assistant
docker exec home-assistant pip install "git+https://github.com/user/repo.git@branch"
docker exec home-assistant pip install some-package
```

**After installing, verify critical packages weren't changed**:
```bash
docker exec home-assistant pip show pycares aiodns aiohttp
# pycares should be 4.11.0, aiodns should be 3.5.0
```

---

### Home Assistant Crash Loop (pycares error)

If Home Assistant enters a restart loop with this error:
```
AttributeError: module 'pycares' has no attribute 'ares_query_a_result'
```

**Cause**: A package was installed WITHOUT `--no-deps`, which upgraded `pycares` from 4.11.0 to 5.0.1 (incompatible with HA).

**Fix**:
```bash
# Option 1: If container is crashing too fast to exec into
ssh master@dell7050 'docker rm -f home-assistant && docker run -d --name home-assistant --restart=unless-stopped -v /home/master/homeassistant:/config -v /etc/localtime:/etc/localtime:ro --network=host ghcr.io/home-assistant/home-assistant:2025.9.3'

# Wait for container to start, then reinstall iaqualink properly
ssh master@dell7050 'docker exec home-assistant pip install --no-deps "git+https://github.com/matiazo/iaqualink-py.git@master"'

# Fix pycares (build deps may still upgrade it)
ssh master@dell7050 'docker exec home-assistant pip install pycares==4.11.0'

# Restart
ssh master@dell7050 'docker restart home-assistant'
```

**Option 2: If container can be exec'd into**:
```bash
ssh master@dell7050 'docker exec home-assistant pip install aiodns==3.5.0 pycares==4.11.0 && docker restart home-assistant'
```

---

### Color picker not showing after restart

1. **Check logs:**
   ```
   Settings → System → Logs
   ```
   Look for errors containing "iaqualink" or "light"

2. **Verify integration is loaded:**
   ```
   Settings → Devices & Services → iaqualink
   ```
   Should show "Custom integration" or version number

3. **Force reload:**
   ```
   Settings → Devices & Services → iaqualink → ⋮ → Reload
   ```

4. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Or open in incognito/private window

### Colors not changing on physical lights

1. **Check device state in Developer Tools:**
   - Verify `rgb_color` attribute updates when you change color
   
2. **Check iaqualink-py library version:**
   - Ensure you're using your updated fork with ICL support
   - Verify manifest.json points to correct version

3. **Review Home Assistant logs:**
   - Look for errors when setting color
   - Check for API command errors

## Integration Details

### Color Mode Detection Logic
```python
color_mode = ColorMode.ONOFF
if dev.supports_rgb_color and dev.supports_white_value:
    color_mode = ColorMode.RGBW  # Full RGBW support
elif dev.supports_rgb_color:
    color_mode = ColorMode.RGB   # RGB only
elif dev.supports_brightness:
    color_mode = ColorMode.BRIGHTNESS  # Brightness only
```

### Color Command Priority (in `async_turn_on`)
1. RGB color (`ATTR_RGB_COLOR`)
2. RGBW color (`ATTR_RGBW_COLOR`)
3. White value (`ATTR_WHITE_VALUE`)
4. Effect (`ATTR_EFFECT`)
5. Brightness (`ATTR_BRIGHTNESS`)
6. Default turn on

This ensures commands are processed in the correct order and prevents conflicts.

## Files in Repository

- `homeassistant_integration_light.py` - Template/reference light.py with RGB support
- `ha_custom_component/` - Working copy of custom integration (gitignored)
- `copy_from_server.ps1` - Download script
- `copy_to_server.ps1` - Upload script
- `HOMEASSISTANT_RGB_SETUP.md` - Original setup instructions
- `HA_INTEGRATION_UPDATE.md` - This file

## Backup

A backup of your original integration was created on the server at:
```
/home/master/homeassistant/custom_components/iaqualink.backup.YYYYMMDD_HHMMSS
```

If you need to rollback:
```bash
ssh master@dell7050
cd /home/master/homeassistant/custom_components
rm -rf iaqualink
cp -r iaqualink.backup.YYYYMMDD_HHMMSS iaqualink
# Then restart Home Assistant
```
