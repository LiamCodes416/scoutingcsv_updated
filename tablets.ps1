param(
    [int]$tablet
)

adb devices

adb pull "/sdcard/Android/data/com.sotabots.sotabotsscouting/files/scouting_export_tablet$tablet.csv"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Success: Tablet $tablet data pulled successfully!" -ForegroundColor Green
} else {
    Write-Error "Error: Failed to pull data from tablet $tablet. Check connection or file path."
}