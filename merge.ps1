$ErrorActionPreference = "Stop"

try {
    # 1. Set up folders matching your local Documents setup
    $inputFolder = Join-Path $env:USERPROFILE "Documents\ScoutingCSV"
    $outputFile  = Join-Path $inputFolder "Scouting_Merged.csv"

    if (-not (Test-Path -Path $inputFolder -PathType Container)) {
        Write-Error "ERROR: Folder not found: $inputFolder"
        exit 1
    }

    # 2. Clean up old merged file if it exists
    if (Test-Path -Path $outputFile -PathType Leaf) {
        Remove-Item -Path $outputFile -Force
        Write-Host "Deleted existing file: $outputFile"
    }

    # 3. Find all CSV files except the output file itself
    $csvFiles = Get-ChildItem -Path $inputFolder -Filter *.csv | 
                Where-Object { $_.Name -ne "Scouting_Merged.csv" }

    if (-not $csvFiles) {
        Write-Host "No CSV files found in folder: $inputFolder"
        exit 0
    }

    Write-Host "Found $($csvFiles.Count) CSV files from tablets. Merging..."

    # 4. Import and combine all CSV data
    $allRows = @()
    foreach ($file in $csvFiles) {
        # Using UTF8 encoding to safely parse tablet comment strings
        $data = Import-Csv -Path $file.FullName -Encoding utf8
        if ($data) {
            $allRows += $data
            Write-Host "Merged: $($file.Name)"
        }
    }

    if ($allRows.Count -eq 0) {
        Write-Host "No data found inside the CSV files."
        exit 0
    }

    # 5. Sort precisely matching SOTABOTS schema (Team then Match)
    # Casting to [int] stops '10' from sorting before '2'
    Write-Host "Sorting rows by Team and Match numbers..."
    $allRows = $allRows | Sort-Object { [int]$_.Team }, { [int]$_.Match }

    # 6. Save the final merged file with UTF8 encoding
    $allRows | Export-Csv -Path $outputFile -NoTypeInformation -Encoding utf8
    Write-Host "All tablet files merged successfully into: $outputFile"

} catch {
    Write-Error "An unexpected error occurred: $_"
}
