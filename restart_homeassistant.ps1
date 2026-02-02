# Restart Home Assistant on server
# Usage: .\restart_homeassistant.ps1

$SERVER = "master@dell7050"

Write-Host "Restarting Home Assistant on $SERVER..." -ForegroundColor Yellow

ssh $SERVER 'docker restart homeassistant'

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nHome Assistant is restarting..." -ForegroundColor Green
    Write-Host "Wait about 30-60 seconds for it to come back online" -ForegroundColor Cyan
    Write-Host "`nThen check:" -ForegroundColor Yellow
    Write-Host "  1. Open your ICL light in Home Assistant" -ForegroundColor White
    Write-Host "  2. Look for the color picker (color wheel)" -ForegroundColor White
    Write-Host "  3. Test changing colors" -ForegroundColor White
    Write-Host "`nTo view logs:" -ForegroundColor Yellow
    Write-Host "  ssh $SERVER 'docker logs -f homeassistant'" -ForegroundColor White
} else {
    Write-Host "`nError: Failed to restart Home Assistant" -ForegroundColor Red
    exit 1
}
