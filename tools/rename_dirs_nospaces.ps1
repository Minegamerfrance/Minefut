# Rename directories recursively by replacing spaces with underscores, deepest first
param(
    [string]$Root = "C:\Users\Utilisateur\Desktop\Minefut"
)
Set-Location -LiteralPath $Root
$dirs = Get-ChildItem -Directory -Recurse -Force
$dirs = $dirs | Sort-Object @{ Expression = { ($_.FullName).Length } } -Descending
foreach ($d in $dirs) {
    if ($d.Name -match ' ') {
        $newName = ($d.Name -replace ' ', '_')
        try {
            Rename-Item -LiteralPath $d.FullName -NewName $newName -ErrorAction Stop
            Write-Host "Renamed: $($d.FullName) -> $newName"
        }
        catch {
            Write-Warning "Failed to rename: $($d.FullName) : $($_.Exception.Message)"
        }
    }
}
