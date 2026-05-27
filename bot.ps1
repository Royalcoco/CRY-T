# PowerShell Trading Bot Application
# Integrates with Python backend in crypto_audio_cli

# Ensure UTF-8 output in PowerShell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$WalletFile = Join-Path $PSScriptRoot "wallet.json"
$PythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$HelperScript = Join-Path $PSScriptRoot "bot_helper.py"

# Audio player object
$Player = New-Object -ComObject WMPlayer.OCX

# Price tracking
$PreviousPrices = @{}

Clear-Host
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "    🤖  BOT DE TRADING AUTOMATIQUE POWERSHELL (v1.0)  🤖  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "Dossier de travail : $PSScriptRoot" -ForegroundColor DarkGray
Write-Host "Lancement de la surveillance du marché..." -ForegroundColor Yellow
Start-Sleep -Seconds 1

while ($true) {
    Clear-Host
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "    🤖  BOT DE TRADING AUTOMATIQUE POWERSHELL (v1.0)  🤖  " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Magenta

    # 1. Charger le portefeuille
    if (Test-Path $WalletFile) {
        $Wallet = Get-Content -Raw $WalletFile | ConvertFrom-Json
        Write-Host " 💼 SOLDE ACTUEL DU PORTEFEUILLE :" -ForegroundColor White
        foreach ($prop in $Wallet.PSObject.Properties) {
            $val = [double]$prop.Value
            if ($val -gt 0) {
                Write-Host "   • $($prop.Name) : $($val.ToString('N6'))" -ForegroundColor Green
            } else {
                Write-Host "   • $($prop.Name) : $($val.ToString('N6'))" -ForegroundColor DarkGray
            }
        }
    } else {
        Write-Host "Portefeuille non trouvé à l'emplacement : $WalletFile" -ForegroundColor Red
        Start-Sleep -Seconds 3
        continue
    }

    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray

    # 2. Récupérer les prix actifs du marché
    $PricesJson = & $PythonExe $HelperScript "prices"
    if ($LASTEXITCODE -ne 0 -or -not $PricesJson) {
        Write-Host "Erreur lors de la récupération des prix du marché." -ForegroundColor Red
        Start-Sleep -Seconds 5
        continue
    }
    
    $MarketData = $PricesJson | ConvertFrom-Json
    $Prices = $MarketData.prices
    $IsLive = $MarketData.is_live

    $StatusText = if ($IsLive) { "[EN LIGNE - CoinGecko]" } else { "[HORS LIGNE - Simulation]" }
    $StatusColor = if ($IsLive) { "Green" } else { "Red" }
    Write-Host " 📈 PRIX ACTIFS DU MARCHÉ $StatusText :" -ForegroundColor $StatusColor
    Write-Host "   • BTC  : `$($Prices.BTC.ToString('N2')) USD" -ForegroundColor Yellow
    Write-Host "   • ETH  : `$($Prices.ETH.ToString('N2')) USD" -ForegroundColor Yellow
    Write-Host "   • SOL  : `$($Prices.SOL.ToString('N2')) USD" -ForegroundColor Yellow
    Write-Host "   • USDT : `$($Prices.USDT.ToString('N4')) USD" -ForegroundColor Yellow
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray

    # 3. Stratégie de Trading (Vente hausse -> hausse crédit / Achat baisse -> dip)
    $ActionTaken = $false

    if ($PreviousPrices.Count -gt 0) {
        # Analyse des opportunités de swap
        $TokensToCheck = @("BTC", "ETH", "SOL")
        
        foreach ($Token in $TokensToCheck) {
            $CurrentPrice = [double]$Prices.$Token
            $PrevPrice = [double]$PreviousPrices.$Token
            $PriceDiffPct = (($CurrentPrice - $PrevPrice) / $PrevPrice) * 100

            Write-Host " Analyse $Token : Actuel = `$($CurrentPrice.ToString('N2')) | Précédent = `$($PrevPrice.ToString('N2')) (Variation: $($PriceDiffPct.ToString('F2'))%)" -ForegroundColor DarkGray

            if ($PriceDiffPct -gt 0.05) {
                # 📈 LE PRIX A AUGMENTÉ : Vendre une partie pour augmenter le crédit USD
                $TokenBalance = [double]$Wallet.$Token
                if ($TokenBalance -gt 0.0001) {
                    $AmountToSell = $TokenBalance * 0.20 # Vendre 20%
                    Write-Host "🚀 [Bot] Le prix de $Token augmente ! Vente de $($AmountToSell.ToString('N6')) $Token pour augmenter le crédit USD." -ForegroundColor Cyan
                    
                    # Exécuter l'échange
                    $SwapResultJson = & $PythonExe $HelperScript "swap" $Token "USD" $AmountToSell.ToString("F6", [System.Globalization.CultureInfo]::InvariantCulture)
                    if ($LASTEXITCODE -eq 0 -and $SwapResultJson) {
                        $SwapResult = $SwapResultJson | ConvertFrom-Json
                        if ($SwapResult.success) {
                            $Receipt = $SwapResult.receipt
                            Write-Host "✅ [Bot] Échange réussi !" -ForegroundColor Green
                            Write-Host "   Reçu ID : $($Receipt.id)" -ForegroundColor DarkGray
                            Write-Host "   Crédité : $($Receipt.to_amount.ToString('N2')) USD" -ForegroundColor Green
                            
                            # Lecture audio
                            if ($Receipt.audio_path -and (Test-Path $Receipt.audio_path)) {
                                $Player.URL = $Receipt.audio_path
                                $Player.controls.play()
                            }
                            $ActionTaken = $true
                            break # Une seule action par tick pour la clarté
                        } else {
                            Write-Host "❌ [Bot] Échec du swap : $($SwapResult.error)" -ForegroundColor Red
                        }
                    }
                }
            }
            elseif ($PriceDiffPct -lt -0.05) {
                # 📉 LE PRIX A BAISSÉ : Acheter le dip en utilisant le crédit USD
                $USDBalance = [double]$Wallet.USD
                if ($USDBalance -gt 1000) {
                    $AmountToSpend = $USDBalance * 0.10 # Dépenser 10% du crédit USD
                    Write-Host "📉 [Bot] Le prix de $Token baisse ! Achat de $Token avec $($AmountToSpend.ToString('N2')) USD." -ForegroundColor Yellow
                    
                    # Exécuter l'échange
                    $SwapResultJson = & $PythonExe $HelperScript "swap" "USD" $Token $AmountToSpend.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture)
                    if ($LASTEXITCODE -eq 0 -and $SwapResultJson) {
                        $SwapResult = $SwapResultJson | ConvertFrom-Json
                        if ($SwapResult.success) {
                            $Receipt = $SwapResult.receipt
                            Write-Host "✅ [Bot] Achat réussi !" -ForegroundColor Green
                            Write-Host "   Reçu ID : $($Receipt.id)" -ForegroundColor DarkGray
                            Write-Host "   Crédité : $($Receipt.to_amount.ToString('N6')) $Token" -ForegroundColor Green
                            
                            # Lecture audio
                            if ($Receipt.audio_path -and (Test-Path $Receipt.audio_path)) {
                                $Player.URL = $Receipt.audio_path
                                $Player.controls.play()
                            }
                            $ActionTaken = $true
                            break
                        } else {
                            Write-Host "❌ [Bot] Échec du swap : $($SwapResult.error)" -ForegroundColor Red
                        }
                    }
                }
            }
        }
    } else {
        Write-Host "Enregistrement des premiers prix de référence..." -ForegroundColor Yellow
    }

    # 4. Mettre à jour l'historique des prix
    foreach ($prop in $Prices.PSObject.Properties) {
        $PreviousPrices[$prop.Name] = $prop.Value
    }

    if (-not $ActionTaken) {
        Write-Host "💤 Aucune opportunité de trading détectée. En attente..." -ForegroundColor DarkGray
    }

    Write-Host "`n[Attente] Prochain cycle dans 10 secondes (Appuyez sur Ctrl+C pour quitter)..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
}
