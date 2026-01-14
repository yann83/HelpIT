Faisons une class python 3 pour inclure toutes ces commandes.

Le point commun de ces commandes est l'executable PsExec64.exe qui se trouve dans .\bin à partir du dossier où se trouve le scrypt ptyhon
Pour toutes les commandes il y a toujours les même arguments : -accepteula \\<ipadress> où est une variable

J'ai besoin de ces commandes :

Celle-ci ouvre un terminal

PsExec64.exe -accepteula \\<ipadress> cmd.exe
___
Celle ci doit m'obtenir la valeur <valeur> , exemple : CN=Poste,OU=Centre,OU=Departement,OU=Direction,OU=Direction,OU=Postes,OU=ORG,OU=As,DC=cn,DC=loc

PsExec64.exe -accepteula \\<ipadress> -s reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine" /v "Distinguished-Name"

elle renvoie

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy\State\Machine
    Distinguished-Name    REG_SZ    <valeur>

reg exited on <ipadress> with error code 0.

___
Celle ci doit m'obtenir la valeur <valeur> , exemple : Windows 10 Pro

PsExec64.exe -accepteula \\<ipadress> -s reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName

elle renvoie

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
    ProductName    REG_SZ    <valeur>

reg exited on <ipadress> with error code 0.
___
Celle ci doit m'obtenir la valeur <valeur> , exemple : 22H2

PsExec64.exe -accepteula \\<ipadress> -s reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v displayversion

elle renvoie

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
    displayversion    REG_SZ    <valeur>

reg exited on <ipadress> with error code 0.
___
Celle ci doit m'obtenir la valeur <valeur> où l'ETAT est Actif , exemple : utilisateur-02566

PsExec64.exe -accepteula \\<ipadress> quser

elle renvoie

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com


 UTILISATEUR           SESSION            ID  ÉTAT    TEMPS INACT TEMPS SESSION
 <valeur>          console             1  Actif       aucun   23/10/2025 08:42
quser exited on <ipadress> with error code 0.
___
Celle ci doit m'obtenir une liste qui est enregistré au fomat csv dans .\tmp avec comme nom <ipadress>_processus , et écrase le fichier existant. Il y a 1 colonne : name, et les noms en plusieurs exemplaire deviennent unique.

PsExec64.exe -accepteula \\<ipadress> powershell "Get-Process | Where-Object { $_.Name -notin @('System','svchost','wininit','lsass','services','csrss','smss','winlogon') } | Select-Object Name,Id"

elle renvoie par exemple

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



Name                              Id
----                              --
acumbrellaagent                 5872
AppHelperCap                    2856
ApplicationFrameHost           13664
bdredline                       6008
Calculator                     16160
cmd                             1528
cmd                             3924
cmd                            15776
conhost                         5360
conhost                         5580
conhost                        11396
conhost                        11948
conhost                        13244
conhost                        13260
[…]
EsWirelessCtrl                  4624
explorer                        4128
firefox                         2608
firefox                         3284
firefox                         7916
firefox                         9148
firefox                        10188
firefox                        10308
firefox                        14804
firefox                        15604
firefox                        15672
firefox                        16112
FMService64                     6080
fontdrvhost                     1028
fontdrvhost                     1036
[…]
fvenotify                        812
[…]
Webview2Agent                 12328


powershell exited on <ipadress> with error code 0.

mon fichier csv contiendra par exemple : 
name
acumbrellaagent
AppHelperCap
ApplicationFrameHost
bdredline
Calculator
cmd
conhost
[…]
EsWirelessCtrl
explorer
firefox
FMService64
fontdrvhost
[…]
fvenotify
[…]
Webview2Agent
__

Celle ci doit s'éxecuter avec la variable <valeur>

PsExec64.exe -accepteula \\<ipadress> taskkill /IM <valeur> /F

elle renvoie 1 si "Opération réussie" est vrai au moins une fois sinon 0

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com


Opération réussie : le processus "firefox.exe" de PID 3284 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 16112 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 9148 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 14804 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 15604 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 10308 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 10188 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 15672 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 2608 a été arrêté.
Opération réussie : le processus "firefox.exe" de PID 7916 a été arrêté.
taskkill exited on <ipadress> with error code 0.

___
Celle ci doit m'obtenir une liste qui est enregistré au fomat csv dans .\tmp avec comme nom <ipadress>_services , et écrase le fichier existant. Il y a 1 colonne : id, name et une colonne etat

PsExec64.exe -accepteula \\<ipadress> sc query state= all

elle renvoie par exemple

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



SERVICE_NAME: AdobeARMservice
DISPLAY_NAME: Adobe Acrobat Update Service
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 1  STOPPED
        WIN32_EXIT_CODE    : 1077  (0x435)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0

SERVICE_NAME: AdobeFlashPlayerUpdateSvc
DISPLAY_NAME: Adobe Flash Player Update Service
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
        WIN32_EXIT_CODE    : 1077  (0x435)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0

[…]

SERVICE_NAME: UdkUserSvc_1948c7
DISPLAY_NAME: Service utilisateur du kit de développement sans station d'accueil_1948c7
        TYPE               : e0  USER_SHARE_PROCESS INSTANCE
        STATE              : 1  STOPPED
        WIN32_EXIT_CODE    : 1077  (0x435)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
sc exited on <ipadress> with error code 0.

mon fichier csv contiendra par exemple : 
id;name;etat
AdobeARMservice;Adobe Acrobat Update Service;STOPPED
AdobeFlashPlayerUpdateSvc;Adobe Flash Player Update Service;RUNNING

Voici les valeurs possibles de STATE (colonne Name)
Name 	Value 	Description
Stopped 	1 	

The service is not running. This corresponds to the Win32 SERVICE_STOPPED constant, which is defined as 0x00000001.
StartPending 	2 	

The service is starting. This corresponds to the Win32 SERVICE_START_PENDING constant, which is defined as 0x00000002.
StopPending 	3 	

The service is stopping. This corresponds to the Win32 SERVICE_STOP_PENDING constant, which is defined as 0x00000003.
Running 	4 	

The service is running. This corresponds to the Win32 SERVICE_RUNNING constant, which is defined as 0x00000004.
ContinuePending 	5 	

The service continue is pending. This corresponds to the Win32 SERVICE_CONTINUE_PENDING constant, which is defined as 0x00000005.
PausePending 	6 	

The service pause is pending. This corresponds to the Win32 SERVICE_PAUSE_PENDING constant, which is defined as 0x00000006.
Paused 	7 	

.........02The service is paused. This corresponds to the Win32 SERVICE_PAUSED constant, which is defined as 0x00000007.
___

Voir le statut du service
Celle ci doit m'obtenir la valeur <valeur> avec la variable <service>, par exemple : RUNNING.
Si c'est RUNNING cela renverra 1 sinon 0

PsExec64.exe -accepteula \\<ipadress> sc query <service>

elle renvoie

PsExec v2.2 - Execute processes remotely
Copyright (C) 2001-2016 Mark Russinovich
Sysinternals - www.sysinternals.com



SERVICE_NAME: wuauserv
        TYPE               : 30  WIN32
        STATE              : 4  <valeur>
                                (STOPPABLE, NOT_PAUSABLE, ACCEPTS_PRESHUTDOWN)
        WIN32_EXIT_CODE    : 0  (0x0)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
sc exited on <ipadress> with error code 0.
___

Démarrer le service
Celle ci doit s'executer avec la variable <service>

PsExec64.exe -accepteula \\<ipadress> sc start <service>
___
Arrêter le service
Celle ci doit s'executer avec la variable <service>

PsExec64.exe -accepteula \\<ipadress> sc stop <service>
___
Redémarrer le service
Celle ci doit s'executer avec la variable <service>

PsExec64.exe -accepteula \\<ipadress> cmd /c "sc stop <service> && sc start <service>"

