# Copy updated Home Assistant iaqualink integration back to server
# Usage: .\copy_to_server.ps1

$SERVER = "root@kube1.local"
$LOCAL_PATH = ".\ha_custom_component"
$REMOTE_PATH = "/home/master/homeassistant/custom_components/iaqualink"

Write-Host "Preparing to copy updated iaqualink integration to $SERVER..." -ForegroundColor Green
Write-Host "Local path: $LOCAL_PATH" -ForegroundColor Cyan
Write-Host "Remote path: $REMOTE_PATH" -ForegroundColor Cyan

# Check if local directory exists
if (-not (Test-Path $LOCAL_PATH)) {
    Write-Host "`nError: Local directory not found: $LOCAL_PATH" -ForegroundColor Red
    Write-Host "Run .\copy_from_server.ps1 first to download the integration" -ForegroundColor Yellow
    exit 1
}

# Copy the updated light.py file to the local integration directory
Write-Host "`nCopying updated light.py to integration directory..." -ForegroundColor Yellow
Copy-Item -Path ".\homeassistant_integration_light.py" -Destination "$LOCAL_PATH\light.py" -Force

Write-Host "Files to be uploaded:" -ForegroundColor Cyan
Get-ChildItem -Path $LOCAL_PATH -File | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor White
}

Write-Host "`nUploading to server..." -ForegroundColor Yellow

# Backup existing integration on server to a separate directory
Write-Host "Creating backup outside custom_components..." -ForegroundColor Yellow
ssh $SERVER 'mkdir -p /home/master/homeassistant_backups && cp -r /home/master/homeassistant/custom_components/iaqualink /home/master/homeassistant_backups/iaqualink.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true'

# Copy files to server using scp
scp -r ${LOCAL_PATH}/* "${SERVER}:${REMOTE_PATH}/"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccess! Files uploaded to ${SERVER}:${REMOTE_PATH}" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart Home Assistant" -ForegroundColor White
    Write-Host "  2. Check that ICL lights show color picker" -ForegroundColor White
    Write-Host "  3. Test RGB color control" -ForegroundColor White
    Write-Host "`nTo restart Home Assistant:" -ForegroundColor Cyan
    Write-Host "  ssh $SERVER 'docker restart homeassistant'" -ForegroundColor White
    Write-Host "  or use Developer Tools -> Restart in HA UI" -ForegroundColor White
} else {
    Write-Host "`nError: Failed to copy files to server" -ForegroundColor Red
    exit 1
}
