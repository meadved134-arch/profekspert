$ErrorActionPreference = "Stop"
$ip = "79.174.85.179"
$remoteDir = "/var/www/profexpert"

Write-Host "Updating site on server ($ip)..." -ForegroundColor Cyan
ssh -o BatchMode=yes root@$ip "cd $remoteDir && git pull && pm2 restart profexpert"
Write-Host "Done! Site is live: http://$ip" -ForegroundColor Green
