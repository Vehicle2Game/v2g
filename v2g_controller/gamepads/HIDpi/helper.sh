sleep 10
service bluetooth stop
/etc/init.d/bluetooth stop
/usr/sbin/bluetoothd --nodetach --debug -p time 


if [ "$(bluetoothctl devices | head -n 1 | awk 'BEGIN { FS = "[ =]" } { print $2 }')" != "" ]; then
    bluetoothctl remove "$(bluetoothctl devices | head -n 1 | awk 'BEGIN { FS = "[ =]" } { print $2 }')"
fi
if [ "$(bluetoothctl devices | head -n 1 | awk 'BEGIN { FS = "[ =]" } { print $2 }')" != "" ]; then
    bluetoothctl remove "$(bluetoothctl devices | head -n 1 | awk 'BEGIN { FS = "[ =]" } { print $2 }')"
fi