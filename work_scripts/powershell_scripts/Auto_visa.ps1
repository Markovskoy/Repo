# Загрузка пользовательского модуля SOAP-запросов (пример)
Import-Module "$PSScriptRoot\Modules\InvokeCustomSOAP.psm1" 

[int]$exitcode = 20 
[string]$outputerrorstring = "" 
[bool]$iserror = $false 

# Пример условной проверки ролей
if ($roles -match "Support_Incidents") { 
    $CaseId = (Invoke-CustomSOAP Get-Case -number $ticketNumber).CaseId 

    # SQL-запрос на получение виз из кейса
    $getVisasQuery = @"
        SELECT vr.Name 
        FROM VisasInCase vic
        LEFT JOIN VisaRoles vr ON vr.Id = vic.VisaRoleId
        WHERE vic.CaseId = '$($CaseId)'
"@

    $visaCheck = Invoke-MSSQL -Server $db_host -Database $db_name -SQLCommand $getVisasQuery 

    if ($visaCheck.Name -inotcontains "Support_Incidents_Visa") {
        $getOwnerQuery = @"
            SELECT u.Name 
            FROM VisasInCase vic
            LEFT JOIN Users u ON u.Id = vic.VisaOwnerId
            WHERE vic.VisaOwnerId IS NOT NULL AND vic.CaseId = '$($CaseId)'
"@
        $approver = (Invoke-MSSQL -Server $db_host -Database $db_name -SQLCommand $getOwnerQuery).Name

        Invoke-CustomSOAP Add-Visa -caseid $CaseId -isrole $true -visarole "Support_Incidents_Visa"
        Invoke-CustomSOAP Set-Visa -caseid $CaseId -login $approver -visastatus 'Approved'
        exit
    }
}

try {
    $outputerrorstring = "Group added, approval completed"
} catch {
    $iserror = $true
} finally {
    if ($iserror) {
        $errortext = ""
        $error | ForEach-Object { $errortext += $_.ToString() + "`n" }
        $errorMessage = @"
$($MyInvocation.InvocationName)
$($MyInvocation.Line)

$errortext
$($_)
"@

        Invoke-CustomSOAP Script-Error -err $errorMessage -number $ticketNumber | Out-Null
    }

    $caseid = (Invoke-CustomSOAP Get-Case -number $ticketNumber).CaseId
    Invoke-CustomSOAP Add-Comment -caseid $caseid -login 'SystemUser' -message $outputerrorstring | Out-Null
    Write-Host $outputerrorstring
    Write-Host $exitcode -NoNewline
    exit $exitcode
}
