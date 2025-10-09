param(
    [string] $Path = ".",
    [string[]] $ExcludeDirs = @("venv","env",".venv")
)

function Show-Tree {
    param(
        [string] $Path = ".",
        [string] $Prefix = "",
        [string[]] $ExcludeDirs = @("venv","env",".venv")
    )

    $items = @(Get-ChildItem -LiteralPath $Path -Force 2>$null |
               Where-Object { $_.Name -ne "." -and $_.Name -ne ".." } |
               Sort-Object @{Expression={$_.PSIsContainer};Descending=$true}, Name)

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $items.Count - 1)
        $connector = if ($isLast) { "+-- " } else { "|-- " }

        if ($item.PSIsContainer) {
            if ($ExcludeDirs -contains $item.Name) {
                # Mostrar la carpeta excluida pero omitir su contenido
                Write-Output ($Prefix + $connector + $item.Name + '\')
                continue
            }
            Write-Output ($Prefix + $connector + $item.Name + '\')
            if ($isLast) {
                $suffix = '    '
            } else {
                $suffix = '|   '
            }
            $newPrefix = $Prefix + $suffix
            Show-Tree -Path $item.FullName -Prefix $newPrefix -ExcludeDirs $ExcludeDirs
        } else {
            Write-Output ($Prefix + $connector + $item.Name)
        }
    }
}

Show-Tree -Path (Resolve-Path $Path).Path -ExcludeDirs $ExcludeDirs