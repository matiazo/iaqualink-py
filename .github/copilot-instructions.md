# GitHub Copilot Instructions for iaqualink-py Home Assistant Integration

## Project Overview

This project provides a Python library and Home Assistant custom integration for controlling Jandy iAqualink pool systems, with full support for ICL (IntelliBrite Color Lights) including RGB/RGBW color control, brightness, and effects.

## Server Environment

### Connection Details
- **Read Access**: `master@dell7050`
- **Write Access**: `master@dell7050`
- **Home Assistant Container**: `home-assistant` (Docker)
- **Python Version in Container**: 3.13

### Key Paths
- **Custom Integration**: `/home/master/homeassistant/custom_components/iaqualink/`
- **Python Library in Container**: `/usr/local/lib/python3.13/site-packages/iaqualink/`
- **Logs**: `/home/master/homeassistant/home-assistant.log`
- **Backups**: `/home/master/homeassistant_backups/`

## Common Operations

### Checking Home Assistant Logs

**View recent logs**:
```bash
ssh master@dell7050 'tail -100 /home/master/homeassistant/home-assistant.log'
```

**Follow logs in real-time**:
```bash
ssh master@dell7050 'tail -f /home/master/homeassistant/home-assistant.log'
```

**Check for integration-specific logs**:
```bash
ssh master@dell7050 'grep iaqualink /home/master/homeassistant/home-assistant.log | tail -50'
```

**Check for errors**:
```bash
ssh master@dell7050 'grep -i error /home/master/homeassistant/home-assistant.log | tail -30'
```

**Check ICL light logs with color debugging**:
```bash
ssh master@dell7050 'tail -200 /home/master/homeassistant/home-assistant.log | grep -E "(Setting ICL|red_val|white_val|Pool lights)"'
```

### Restarting Home Assistant

**Restart the container**:
```bash
ssh master@dell7050 'docker restart home-assistant'
```

Wait 30-40 seconds for Home Assistant to fully start before checking logs or testing.

**Verify container is running**:
```bash
ssh master@dell7050 'docker ps | grep home-assistant'
```

### Backup Management

**List existing backups**:
```bash
ssh master@dell7050 'ls -la /home/master/homeassistant_backups/'
```

**Create manual backup** (before making changes):
```bash
ssh master@dell7050 'mkdir -p /home/master/homeassistant_backups && cp -r /home/master/homeassistant/custom_components/iaqualink /home/master/homeassistant_backups/iaqualink.backup.$(date +%Y%m%d_%H%M%S)'
```

**Restore from backup**:
```bash
ssh master@dell7050 'cp -r /home/master/homeassistant_backups/iaqualink.backup.YYYYMMDD_HHMMSS/* /home/master/homeassistant/custom_components/iaqualink/ && docker restart home-assistant'
```

**Clean old backups** (keep last 5):
```bash
ssh master@dell7050 'cd /home/master/homeassistant_backups && ls -t | grep iaqualink.backup | tail -n +6 | xargs -r rm -rf'
```

## Deployment Workflow

### CRITICAL: Installing the iaqualink Library

The Home Assistant container comes with stock `iaqualink` v0.6.0 which does NOT support ICL lights. You MUST install this forked version after any container recreation:

```bash
# Install the forked iaqualink library (REQUIRED for ICL lights)
ssh master@dell7050 'docker exec home-assistant pip install --no-deps "git+https://github.com/matiazo/iaqualink-py.git@master"'

# Restart Home Assistant
ssh master@dell7050 'docker restart home-assistant'

# Verify the correct version is installed (should show 0.1.dev* not 0.6.0)
ssh master@dell7050 'docker exec home-assistant pip show iaqualink'
```

**IMPORTANT**: The `--no-deps` flag is critical to avoid upgrading aiodns/pycares which breaks HA.

If Home Assistant crashes with `pycares.ares_query_a_result` error, fix with:
```bash
ssh master@dell7050 'docker exec home-assistant pip install aiodns==3.5.0 pycares==4.11.0 && docker restart home-assistant'
```

### Deploying Custom Integration Changes

The project includes PowerShell scripts for deployment:

**1. Upload integration to server**:
```powershell
.\copy_to_server.ps1
```

This script:
- Creates a backup in `/home/master/homeassistant_backups/`
- Copies `homeassistant_integration_light.py` to `ha_custom_component\light.py`
- Uploads all files to the server via SCP

**2. Restart Home Assistant**:
```powershell
ssh master@dell7050 'docker restart home-assistant'
```

**3. Verify deployment**:
```bash
ssh master@dell7050 'grep iaqualink /home/master/homeassistant/home-assistant.log | tail -20'
```

### Deploying Python Library Changes

When changes are made to the core library (e.g., `src/iaqualink/systems/iaqua/device.py`):

**Copy updated library file to container**:
```bash
# 1. Copy to server temp location
scp src/iaqualink/systems/iaqua/device.py master@dell7050:/tmp/device.py

# 2. Copy into container
ssh master@dell7050 'docker cp /tmp/device.py home-assistant:/usr/local/lib/python3.13/site-packages/iaqualink/systems/iaqua/device.py'

# 3. Restart Home Assistant
ssh master@dell7050 'docker restart home-assistant'
```

### Refreshing from Remote Repository

To update the Python library in Home Assistant from the latest GitHub repository:

```bash
ssh master@dell7050 'docker exec home-assistant pip install --no-cache-dir --upgrade --force-reinstall "git+https://github.com/matiazo/iaqualink-py.git@master" && docker restart home-assistant'
```

This is useful when:
- Testing changes that have been pushed to GitHub
- Updating to the latest published version
- Verifying package installation works correctly

## File Structure

### Local Development
- **Custom Integration**: `ha_custom_component/` (the full HA custom component, tracked in git)
- **Python Library**: `src/iaqualink/` (core library with ICL light support)
- **Deployment Scripts**: `copy_to_server.ps1`, `copy_from_server.ps1`, `restart_homeassistant.ps1`
- **Legacy Template**: `homeassistant_integration_light.py` (older source file for light.py)

### Server Deployment
- **Custom Integration**: `/home/master/homeassistant/custom_components/iaqualink/`
  - `__init__.py` - Main integration setup
  - `light.py` - Light platform with RGB/RGBW support
  - `climate.py`, `sensor.py`, `switch.py`, etc.
- **Python Library**: `/usr/local/lib/python3.13/site-packages/iaqualink/`

## Important Implementation Details

### ICL Light Color Control

**Key Features**:
- **Color Modes**: RGBW (with white LEDs) or RGB (color only)
- **Debouncing**: 300ms delay for color changes to prevent API flooding
- **Optimistic Updates**: UI updates immediately while waiting for hardware
- **Single API Call**: RGB and white values sent together to avoid race conditions

**Critical Code Patterns**:
```python
# Set RGB color with explicit white value
await self.dev.set_rgb_color(red, green, blue, white=0)

# Debouncing with asyncio
self._debounce_task = asyncio.create_task(self._debounced_update())

# Optimistic UI update
self._attr_rgb_color = rgb_color
self.async_write_ha_state()
```

### Common Issues and Solutions

**Issue**: Colors revert back after selection
- **Cause**: White LEDs washing out colors or race condition
- **Solution**: Ensure white=0 when setting RGB colors, use single API call

**Issue**: Sluggish UI or errors when dragging color picker
- **Cause**: Too many API calls overwhelming the device
- **Solution**: Implement debouncing (DEBOUNCE_DELAY = 0.3 seconds)

**Issue**: Integration fails to load with "No module named 'backup'"
- **Cause**: Backup directories in `custom_components/` treated as submodules
- **Solution**: Store backups in `/home/master/homeassistant_backups/` instead

**Issue**: Cache/bytecode issues after updates
- **Cause**: Python .pyc files not refreshing
- **Solution**: Clear cache and restart:
  ```bash
  ssh master@dell7050 'rm -rf /home/master/homeassistant/custom_components/iaqualink/__pycache__ && docker restart home-assistant'
  ```

## Testing Checklist

After deploying changes, verify:

1. **Integration Loads**:
   ```bash
   ssh master@dell7050 'grep "Got.*lights" /home/master/homeassistant/home-assistant.log | tail -5'
   ```

2. **No Errors**:
   ```bash
   ssh master@dell7050 'grep -i "error.*iaqualink\|exception.*iaqualink" /home/master/homeassistant/home-assistant.log | tail -10'
   ```

3. **ICL Lights Detected**:
   ```bash
   ssh master@dell7050 'grep "Pool lights" /home/master/homeassistant/home-assistant.log | tail -3'
   ```

4. **Color Commands Working**:
   ```bash
   ssh master@dell7050 'grep "Setting ICL light" /home/master/homeassistant/home-assistant.log | tail -10'
   ```

## Best Practices

1. **Always create backups** before making changes
2. **Test locally** when possible before deploying to server
3. **Check logs** after every deployment
4. **Wait 30-40 seconds** after restart before testing
5. **Clear Python cache** if encountering import/module issues
6. **Use debouncing** for frequently-updated values (colors, brightness)
7. **Implement optimistic updates** for better UI responsiveness
8. **Store backups outside** `custom_components/` to avoid import conflicts

## Debugging Tips

**Enable debug logging** in Home Assistant:
Edit `/home/master/homeassistant/configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.iaqualink: debug
    iaqualink: debug
```

Then restart Home Assistant.

**Monitor API calls in real-time**:
```bash
ssh master@dell7050 'tail -f /home/master/homeassistant/home-assistant.log | grep -E "(-> GET|<- 200|Setting ICL)"'
```

**Check Python library version in container**:
```bash
ssh master@dell7050 'docker exec home-assistant pip show iaqualink'
```

**Verify file permissions**:
```bash
ssh master@dell7050 'ls -la /home/master/homeassistant/custom_components/iaqualink/'
```

## Quick Reference Commands

```bash
# Quick status check
ssh master@dell7050 'tail -50 /home/master/homeassistant/home-assistant.log | grep iaqualink'

# Quick restart and verify
ssh master@dell7050 'docker restart home-assistant' && sleep 40 && ssh master@dell7050 'grep iaqualink /home/master/homeassistant/home-assistant.log | tail -10'

# Emergency restore (replace TIMESTAMP with actual backup)
ssh master@dell7050 'cp -r /home/master/homeassistant_backups/iaqualink.backup.TIMESTAMP/* /home/master/homeassistant/custom_components/iaqualink/ && docker restart home-assistant'

# Full deployment pipeline
.\copy_to_server.ps1 && ssh master@dell7050 'docker restart home-assistant' && sleep 40 && ssh master@dell7050 'grep iaqualink /home/master/homeassistant/home-assistant.log | tail -20'

# After container recreation - install forked library
ssh master@dell7050 'docker exec home-assistant pip install --no-deps "git+https://github.com/matiazo/iaqualink-py.git@master" && docker restart home-assistant'

# Verify ICL lights are detected (should show "Got 1 lights")
ssh master@dell7050 'grep "Got.*lights" /home/master/homeassistant/home-assistant.log | tail -3'
```

## After Server Migration / Container Recreation

If you migrate to a new server or recreate the Docker container, follow these steps:

1. **Deploy custom integration files**:
   ```powershell
   .\copy_to_server.ps1
   ```

2. **Install the forked iaqualink library** (stock HA has v0.6.0 without ICL support):
   ```bash
   ssh master@dell7050 'docker exec home-assistant pip install --no-deps "git+https://github.com/matiazo/iaqualink-py.git@master"'
   ```

3. **Restart Home Assistant**:
   ```bash
   ssh master@dell7050 'docker restart home-assistant'
   ```

4. **Verify lights are detected**:
   ```bash
   ssh master@dell7050 'grep "Got.*lights" /home/master/homeassistant/home-assistant.log | tail -5'
   ```
   Should show: `Got 1 lights: [IaquaICLLight(...)]`
