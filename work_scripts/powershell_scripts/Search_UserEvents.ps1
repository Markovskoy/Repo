# Скрипт: Search-UserEvents.ps1
# Описание: Поиск событий в системных журналах Windows по имени пользователя
# Параметры: 
#   -UserName: имя пользователя для поиска (по умолчанию: ***)
#   -Domain: домен пользователя (по умолчанию: ***)
#   -Days: количество дней для поиска (по умолчанию: 7)
#   -OutputPath: путь для сохранения результатов

param (
    [string]$UserName = "***",
    [string]$Domain = "***",
    [int]$Days = 7,
    [string]$OutputPath = "C:\Temp\UserEvents.csv"
)

# Получаем список всех доступных журналов событий
$logs = Get-WinEvent -ListLog * | Select-Object -ExpandProperty LogName
$results = @()

# Формируем регулярное выражение для поиска
$searchPattern = "$UserName|$Domain\\$UserName"

# Ищем события во всех журналах
foreach ($log in $logs) {
    try {
        $events = Get-WinEvent -FilterHashtable @{
            LogName = $log
            StartTime = (Get-Date).AddDays(-$Days)
        } | Where-Object { $_.Message -match $searchPattern }

        if ($events) {
            $results += $events | Select-Object @{
                Name = "LogName"; Expression = {$log}
            }, TimeCreated, Id, LevelDisplayName, Message
        }
    } catch {
        Write-Warning "Не удалось получить данные из журнала $log : $_"
    }
}

$results | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
Write-Host "Результаты успешно сохранены в $OutputPath"
