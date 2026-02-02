# Copy Home Assistant iaqualink custom integration from server
# Usage: .\copy_from_server.ps1

$SERVER = "master@dell7050"
$REMOTE_PATH = "/home/master/homeassistant/custom_components/iaqualink"
$LOCAL_PATH = ".\ha_custom_component"

Write-Host "Copying iaqualink custom integration from $SERVER..." -ForegroundColor Green
Write-Host "Remote path: $REMOTE_PATH" -ForegroundColor Cyan
Write-Host "Local path: $LOCAL_PATH" -ForegroundColor Cyan

# Create local directory if it doesn't exist
if (-not (Test-Path $LOCAL_PATH)) {
    New-Item -ItemType Directory -Path $LOCAL_PATH | Out-Null
    Write-Host "Created directory: $LOCAL_PATH" -ForegroundColor Yellow
}

# Copy the entire directory using scp
scp -r "${SERVER}:${REMOTE_PATH}/*" $LOCAL_PATH

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccess! Files copied to: $LOCAL_PATH" -ForegroundColor Green
    Write-Host "`nCopied files:" -ForegroundColor Cyan
    Get-ChildItem -Path $LOCAL_PATH -Recurse -File | ForEach-Object {
        Write-Host "  - $($_.FullName.Replace((Get-Location).Path + '\', ''))" -ForegroundColor White
    }
} else {
    Write-Host "`nError: Failed to copy files from server" -ForegroundColor Red
    exit 1
}
