import signal
interval = 1.0
ticks = 0
def alarm_handler(signo,frame):
    global ticks
    print "Alarm ", ticks
    ticks = ticks + 1
    signal.alarm(interval)                # Schedule a new alarm

signal.signal(signal.SIGALRM, alarm_handler)
signal.alarm(interval)
# Spin forever--should see handler being called every second
while 1:
    pass
