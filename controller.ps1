<#
.SYNOPSIS
    Controller for Ava (AI Stock Monitoring Employee)
.DESCRIPTION
    Provides start, stop, status, and single-run lifecycle management for the AI employee.
#>

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "status", "run-once")]
    [string]$Action
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $scriptDir "employee.pid"
$logFile = Join-Path $scriptDir "employee_activity.log"
$csvFile = Join-Path $scriptDir "CSL_AX_prices.csv"
$pyScript = Join-Path $scriptDir "ai_employee.py"

function Get-PythonPath {
    $pythonCandidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    )
    foreach ($cand in $pythonCandidates) {
        if (Test-Path $cand) { return $cand }
    }
    # Fallback to py.exe or python.exe
    return "py"
}

function Get-RunningWorker {
    if (Test-Path $pidFile) {
        $savedPid = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
        if ($savedPid -match '^\d+$') {
            $proc = Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue
            if ($proc -and ($proc.ProcessName -like "*python*" -or $proc.ProcessName -like "*py*")) {
                return $proc
            }
        }
    }
    # Search for running python processes with ai_employee.py in CommandLine
    $pyProcs = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -eq "python.exe" -or $_.Name -eq "pythonw.exe" -or $_.Name -eq "py.exe") -and
        $_.CommandLine -match "ai_employee\.py"
    }
    if ($pyProcs) {
        $first = $pyProcs[0]
        $proc = Get-Process -Id $first.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            Set-Content -Path $pidFile -Value $proc.Id -Encoding utf8
            return $proc
        }
    }
    return $null
}

switch ($Action) {
    "start" {
        Write-Host "==========================================================" -ForegroundColor Cyan
        Write-Host "Starting AI Employee (Ava) - CSL.AX Market Monitor" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Cyan

        $existing = Get-RunningWorker
        if ($existing) {
            Write-Host "[WARNING] Ava is already actively running! (PID: $($existing.Id))" -ForegroundColor Yellow
            Write-Host "Use check_status.bat to inspect her work or stop_employee.bat to stop."
            return
        }

        if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }

        $pythonExe = Get-PythonPath
        Write-Host "Launching Ava in the background using: $pythonExe..." -ForegroundColor Green
        
        $cmdLine = "`"$pythonExe`" `"$pyScript`""
        $launchResult = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
            CommandLine = $cmdLine
            CurrentDirectory = $scriptDir
        }

        if ($launchResult.ReturnValue -eq 0 -and $launchResult.ProcessId) {
            Set-Content -Path $pidFile -Value $launchResult.ProcessId -Encoding utf8
            Write-Host "[SUCCESS] Ava is ON DUTY! (PID: $($launchResult.ProcessId))" -ForegroundColor Green
            Write-Host "She will autonomously check CSL.AX every 30 minutes without you asking."
            Write-Host "Ledger: $csvFile"
            Write-Host "Log:    $logFile"
        } else {
            Write-Host "[ERROR] Could not start Ava via WMI. Return code: $($launchResult.ReturnValue)" -ForegroundColor Red
        }
    }

    "stop" {
        Write-Host "==========================================================" -ForegroundColor Cyan
        Write-Host "Stopping AI Employee (Ava)" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Cyan

        $stoppedAny = $false

        # Stop via PID file
        if (Test-Path $pidFile) {
            $savedPid = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
            if ($savedPid -match '^\d+$') {
                try {
                    Stop-Process -Id ([int]$savedPid) -Force -ErrorAction Stop
                    Write-Host "[SUCCESS] Ava has clocked out safely. (Stopped PID: $savedPid)" -ForegroundColor Green
                    $stoppedAny = $true
                } catch { }
            }
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }

        # Stop any additional ai_employee python processes
        $workers = Get-CimInstance Win32_Process | Where-Object {
            ($_.Name -eq "python.exe" -or $_.Name -eq "pythonw.exe" -or $_.Name -eq "py.exe") -and
            $_.CommandLine -match "ai_employee\.py"
        }
        foreach ($w in $workers) {
            try {
                Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Host "[SUCCESS] Stopped worker PID $($w.ProcessId)" -ForegroundColor Green
                $stoppedAny = $true
            } catch { }
        }

        if (-not $stoppedAny) {
            Write-Host "[INFO] Ava is not currently running." -ForegroundColor Yellow
        }
    }

    "status" {
        Write-Host "==========================================================" -ForegroundColor Cyan
        Write-Host "AI Employee (Ava) - Status Report" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Cyan

        $worker = Get-RunningWorker
        if ($worker) {
            Write-Host "[STATUS] Ava is currently ACTIVE (PID: $($worker.Id))" -ForegroundColor Green
            Write-Host "[UPTIME] Working since: $($worker.StartTime)" -ForegroundColor DarkCyan
        } else {
            Write-Host "[STATUS] Ava is currently OFF DUTY (Stopped)" -ForegroundColor Yellow
            if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
        }

        Write-Host "`nRecent Activity Log (employee_activity.log):" -ForegroundColor White
        Write-Host "----------------------------------------------------------" -ForegroundColor Gray
        if (Test-Path $logFile) {
            Get-Content $logFile -Tail 5 | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host "No activity log recorded yet." -ForegroundColor Gray
        }

        Write-Host "`nLatest Recorded Prices (CSL_AX_prices.csv):" -ForegroundColor White
        Write-Host "----------------------------------------------------------" -ForegroundColor Gray
        if (Test-Path $csvFile) {
            $lines = Get-Content $csvFile
            if ($lines.Count -gt 0) {
                Write-Host $lines[0] -ForegroundColor DarkGray
                $lines | Select-Object -Skip 1 | Select-Object -Last 5 | ForEach-Object { Write-Host $_ }
            }
        } else {
            Write-Host "No CSV ledger found yet." -ForegroundColor Gray
        }
        Write-Host "==========================================================" -ForegroundColor Cyan
    }

    "run-once" {
        Write-Host "Executing single immediate check with Ava..." -ForegroundColor Cyan
        & py $pyScript --once
    }
}
