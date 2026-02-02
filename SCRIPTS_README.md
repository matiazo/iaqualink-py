# Home Assistant Integration Deployment Scripts

Quick reference for the PowerShell scripts to manage your Home Assistant iaqualink custom integration.

## Scripts

### 1️⃣ Download from Server
```powershell
.\copy_from_server.ps1
```
- Downloads current integration from `master@kube1.local`
- Saves to `.\ha_custom_component\`
- Use this before making changes

### 2️⃣ Upload to Server
```powershell
.\copy_to_server.ps1
```
- Copies updated `light.py` from `homeassistant_integration_light.py`
- Uploads all files to `root@kube1.local`
- Creates backup before overwriting
- Use this after making changes

### 3️⃣ Restart Home Assistant
```powershell
.\restart_homeassistant.ps1
```
- Restarts Home Assistant container
- Use this after uploading changes
- Wait 30-60 seconds for restart to complete

## Typical Workflow

1. **Download current integration:**
   ```powershell
   .\copy_from_server.ps1
   ```

2. **Make changes** to `ha_custom_component\light.py`

3. **Upload changes:**
   ```powershell
   .\copy_to_server.ps1
   ```

4. **Restart Home Assistant:**
   ```powershell
   .\restart_homeassistant.ps1
   ```

5. **Test** the changes in Home Assistant UI

## Server Details

- **Download from:** `master@kube1.local:/home/master/homeassistant/custom_components/iaqualink`
- **Upload to:** `root@kube1.local:/home/master/homeassistant/custom_components/iaqualink`
- **Container:** `homeassistant` (Docker)

## Current Status

✅ RGB/RGBW color support has been added to `light.py`  
✅ Updated integration uploaded to server  
⏳ **Next:** Restart Home Assistant and test!

Run: `.\restart_homeassistant.ps1`
