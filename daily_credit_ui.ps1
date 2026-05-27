# =============================================================
#  daily_credit_ui.ps1
#  Interface PowerShell - Credit USD journalier automatique
#  Injecte une somme equivalente toutes les 24h dans le wallet
# =============================================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Chemins prioritaires
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe   = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$CreditPy    = Join-Path $ScriptDir "daily_credit.py"
$WalletFile  = Join-Path $ScriptDir "wallet.json"
$CreditLog   = Join-Path $ScriptDir "credit_log.json"
$TaskName    = "CryptoWallet_DailyCredit"

function Show-Header {
    Clear-Host
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "   💳  CREDIT USD JOURNALIER - PORTEFEUILLE CRYPTO  💳   " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "  Dossier : $ScriptDir" -ForegroundColor DarkGray
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
}

function Show-WalletStatus {
    if (Test-Path $WalletFile) {
        $Wallet = Get-Content -Raw $WalletFile | ConvertFrom-Json
        Write-Host " PORTEFEUILLE ACTUEL :" -ForegroundColor White
        Write-Host "   USD  : `$$($Wallet.USD.ToString('N2'))" -ForegroundColor Green
        Write-Host "   BTC  : $($Wallet.BTC.ToString('N6'))" -ForegroundColor Yellow
        Write-Host "   ETH  : $($Wallet.ETH.ToString('N6'))" -ForegroundColor Yellow
        Write-Host "   SOL  : $($Wallet.SOL.ToString('N6'))" -ForegroundColor Yellow
        Write-Host "   USDT : $($Wallet.USDT.ToString('N4'))" -ForegroundColor Yellow
    } else {
        Write-Host "  [!] Fichier wallet.json introuvable." -ForegroundColor Red
    }
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
}

function Show-CreditLog {
    if (Test-Path $CreditLog) {
        $Log = Get-Content -Raw $CreditLog | ConvertFrom-Json
        Write-Host " HISTORIQUE DES CREDITS JOURNALIERS :" -ForegroundColor White
        Write-Host "   Montant journalier configure  : `$$($Log.daily_amount_usd.ToString('N2')) USD" -ForegroundColor Cyan
        Write-Host "   Total cumule injecte          : `$$($Log.total_credited_usd.ToString('N2')) USD" -ForegroundColor Green
        Write-Host "   Prochain credit prevu         : $($Log.next_credit_due)" -ForegroundColor Yellow
        Write-Host "   Nombre de jours effectues     : $($Log.entries.Count)" -ForegroundColor Gray
        if ($Log.entries.Count -gt 0) {
            $Last = $Log.entries[-1]
            Write-Host "   Dernier credit                : $($Last.date) (+`$$($Last.amount_usd) USD)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  Aucun historique de credit (premier lancement)." -ForegroundColor DarkGray
    }
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
}

function Register-DailyTask {
    param([double]$Amount, [string]$TimeHHMM)

    # Supprimer l'ancienne tache si elle existe
    $Existing = schtasks /query /tn $TaskName 2>$null
    if ($LASTEXITCODE -eq 0) {
        schtasks /delete /tn $TaskName /f | Out-Null
        Write-Host "  Ancienne tache supprimee." -ForegroundColor DarkGray
    }

    # Construire la commande d'action
    $Action = "`"$PythonExe`" `"$CreditPy`" $Amount"

    # Enregistrer la nouvelle tache planifiee Windows
    $Result = schtasks /create `
        /tn $TaskName `
        /tr $Action `
        /sc DAILY `
        /st $TimeHHMM `
        /f 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  Tache planifiee Windows enregistree avec succes !" -ForegroundColor Green
        Write-Host "  Nom de la tache  : $TaskName" -ForegroundColor Cyan
        Write-Host "  Heure d execution: $TimeHHMM chaque jour" -ForegroundColor Cyan
        Write-Host "  Montant injecte  : `$$Amount USD" -ForegroundColor Cyan
        Write-Host "  La tache s executera automatiquement toutes les 24h." -ForegroundColor Yellow
    } else {
        Write-Host "  [ERREUR] Impossible d'enregistrer la tache : $Result" -ForegroundColor Red
    }
}

function Remove-DailyTask {
    $Existing = schtasks /query /tn $TaskName 2>$null
    if ($LASTEXITCODE -eq 0) {
        schtasks /delete /tn $TaskName /f | Out-Null
        Write-Host "  Tache '$TaskName' supprimee." -ForegroundColor Yellow
    } else {
        Write-Host "  Aucune tache planifiee trouvee." -ForegroundColor DarkGray
    }
}

function Inject-Now {
    param([double]$Amount)
    Write-Host ""
    Write-Host "  Injection immediate de `$$Amount USD dans le portefeuille..." -ForegroundColor Cyan
    $Output = & $PythonExe $CreditPy $Amount.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture) 2>&1
    Write-Host $Output -ForegroundColor White
}

function Show-TaskStatus {
    $Info = schtasks /query /tn $TaskName /fo LIST 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " TACHE WINDOWS PLANIFIEE ACTIVE :" -ForegroundColor Green
        $Info | ForEach-Object { Write-Host "   $_" -ForegroundColor DarkGray }
    } else {
        Write-Host " Aucune tache Windows planifiee trouvee pour '$TaskName'." -ForegroundColor DarkGray
        Write-Host " Utilisez l option [2] pour programmer le credit journalier." -ForegroundColor Yellow
    }
}

# ===================== BOUCLE PRINCIPALE =====================
while ($true) {
    Show-Header
    Show-WalletStatus
    Show-CreditLog

    Write-Host " OPTIONS :" -ForegroundColor White
    Write-Host "  [1] Injecter le credit USD maintenant (test immediat)" -ForegroundColor Cyan
    Write-Host "  [2] Programmer le credit journalier automatique (Tache Windows)" -ForegroundColor Cyan
    Write-Host "  [3] Voir l etat de la tache planifiee" -ForegroundColor Cyan
    Write-Host "  [4] Supprimer la tache planifiee" -ForegroundColor Red
    Write-Host "  [5] Quitter" -ForegroundColor Gray
    Write-Host "  [6] Retirer USD du portefeuille vers systeme de paiement" -ForegroundColor Yellow
    Write-Host "  [7] Afficher l'historique des retraits monétaires" -ForegroundColor Cyan
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray

    $Choice = Read-Host "Choisissez une option (1-7)"

    switch ($Choice) {
        "1" {
            $AmountStr = Read-Host "Montant USD a injecter maintenant (defaut: 100)"
            $Amount = if ($AmountStr -match '^\d+(\.\d+)?$') { [double]$AmountStr } else { 100.0 }
            Inject-Now -Amount $Amount
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        "2" {
            $AmountStr = Read-Host "Montant USD journalier a injecter (defaut: 100)"
            $Amount = if ($AmountStr -match '^\d+(\.\d+)?$') { [double]$AmountStr } else { 100.0 }
            $TimeStr  = Read-Host "Heure d execution (format HH:MM, defaut: 09:00)"
            $TimeHHMM = if ($TimeStr -match '^\d{2}:\d{2}$') { $TimeStr } else { "09:00" }
            Register-DailyTask -Amount $Amount -TimeHHMM $TimeHHMM
            # Injecter aussi immediatement pour confirmer
            Write-Host ""
            Write-Host "  Injection immediate de la premiere dose..." -ForegroundColor Yellow
            Inject-Now -Amount $Amount
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        "3" {
            Show-Header
            Show-TaskStatus
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        "4" {
            Remove-DailyTask
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        "5" {
            Write-Host "`nFermeture de l interface. Le credit journalier continue en arriere-plan." -ForegroundColor Green
            break
        }
        "6" {
            $AmountStr = Read-Host "Montant USD a retirer (defaut: 10)"
            $Amount = if ($AmountStr -match '^\d+(\.\d+)?$') { [double]$AmountStr } else { 10.0 }
            $WithdrawScript = Join-Path $ScriptDir "withdraw_payment.py"
            $Output = & $PythonExe $WithdrawScript $Amount.ToString('F2',[System.Globalization.CultureInfo]::InvariantCulture) 2> $null
            Write-Host $Output -ForegroundColor White
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        "7" {
            $ListScript = Join-Path $ScriptDir "list_payments.py"
            $Output = & $PythonExe $ListScript 2> $null
            Write-Host $Output -ForegroundColor White
            Read-Host "`nAppuyez sur Entree pour continuer"
        }
        default {
            Write-Host "`n[!] Option invalide." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }

    if ($Choice -eq "5") { break }
}
