$scriptDirectory = $PSScriptRoot
$requirementsFile = Join-Path $scriptDirectory "requirements.txt"
$wallpaperFolder = Join-Path $scriptDirectory "images"
$scraperScript = Join-Path $scriptDirectory "devianart.py"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    Write-Error "Python was not found. Install Python and ensure it is available as 'python' in PATH."
    exit 1
}
$python = $pythonCommand.Source

if (-not (Test-Path $requirementsFile)) {
    Write-Error "Python requirements file was not found: $requirementsFile"
    exit 1
}

# Install project dependencies on the first run when Beautiful Soup is unavailable.
& $python -c "import bs4" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Python dependencies..."
    & $python -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Python dependencies from $requirementsFile"
        exit 1
    }
}

# Delete existing wallpaper files
Remove-Item -Path "$wallpaperFolder\wallpaper.jpg" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.png" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.jpeg" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.bmp" -ErrorAction SilentlyContinue

# Get the current month
$month = (Get-Date).Month

# Define the URL based on the current month
$url = switch ($month) {
	9 { "https://www.deviantart.com/topic/creepy" }
    10 { "https://www.deviantart.com/topic/horror" }
    11 { "https://www.deviantart.com/topic/surreal" }
    12 { "https://www.deviantart.com/topic/christmas" }
    1  { "https://www.deviantart.com/topic/winter" }
    2  { "https://www.deviantart.com/topic/cyberpunk" }
    3  { "https://www.deviantart.com/topic/fantasy" }
    4  { "https://www.deviantart.com/topic/science-fiction" }
    5  { "https://www.deviantart.com/topic/photo-manipulation" }
    default { "https://www.deviantart.com/topic/random" }
}

# Download image
& $python $scraperScript -d $wallpaperFolder -f wallpaper -c 1 -r -u $url
if ($LASTEXITCODE -ne 0) {
    Write-Error "The DeviantArt scraper failed."
    exit 1
}

# Get all image files in the folder
$wallpapers = Get-ChildItem -Path $wallpaperFolder -Recurse | Where-Object { $_.Extension -match "jpg|jpeg|png|bmp" }

# Check if any wallpapers were found
if ($null -eq $wallpapers -or $wallpapers.Count -eq 0) {
    Write-Host "No wallpapers found in the specified folder: $wallpaperFolder"
    exit
}

# Select a random wallpaper
$randomWallpaper = Get-Random -InputObject $wallpapers

# Output the selected file for debugging
Write-Host "Selected file: "$randomWallpaper.FullName

# Set the wallpaper using SystemParametersInfo
$code = @"
using System;
using System.Runtime.InteropServices;

public class Wallpaper {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);

    public static void SetWallpaper(string path) {
        SystemParametersInfo(0x0014, 0, path, 0x01 | 0x02);
    }
}
"@

Add-Type -TypeDefinition $code
[Wallpaper]::SetWallpaper($randomWallpaper.FullName)
