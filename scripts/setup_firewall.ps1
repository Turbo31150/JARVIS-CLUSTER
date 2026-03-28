# JARVIS M2 Firewall Setup — Run as Administrator
# Ouvre tous les ports pour que M1 puisse controler M2

Write-Host "=== JARVIS M2 Firewall Setup ===" -ForegroundColor Cyan

# Supprimer anciennes regles
@("JARVIS M2 Services", "JARVIS M2 WinRM", "JARVIS M2 UDP") | ForEach-Object {
    Remove-NetFirewallRule -DisplayName $_ -ErrorAction SilentlyContinue
}

# TCP — Tous les services JARVIS
New-NetFirewallRule -DisplayName "JARVIS M2 Services" `
    -Direction Inbound -Action Allow -Protocol TCP `
    -LocalPort 1234,5678,8080,8765,8901,9742,18800 `
    -RemoteAddress 192.168.1.0/24 `
    -Profile Any -Enabled True

# WinRM — Remote management depuis M1
New-NetFirewallRule -DisplayName "JARVIS M2 WinRM" `
    -Direction Inbound -Action Allow -Protocol TCP `
    -LocalPort 5985,5986 `
    -RemoteAddress 192.168.1.85 `
    -Profile Any -Enabled True

# UDP
New-NetFirewallRule -DisplayName "JARVIS M2 UDP" `
    -Direction Inbound -Action Allow -Protocol UDP `
    -LocalPort 1234,8765 `
    -RemoteAddress 192.168.1.0/24 `
    -Profile Any -Enabled True

Write-Host ""
Write-Host "Firewall rules created:" -ForegroundColor Green
Get-NetFirewallRule -DisplayName "JARVIS*" | Select-Object DisplayName, Enabled, Direction | Format-Table -AutoSize

Write-Host ""
Write-Host "M1 (192.168.1.85) can now fully control M2 (192.168.1.26)" -ForegroundColor Yellow
Write-Host "Ports: 1234, 5678, 8080, 8765, 8901, 9742, 18800, 5985, 5986" -ForegroundColor Yellow

pause
