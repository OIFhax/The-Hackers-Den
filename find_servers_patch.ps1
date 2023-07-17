$computers = Get-Content -Path "C:\path\to\your\file.txt" # replace with your file path
$ldapServer = "ldap://your.ldap.server" # replace with your LDAP server
$results = @()

foreach ($computer in $computers) {
    try {
        $searcher = New-Object System.DirectoryServices.DirectorySearcher
        $searcher.SearchRoot = New-Object System.DirectoryServices.DirectoryEntry($ldapServer)
        $searcher.Filter = "(sAMAccountName=$computer$)"
        $result = $searcher.FindOne()

        if ($result -ne $null) {
            $osInfo = New-Object PSObject -Property @{
                ComputerName = $computer
                OSName = $result.Properties["operatingsystem"][0]
                ServicePack = $result.Properties["operatingsystemservicepack"][0]
            }
            $results += $osInfo
        } else {
            Write-Error "Failed to find $computer on the LDAP server"
        }
    } catch {
        Write-Error "Failed to get OS info from ${computer}: $_"
    }
}

$results | Export-Csv -Path "C:\path\to\your\output.csv" -NoTypeInformation # replace with your output file path
