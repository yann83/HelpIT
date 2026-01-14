Il semble y avoir une légère confusion dans la question. PsExec est lui-même un binaire unique de la suite Sysinternals PsTools, qui permet d'exécuter des processus sur des systèmes distématiques. La suite PsTools, en revanche, contient plusieurs utilitaires de ligne de commande pour l'administration à distance.

Voici des exemples d'utilisation et de retour pour certains des binaires les plus couramment utilisés de la suite PsTools, en ciblant le poste `TESTPC`.

Pour utiliser ces outils, vous devez généralement disposer des droits d'administrateur sur le poste distant (`TESTPC`) et les ports nécessaires (comme TCP/445 pour le partage de fichiers et d'imprimantes) doivent être ouverts sur le pare-feu du `TESTPC`.

---

### 1. PsExec - Exécuter des processus à distance

**Description :** PsExec vous permet d'exécuter des commandes et des programmes sur des systèmes distants. Il peut ouvrir une console interactive, exécuter des scripts ou installer des logiciels.

**Exemple d'utilisation :** Exécuter la commande `ipconfig` sur `TESTPC` pour afficher sa configuration réseau.

```cmd
psexec \\TESTPC ipconfig
```

**Exemple de retour :**

```
PsExec v2.43 - Execute processes remotely
Copyright (C) 2001-2023 Mark Russinovich
Sysinternals - www.sysinternals.com


Windows IP Configuration


Ethernet adapter Ethernet:

   Connection-specific DNS Suffix  . :
   IPv6 Address. . . . . . . . . . . : fe80::abcd:ef01:2345:6789%12
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1
```


---

### 2. PsKill - Terminer des processus

**Description :** PsKill permet de terminer des processus sur des ordinateurs locaux ou distants, en utilisant le nom du processus ou son ID (PID).

**Exemple d'utilisation :** Tuer toutes les instances du bloc-notes (`notepad.exe`) sur `TESTPC`.

```cmd
pskill \\TESTPC notepad.exe
```

**Exemple de retour :**

```
PsKill v1.16 - Terminate processes
Copyright (C) 1999-2016 Mark Russinovich
Sysinternals - www.sysinternals.com

Process notepad.exe with PID 1234 killed on TESTPC.
Process notepad.exe with PID 5678 killed on TESTPC.
```


---

### 3. PsList - Lister les processus

**Description :** PsList affiche des informations détaillées sur les processus en cours d'exécution sur un système local ou distant, y compris l'utilisation du CPU, de la mémoire et les informations sur les threads.

**Exemple d'utilisation :** Lister tous les processus en cours d'exécution sur `TESTPC`.

```cmd
pslist \\TESTPC
```

**Exemple de retour :**

```
PsList v1.40 - Process information lister
Copyright (C) 1999-2016 Mark Russinovich
Sysinternals - www.sysinternals.com

Process information for TESTPC:

Name                Pid Pri Thd Hnd   Priv        VM      WS   CPU Time    Elapsed Time
Idle                  0   0   1   0      0       0 K      0 K 100:00:00:00 100:00:00:00
System                4   8 100 800      4      40 K    400 K    0:00:00:10    0:01:23:45
explorer.exe       1234   8  30 500  10000    100000 K  20000 K    0:00:01:20    0:01:10:00
notepad.exe        5678   8   1  50   2000     10000 K   5000 K    0:00:00:05    0:00:01:30
...
```


---

### 4. PsService - Visualiser et contrôler les services

**Description :** PsService permet de visualiser le statut, la configuration et les dépendances des services Windows, ainsi que de les démarrer, arrêter, mettre en pause ou redémarrer sur des systèmes locaux ou distants.

**Exemple d'utilisation :** Afficher le statut du service "Spouleur d'impression" sur `TESTPC`.

```cmd
psservice \\TESTPC query spooler
```

**Exemple de retour :**

```
PsService v2.26 - Service information viewer and controller
Copyright (C) 1999-2016 Mark Russinovich
Sysinternals - www.sysinternals.com

Service information for TESTPC:

Name                 : Spooler
Display name         : Spouleur d'impression
Description          : Charge les fichiers en mémoire pour l'impression...
Path                 : C:\Windows\System32\spoolsv.exe
Start type           : Auto
Service type         : Share Process
State                : Running
Account              : LocalSystem
```


---

### 5. PsShutdown - Arrêter ou redémarrer un ordinateur

**Description :** PsShutdown permet d'initier un arrêt, un redémarrage, une déconnexion ou un verrouillage d'un système local ou distant. Il peut également annuler un arrêt en cours.

**Exemple d'utilisation :** Redémarrer `TESTPC` après un délai de 60 secondes, avec un message.

```cmd
psshutdown \\TESTPC -r -t 60 -m "Redémarrage planifié dans 1 minute."
```

**Exemple de retour (sur la machine exécutant la commande) :**

```
PsShutdown v2.60 - Shutdown, reboot, or poweroff local or remote machine
Copyright (C) 1999-2016 Mark Russinovich
Sysinternals - www.sysinternals.com

TESTPC is scheduled to reboot in 60 seconds.
```

**Exemple de retour (sur TESTPC, l'utilisateur verrait une boîte de dialogue) :**
Une boîte de dialogue s'afficherait sur `TESTPC` indiquant : "Redémarrage planifié dans 1 minute." et un compte à rebours.

---

### 6. PsInfo - Lister les informations système

**Description :** PsInfo affiche des informations détaillées sur un système, telles que la version du système d'exploitation, le temps de disponibilité (uptime), la configuration du CPU, la mémoire installée et les correctifs installés.

**Exemple d'utilisation :** Afficher les informations système de `TESTPC`.

```cmd
psinfo \\TESTPC
```

**Exemple de retour :**

```
PsInfo v1.78 - Local and remote system information viewer
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com

System information for TESTPC:
Uptime:                  1 day, 5 hours, 30 minutes, 15 seconds
Install date:            11/05/2023, 10:00:00 AM
OS version:              Microsoft Windows 10 Pro, 64-bit
Build:                   19045
Processor:               Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz
Memory:                  16384 MB
...
```


# Utilisation de PsExec pour exécuter un script distant et récupérer les résultats

Voici plusieurs méthodes pour accomplir cette tâche :

## Méthode 1 : Solution complète en une ligne

```batch
psexec \\POSTE_DISTANT -u DOMAINE\utilisateur -p motdepasse cmd /c "mkdir C:\temp & exit" && ^
copy "C:\local\script.ps1" "\\POSTE_DISTANT\C$\temp\" && ^
psexec \\POSTE_DISTANT -u DOMAINE\utilisateur -p motdepasse powershell -ExecutionPolicy Bypass -File "C:\temp\script.ps1" > "C:\temp\resultats.txt" && ^
copy "\\POSTE_DISTANT\C$\temp\resultats.txt" "C:\temp\local\"
```

## Méthode 2 : Script Batch structuré

```batch
@echo off
setlocal

REM === Configuration ===
set POSTE_DISTANT=POSTE_DISTANT
set UTILISATEUR=DOMAINE\utilisateur
set MOT_DE_PASSE=motdepasse
set SCRIPT_LOCAL=C:\scripts\monscript.ps1
set DOSSIER_DISTANT=C:\temp
set FICHIER_RESULTAT=resultats.txt
set DOSSIER_LOCAL_TEMP=C:\temp\resultats

REM === 1. Créer le dossier distant ===
echo [1/5] Creation du dossier distant...
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% cmd /c "if not exist %DOSSIER_DISTANT% mkdir %DOSSIER_DISTANT%"

REM === 2. Copier le script vers le poste distant ===
echo [2/5] Copie du script vers le poste distant...
copy "%SCRIPT_LOCAL%" "\\%POSTE_DISTANT%\C$\temp\"
if %errorlevel% neq 0 (
    echo ERREUR lors de la copie du script
    exit /b 1
)

REM === 3. Exécuter le script et rediriger la sortie ===
echo [3/5] Execution du script distant...
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% ^
    powershell -ExecutionPolicy Bypass -Command ^
    "& '%DOSSIER_DISTANT%\monscript.ps1' | Out-File -FilePath '%DOSSIER_DISTANT%\%FICHIER_RESULTAT%' -Encoding UTF8"

REM === 4. Récupérer le fichier de résultats ===
echo [4/5] Recuperation des resultats...
if not exist "%DOSSIER_LOCAL_TEMP%" mkdir "%DOSSIER_LOCAL_TEMP%"
copy "\\%POSTE_DISTANT%\C$\temp\%FICHIER_RESULTAT%" "%DOSSIER_LOCAL_TEMP%\"

REM === 5. Nettoyage (optionnel) ===
echo [5/5] Nettoyage du poste distant...
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% ^
    cmd /c "del %DOSSIER_DISTANT%\monscript.ps1 & del %DOSSIER_DISTANT%\%FICHIER_RESULTAT%"

echo.
echo === Operation terminee ===
echo Resultats disponibles dans: %DOSSIER_LOCAL_TEMP%\%FICHIER_RESULTAT%
pause
```

## Méthode 3 : Script PowerShell (plus moderne)

```powershell
# === Configuration ===
$posteDistant = "POSTE_DISTANT"
$credential = Get-Credential # ou créer l'objet manuellement
$scriptLocal = "C:\scripts\monscript.ps1"
$dossierDistant = "C:\temp"
$fichierResultat = "resultats.txt"
$dossierLocalTemp = "C:\temp\resultats"

# === 1. Créer le dossier distant ===
Write-Host "[1/5] Création du dossier distant..." -ForegroundColor Cyan
psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
    cmd /c "if not exist $dossierDistant mkdir $dossierDistant"

# === 2. Copier le script ===
Write-Host "[2/5] Copie du script..." -ForegroundColor Cyan
$destinationUNC = "\\$posteDistant\C$\temp\monscript.ps1"
Copy-Item -Path $scriptLocal -Destination $destinationUNC -Force

# === 3. Exécuter le script ===
Write-Host "[3/5] Exécution du script distant..." -ForegroundColor Cyan
psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
    powershell -ExecutionPolicy Bypass -Command `
    "& '$dossierDistant\monscript.ps1' | Out-File -FilePath '$dossierDistant\$fichierResultat' -Encoding UTF8"

# === 4. Récupérer les résultats ===
Write-Host "[4/5] Récupération des résultats..." -ForegroundColor Cyan
if (!(Test-Path $dossierLocalTemp)) {
    New-Item -ItemType Directory -Path $dossierLocalTemp | Out-Null
}
Copy-Item -Path "\\$posteDistant\C$\temp\$fichierResultat" -Destination $dossierLocalTemp -Force

# === 5. Nettoyage ===
Write-Host "[5/5] Nettoyage..." -ForegroundColor Cyan
psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
    cmd /c "del $dossierDistant\monscript.ps1 & del $dossierDistant\$fichierResultat"

Write-Host "`n=== Opération terminée ===" -ForegroundColor Green
Write-Host "Résultats disponibles dans: $dossierLocalTemp\$fichierResultat"
```

## Méthode 4 : Sans copie de fichier (exécution directe)

```batch
REM Exécuter directement depuis le partage réseau
psexec \\POSTE_DISTANT -u DOMAINE\utilisateur -p motdepasse ^
    powershell -ExecutionPolicy Bypass -File "\\SERVEUR\partage\script.ps1" ^
    > C:\temp\resultats.txt
```

## Points importants à vérifier :

1. **Partage administratif activé** : `C$` doit être accessible
2. **Pare-feu** : Port 445 (SMB) ouvert
3. **Droits d'administration** sur le poste distant
4. **Service Remote Registry** : Démarré si nécessaire
5. **UAC** : Peut nécessiter `-h` avec PsExec pour élévation

## Options utiles de PsExec :

- `-s` : Exécuter en tant que SYSTEM
- `-i` : Mode interactif
- `-d` : Ne pas attendre la fin de l'exécution
- `-c` : Copier automatiquement l'exécutable spécifié
- `-h` : Exécuter avec élévation de privilèges (si UAC actif)

**Conseil** : Pour des déploiements en production, considérez PowerShell Remoting (WinRM) qui est plus moderne et sécurisé.

# Script PowerShell pour récupérer les numéros de série des écrans

## 1. Script PowerShell (Get-MonitorSerials.ps1)

```powershell
<#
.SYNOPSIS
    Récupère les numéros de série des écrans connectés au PC
.DESCRIPTION
    Ce script utilise WMI pour interroger les informations EDID des moniteurs
    et génère un fichier texte avec les résultats
.NOTES
    Auteur: Admin
    Date: 2024
#>

# Configuration
$outputFile = "C:\temp\monitor_serials.txt"
$computerName = $env:COMPUTERNAME
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Créer le dossier si nécessaire
$outputDir = Split-Path $outputFile -Parent
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Fonction pour décoder les données EDID
function Get-MonitorInfo {
    $monitors = @()
    
    try {
        # Méthode 1 : Via WmiMonitorID (la plus fiable)
        $monitorIDs = Get-WmiObject -Namespace root\wmi -Class WmiMonitorID -ErrorAction SilentlyContinue
        
        foreach ($monitor in $monitorIDs) {
            $monitorInfo = [PSCustomObject]@{
                Manufacturer = ($monitor.ManufacturerName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
                ProductCode  = ($monitor.ProductCodeID | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
                SerialNumber = ($monitor.SerialNumberID | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
                UserFriendlyName = ($monitor.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
                WeekOfManufacture = $monitor.WeekOfManufacture
                YearOfManufacture = $monitor.YearOfManufacture
                Active = $monitor.Active
            }
            $monitors += $monitorInfo
        }
    }
    catch {
        Write-Warning "Erreur lors de la récupération via WmiMonitorID: $_"
    }
    
    # Méthode 2 : Via le registre (backup)
    if ($monitors.Count -eq 0) {
        try {
            $regPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\DISPLAY"
            $displays = Get-ChildItem $regPath -Recurse -ErrorAction SilentlyContinue | 
                        Where-Object { $_.PSChildName -match "^\d+" }
            
            foreach ($display in $displays) {
                $deviceDesc = (Get-ItemProperty -Path $display.PSPath -Name "DeviceDesc" -ErrorAction SilentlyContinue).DeviceDesc
                $hardwareID = (Get-ItemProperty -Path $display.PSPath -Name "HardwareID" -ErrorAction SilentlyContinue).HardwareID
                
                if ($deviceDesc -or $hardwareID) {
                    $monitorInfo = [PSCustomObject]@{
                        Manufacturer = "N/A"
                        ProductCode  = "N/A"
                        SerialNumber = if ($hardwareID) { $hardwareID[0] } else { "N/A" }
                        UserFriendlyName = if ($deviceDesc) { $deviceDesc } else { "N/A" }
                        WeekOfManufacture = "N/A"
                        YearOfManufacture = "N/A"
                        Active = $true
                    }
                    $monitors += $monitorInfo
                }
            }
        }
        catch {
            Write-Warning "Erreur lors de la récupération via le registre: $_"
        }
    }
    
    return $monitors
}

# Fonction pour formater la sortie
function Format-Output {
    param($monitors)
    
    $output = @()
    $output += "=" * 80
    $output += "INFORMATIONS DES ECRANS CONNECTES"
    $output += "=" * 80
    $output += "Ordinateur: $computerName"
    $output += "Date/Heure: $date"
    $output += "Nombre d'écrans détectés: $($monitors.Count)"
    $output += "=" * 80
    $output += ""
    
    if ($monitors.Count -eq 0) {
        $output += "AUCUN ECRAN DETECTE"
        $output += ""
        $output += "Vérifiez que:"
        $output += "  - Le script est exécuté avec les droits administrateur"
        $output += "  - Les pilotes d'affichage sont correctement installés"
        $output += "  - Les écrans supportent EDID"
    }
    else {
        $counter = 1
        foreach ($monitor in $monitors) {
            $output += "ECRAN #$counter"
            $output += "-" * 80
            $output += "  Fabricant          : $($monitor.Manufacturer)"
            $output += "  Nom du modèle      : $($monitor.UserFriendlyName)"
            $output += "  Code produit       : $($monitor.ProductCode)"
            $output += "  Numéro de série    : $($monitor.SerialNumber)"
            $output += "  Année fabrication  : $($monitor.YearOfManufacture)"
            $output += "  Semaine fabrication: $($monitor.WeekOfManufacture)"
            $output += "  Actif              : $($monitor.Active)"
            $output += ""
            $counter++
        }
    }
    
    $output += "=" * 80
    $output += "FIN DU RAPPORT"
    $output += "=" * 80
    
    return $output
}

# Exécution principale
try {
    Write-Host "Récupération des informations des écrans..." -ForegroundColor Cyan
    
    $monitors = Get-MonitorInfo
    $output = Format-Output -monitors $monitors
    
    # Écrire dans le fichier
    $output | Out-File -FilePath $outputFile -Encoding UTF8 -Force
    
    # Afficher également à l'écran
    $output | ForEach-Object { Write-Host $_ }
    
    Write-Host "`nFichier de sortie créé: $outputFile" -ForegroundColor Green
    
    # Code de sortie
    exit 0
}
catch {
    $errorMsg = "ERREUR: $_"
    Write-Host $errorMsg -ForegroundColor Red
    $errorMsg | Out-File -FilePath $outputFile -Encoding UTF8 -Force
    exit 1
}
```

## 2. Version simplifiée (Get-MonitorSerials-Simple.ps1)

```powershell
# Version courte et directe
$outputFile = "C:\temp\monitor_serials.txt"
$result = @()

$result += "=== Numéros de série des écrans - $(Get-Date) ==="
$result += "Ordinateur: $env:COMPUTERNAME"
$result += ""

Get-WmiObject -Namespace root\wmi -Class WmiMonitorID | ForEach-Object {
    $manufacturer = ($_.ManufacturerName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    $name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    $serial = ($_.SerialNumberID | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    
    $result += "Fabricant: $manufacturer"
    $result += "Modèle: $name"
    $result += "Numéro de série: $serial"
    $result += "---"
}

$result | Out-File -FilePath $outputFile -Encoding UTF8
Write-Host "Fichier créé: $outputFile"
```

## 3. Commandes PsExec pour exécution distante

### Option A : Script Batch complet

```batch
@echo off
setlocal EnableDelayedExpansion

REM ========================================
REM Configuration
REM ========================================
set POSTE_DISTANT=PC-DISTANT-01
set DOMAINE=MONDOMAINE
set UTILISATEUR=%DOMAINE%\administrateur
set MOT_DE_PASSE=VotreMotDePasse

set SCRIPT_LOCAL=C:\scripts\Get-MonitorSerials.ps1
set SCRIPT_NAME=Get-MonitorSerials.ps1
set DOSSIER_DISTANT=C:\temp
set FICHIER_RESULTAT=monitor_serials.txt
set DOSSIER_LOCAL_RESULTATS=C:\resultats_monitoring

REM ========================================
echo.
echo ====================================================
echo   RECUPERATION DES NUMEROS DE SERIE DES ECRANS
echo   Poste cible: %POSTE_DISTANT%
echo ====================================================
echo.

REM === 1. Vérifier la connectivité ===
echo [1/7] Verification de la connectivite...
ping %POSTE_DISTANT% -n 1 -w 1000 >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Le poste %POSTE_DISTANT% n'est pas accessible
    pause
    exit /b 1
)
echo [OK] Poste accessible

REM === 2. Créer le dossier distant ===
echo [2/7] Creation du dossier distant...
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% -accepteula ^
    cmd /c "if not exist %DOSSIER_DISTANT% mkdir %DOSSIER_DISTANT%"
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de creer le dossier distant
    pause
    exit /b 1
)
echo [OK] Dossier cree

REM === 3. Copier le script PowerShell ===
echo [3/7] Copie du script vers le poste distant...
copy "%SCRIPT_LOCAL%" "\\%POSTE_DISTANT%\C$\temp\%SCRIPT_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de copier le script
    pause
    exit /b 1
)
echo [OK] Script copie

REM === 4. Exécuter le script PowerShell ===
echo [4/7] Execution du script distant...
echo     (Cela peut prendre quelques secondes...)
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% -h ^
    powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%DOSSIER_DISTANT%\%SCRIPT_NAME%"
if %errorlevel% neq 0 (
    echo [AVERTISSEMENT] Le script a retourne un code d'erreur
)
echo [OK] Script execute

REM === 5. Vérifier l'existence du fichier de résultats ===
echo [5/7] Verification du fichier de resultats...
if not exist "\\%POSTE_DISTANT%\C$\temp\%FICHIER_RESULTAT%" (
    echo [ERREUR] Le fichier de resultats n'a pas ete cree
    pause
    exit /b 1
)
echo [OK] Fichier de resultats present

REM === 6. Récupérer le fichier de résultats ===
echo [6/7] Recuperation des resultats...
if not exist "%DOSSIER_LOCAL_RESULTATS%" mkdir "%DOSSIER_LOCAL_RESULTATS%"

REM Créer un nom de fichier avec horodatage
set TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set FICHIER_LOCAL=%DOSSIER_LOCAL_RESULTATS%\%POSTE_DISTANT%_%FICHIER_RESULTAT:~0,-4%_%TIMESTAMP%.txt

copy "\\%POSTE_DISTANT%\C$\temp\%FICHIER_RESULTAT%" "%FICHIER_LOCAL%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de recuperer les resultats
    pause
    exit /b 1
)
echo [OK] Resultats recuperes

REM === 7. Nettoyage du poste distant ===
echo [7/7] Nettoyage du poste distant...
psexec \\%POSTE_DISTANT% -u %UTILISATEUR% -p %MOT_DE_PASSE% ^
    cmd /c "del /Q %DOSSIER_DISTANT%\%SCRIPT_NAME% & del /Q %DOSSIER_DISTANT%\%FICHIER_RESULTAT%"
echo [OK] Nettoyage effectue

REM === Affichage des résultats ===
echo.
echo ====================================================
echo   OPERATION TERMINEE AVEC SUCCES
echo ====================================================
echo.
echo Fichier de resultats: %FICHIER_LOCAL%
echo.
echo Contenu du fichier:
echo ----------------------------------------------------
type "%FICHIER_LOCAL%"
echo ----------------------------------------------------
echo.
pause
```

### Option B : Script PowerShell complet

```powershell
<#
.SYNOPSIS
    Déploie et exécute le script de récupération des numéros de série sur un poste distant
#>

# ========================================
# Configuration
# ========================================
$posteDistant = "PC-DISTANT-01"
$utilisateur = "DOMAINE\administrateur"
$motDePasse = "VotreMotDePasse" | ConvertTo-SecureString -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($utilisateur, $motDePasse)

$scriptLocal = "C:\scripts\Get-MonitorSerials.ps1"
$scriptName = "Get-MonitorSerials.ps1"
$dossierDistant = "C:\temp"
$fichierResultat = "monitor_serials.txt"
$dossierLocalResultats = "C:\resultats_monitoring"

# ========================================
# Fonctions
# ========================================
function Write-Step {
    param($step, $total, $message)
    Write-Host "[$step/$total] $message" -ForegroundColor Cyan
}

function Write-Success {
    param($message)
    Write-Host "[OK] $message" -ForegroundColor Green
}

function Write-Error {
    param($message)
    Write-Host "[ERREUR] $message" -ForegroundColor Red
}

# ========================================
# Exécution
# ========================================
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "  RECUPERATION DES NUMEROS DE SERIE DES ECRANS" -ForegroundColor Yellow
Write-Host "  Poste cible: $posteDistant" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host ""

try {
    # 1. Vérifier la connectivité
    Write-Step 1 7 "Vérification de la connectivité..."
    if (!(Test-Connection -ComputerName $posteDistant -Count 1 -Quiet)) {
        throw "Le poste $posteDistant n'est pas accessible"
    }
    Write-Success "Poste accessible"

    # 2. Créer le dossier distant
    Write-Step 2 7 "Création du dossier distant..."
    $createFolder = "cmd /c `"if not exist $dossierDistant mkdir $dossierDistant`""
    & psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
        -accepteula $createFolder 2>&1 | Out-Null
    Write-Success "Dossier créé"

    # 3. Copier le script
    Write-Step 3 7 "Copie du script vers le poste distant..."
    $destination = "\\$posteDistant\C$\temp\$scriptName"
    Copy-Item -Path $scriptLocal -Destination $destination -Force -ErrorAction Stop
    Write-Success "Script copié"

    # 4. Exécuter le script
    Write-Step 4 7 "Exécution du script distant..."
    Write-Host "     (Cela peut prendre quelques secondes...)" -ForegroundColor Gray
    $executeScript = "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$dossierDistant\$scriptName`""
    & psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
        -h $executeScript 2>&1 | Out-Null
    Write-Success "Script exécuté"

    # 5. Vérifier le fichier de résultats
    Write-Step 5 7 "Vérification du fichier de résultats..."
    Start-Sleep -Seconds 2
    $fichierDistant = "\\$posteDistant\C$\temp\$fichierResultat"
    if (!(Test-Path $fichierDistant)) {
        throw "Le fichier de résultats n'a pas été créé"
    }
    Write-Success "Fichier de résultats présent"

    # 6. Récupérer les résultats
    Write-Step 6 7 "Récupération des résultats..."
    if (!(Test-Path $dossierLocalResultats)) {
        New-Item -ItemType Directory -Path $dossierLocalResultats -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $fichierLocal = Join-Path $dossierLocalResultats "$posteDistant`_monitor_serials_$timestamp.txt"
    Copy-Item -Path $fichierDistant -Destination $fichierLocal -Force -ErrorAction Stop
    Write-Success "Résultats récupérés"

    # 7. Nettoyage
    Write-Step 7 7 "Nettoyage du poste distant..."
    $cleanup = "cmd /c `"del /Q $dossierDistant\$scriptName & del /Q $dossierDistant\$fichierResultat`""
    & psexec \\$posteDistant -u $credential.UserName -p $credential.GetNetworkCredential().Password `
        $cleanup 2>&1 | Out-Null
    Write-Success "Nettoyage effectué"

    # Afficher les résultats
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "  OPERATION TERMINEE AVEC SUCCES" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "Fichier de résultats: " -NoNewline
    Write-Host $fichierLocal -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Contenu du fichier:" -ForegroundColor Cyan
    Write-Host ("-" * 60)
    Get-Content $fichierLocal | ForEach-Object { Write-Host $_ }
    Write-Host ("-" * 60)
    
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

Write-Host ""
```

### Option C : Commandes PsExec en ligne (rapide)

```batch
REM Version courte - tout en une ligne
psexec \\PC-DISTANT -u DOMAINE\admin -p password -accepteula cmd /c "mkdir C:\temp" && ^
copy "C:\scripts\Get-MonitorSerials.ps1" "\\PC-DISTANT\C$\temp\" && ^
psexec \\PC-DISTANT -u DOMAINE\admin -p password -h powershell -ExecutionPolicy Bypass -File "C:\temp\Get-MonitorSerials.ps1" && ^
copy "\\PC-DISTANT\C$\temp\monitor_serials.txt" "C:\resultats\" && ^
type "C:\resultats\monitor_serials.txt"
```

### Option D : Pour plusieurs postes (batch)

```batch
@echo off
REM Liste des postes dans un fichier texte
set LISTE_POSTES=C:\scripts\postes.txt
set UTILISATEUR=DOMAINE\admin
set MOT_DE_PASSE=password

for /F "tokens=*" %%A in (%LISTE_POSTES%) do (
    echo.
    echo ========================================
    echo Traitement de: %%A
    echo ========================================
    
    REM Copier
    copy "C:\scripts\Get-MonitorSerials.ps1" "\\%%A\C$\temp\" >nul 2>&1
    
    REM Exécuter
    psexec \\%%A -u %UTILISATEUR% -p %MOT_DE_PASSE% -h ^
        powershell -ExecutionPolicy Bypass -File "C:\temp\Get-MonitorSerials.ps1"
    
    REM Récupérer
    copy "\\%%A\C$\temp\monitor_serials.txt" "C:\resultats\%%A_monitors.txt" >nul 2>&1
    
    REM Nettoyer
    psexec \\%%A -u %UTILISATEUR% -p %MOT_DE_PASSE% cmd /c "del C:\temp\Get-MonitorSerials.ps1 & del C:\temp\monitor_serials.txt"
    
    echo [OK] Termine pour %%A
)

echo.
echo === TOUS LES POSTES TRAITES ===
pause
```

## 4. Prérequis et vérifications

### Checklist avant exécution :

```powershell
# Script de vérification des prérequis
$posteDistant = "PC-DISTANT-01"

Write-Host "Vérification des prérequis..." -ForegroundColor Cyan

# 1. Connectivité réseau
if (Test-Connection -ComputerName $posteDistant -Count 1 -Quiet) {
    Write-Host "[OK] Connectivité réseau" -ForegroundColor Green
} else {
    Write-Host "[KO] Pas de connectivité réseau" -ForegroundColor Red
}

# 2. Partage administratif C$
if (Test-Path "\\$posteDistant\C$") {
    Write-Host "[OK] Partage C$ accessible" -ForegroundColor Green
} else {
    Write-Host "[KO] Partage C$ inaccessible" -ForegroundColor Red
}

# 3. PsExec disponible
if (Get-Command psexec -ErrorAction SilentlyContinue) {
    Write-Host "[OK] PsExec disponible" -ForegroundColor Green
} else {
    Write-Host "[KO] PsExec non trouvé" -ForegroundColor Red
    Write-Host "     Télécharger depuis: https://live.sysinternals.com/psexec.exe"
}

# 4. Service Remote Registry
$service = Get-Service -ComputerName $posteDistant -Name RemoteRegistry -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq 'Running') {
    Write-Host "[OK] Service Remote Registry actif" -ForegroundColor Green
} else {
    Write-Host "[WARN] Service Remote Registry arrêté (peut nécessiter activation)" -ForegroundColor Yellow
}
```

## 5. Exemple de fichier postes.txt pour traitement en masse

```text
PC-BUREAU-01
PC-BUREAU-02
PC-BUREAU-03
LAPTOP-SALES-01
LAPTOP-SALES-02
```

Ces scripts vous permettent de récupérer facilement les numéros de série des écrans sur des postes distants de manière automatisée !

