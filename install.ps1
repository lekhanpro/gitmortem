param()

$source = if ($env:GITMORTEM_PIP_SOURCE) {
    $env:GITMORTEM_PIP_SOURCE
} else {
    "git+https://github.com/lekhanpro/gitmortem.git"
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "gitmortem install failed: Python 3.10+ is required."
}

$pythonCommand = Get-PythonCommand
if ($pythonCommand.Length -gt 1) {
    & $pythonCommand[0] $pythonCommand[1] -m pip install --user --upgrade $source
} else {
    & $pythonCommand[0] -m pip install --user --upgrade $source
}

Write-Output ""
Write-Output "gitmortem installed."
Write-Output "Try:"
Write-Output "  python -m gitmortem HEAD~1"
