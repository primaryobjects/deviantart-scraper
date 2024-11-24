# Get the current logged-in user's profile path
$userProfile = [System.Environment]::GetFolderPath('UserProfile')

#############
# IMPORTANT
# Replace "\Documents\deviantart-scraper" with the path to deviantart-scraper.
#############
$deviantArtScraperFolder = "Documents\deviantart-scraper"
#############

# Define the folder containing the wallpapers.
$wallpaperFolder = "$userProfile\$deviantArtScraperFolder\images"

# Delete existing wallpaper files
Remove-Item -Path "$wallpaperFolder\wallpaper.jpg" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.png" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.jpeg" -ErrorAction SilentlyContinue
Remove-Item -Path "$wallpaperFolder\wallpaper.bmp" -ErrorAction SilentlyContinue

# Get the current month
$month = (Get-Date).Month

# Define the URL based on the current month
$url = switch ($month) {
    10 { "https://www.deviantart.com/topic/horror" }
    11 { "https://www.deviantart.com/topic/artisan-crafts" }
    12 { "https://www.deviantart.com/topic/poetry" }
    1  { "https://www.deviantart.com/topic/photography" }
    2  { "https://www.deviantart.com/topic/game-art" }
    3  { "https://www.deviantart.com/topic/stock-images" }
    4  { "https://www.deviantart.com/topic/science-fiction" }
    5  { "https://www.deviantart.com/topic/photo-manipulation" }
    default { "https://www.deviantart.com/topic/random" }
}

# Download image
python "$userProfile\$deviantArtScraperFolder\devianart.py" -f wallpaper -c 1 -r -u $url

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
