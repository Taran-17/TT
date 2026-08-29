Set-Location 'C:\Work\tt'
$trace = 'C:\Work\tt\tt-launch.trace.log'
$stdout = 'C:\Work\tt\uvicorn.out.log'
$stderr = 'C:\Work\tt\uvicorn.err.log'
Set-Content -LiteralPath $trace -Value "launcher-start $(Get-Date -Format o)"
Remove-Item -LiteralPath $stdout, $stderr -ErrorAction SilentlyContinue
try {
    $proc = Start-Process -WindowStyle Hidden -FilePath 'C:\Python312\python.exe' -ArgumentList @(
        '-m',
        'uvicorn',
        'server:app',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
        '--log-level',
        'info'
    ) -WorkingDirectory 'C:\Work\tt' -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Set-Content -LiteralPath $trace -Value "launcher-start $(Get-Date -Format o)`npid=$($proc.Id)"
} catch {
    Set-Content -LiteralPath $trace -Value "launcher-start $(Get-Date -Format o)`nerror=$($_.Exception.Message)`nfull=$($_ | Out-String)"
    throw
}
