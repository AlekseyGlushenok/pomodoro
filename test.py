# pomodoro timer
# todo-list:
# 1) show current time cycle and time remaining
# 2) refactoring and code style
# 3) save settings beetwin sessions
# bug(possible not but doesn't work as i wont)
# 1) close settings work incorrect(second open empty window)
# 2) if lib App Indicator doesn't install programm break with fatal, should be the hint message for install depth


import signal
import os
import gi
import time
from multiprocessing import Process
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, Gdk
from gi.repository import Notify

DEFAULT_ACTIVITY_TIMER=30
DEFAULT_HARD_ACTIVITY_TIMER=10
DEFAULT_TIMEOUT_TIMER=2
DEFAULT_SCREEN_LOCK=True

APPID = "GTK Test"
CURRDIR = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(CURRDIR, 'icon.png')

class TrayIcon:

    def __init__(self, appid, icon, menu):
        self.menu = menu

        try:
            from gi.repository import AyatanaAppIndicator3 as AppIndicator
        except ImportError:
            try:
                from gi.repository import AppIndicator3 as AppIndicator
            except ImportError:
                from gi.repository import AppIndicator

        self.ind = AppIndicator.Indicator.new(
            appid, icon,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_menu(self.menu)

    def onPopupMenu(self, icon, button, time):
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, icon,
                        button, time)


class Handler:
    def __init__(self, timer, overlay, settings):
        self.timer = timer
        self.overlay = overlay
        self.settings = settings
        self.clock = builder.get_object('clock')
        self.screenLock = False
        self.lockAvailable = DEFAULT_SCREEN_LOCK

    def onQuit(self, *args):
        Notify.uninit()
        Gtk.main_quit()

    def showSettings(self, *args):
        # unlock screen
        if (self.screenLock):
            self.toggleScreen()
        
        # stop timer
        timer.stop()
        
        # init settings field
        activityTimer = builder.get_object('activityTime')
        activityTimer.set_text(str(timer.activityTimer))
        
        hardActivityTimer = builder.get_object('hardActivity')
        hardActivityTimer.set_text(str(timer.hardActivityTimer))
        
        timeout = builder.get_object('timeout')
        timeout.set_text(str(timer.timeout))
        
        screenLock = builder.get_object('lock')
        screenLock.set_active(self.lockAvailable)
        
        self.settings.show_all()

    def setActivityTimer(self, input):
        if input.get_text() != '':
            self.timer.activityTimer = int(input.get_text())

    def setHardActivityTimer(self, input):
        if input.get_text() != '':
            self.timer.hardActivityTimer = int(input.get_text())

    def setTimeout(self, input):
        if input.get_text() != '':
            self.timer.timeout = int(input.get_text())

    def lockScreenToggle(self, input):
        self.lockAvailable = input.get_active()
        print(self.lockAvailable)

    def notify(self, msg):
        Notify.Notification.new("Notification", msg, ICON).show()

    def toggleScreen(self):
        # if lock unavaliable skip this
        if not self.lockAvailable:
            return

        if not self.screenLock:
            self.tag = GLib.timeout_add(500, timer.clock)
            self.overlay.show()
        else:
            GLib.source_remove(self.tag)
            self.overlay.hide()
        self.screenLock = not self.screenLock

    def printTime(self, time):
        # overlay printing
        print(time)
        self.clock.set_label(time)

    def hideSettings(self, *args):
        # todo: need refactor for close button
        timer.restart()
        self.settings.hide()

class Timer:
    def __init__(self, activityTimer, hardActivityTimer, timeout):
        self.activityTimer = activityTimer
        self.hardActivityTimer = hardActivityTimer
        self.timeout = timeout
        self.phase = 1
        self.isStopped = False

    def start(self):
        self.start = time.perf_counter()
        self.tag = GLib.timeout_add(500, self.tick)
        self.handler.notify('start timer')

    def tick(self):
        if (self.phase == 1 and (time.perf_counter() - self.start) / 60 > self.activityTimer):
            self.phase += 1
            self.start = time.perf_counter()
            self.handler.notify('Start working hard')
        if (self.phase == 2 and (time.perf_counter() - self.start) / 60 > self.hardActivityTimer):
            self.phase += 1
            self.start = time.perf_counter()
            self.handler.toggleScreen()
        if (self.phase == 3 and (time.perf_counter() - self.start) / 60 > self.timeout):
            self.phase = 1
            self.start = time.perf_counter()
            self.handler.toggleScreen()
        return True

    def clock(self):
        timeInSec = round(self.timeout * 60 - (time.perf_counter() - self.start))
        timeH = timeInSec // 3600
        timeM = (timeInSec % 3600) // 60
        timeS = timeInSec % 60
        timeString = ''
        
        if (timeH > 0):
            timeString = timeString + str(timeH).rjust(2, '0') + ':'
        
        if (timeM > 0):
            timeString = timeString + str(timeM).rjust(2, '0') + ':'
        
        if (timeS > 0):
            timeString = timeString + str(timeS).rjust(2, '0')
        
        self.handler.printTime(timeString)

        return True

    def stop(self):
        GLib.source_remove(self.tag)
        self.isStopped = True

    def restart(self):
        self.phase = 1
        self.isStopped = False
        self.start = time.perf_counter()
        self.tag = GLib.timeout_add(500, self.tick)
        self.handler.notify('start timer')


    def setHandler(self, handler):
        self.handler = handler;
        return False


# Handle pressing Ctr+C properly, ignored by default
signal.signal(signal.SIGINT, signal.SIG_DFL)

# timer set
timer = Timer(DEFAULT_ACTIVITY_TIMER, DEFAULT_HARD_ACTIVITY_TIMER, DEFAULT_TIMEOUT_TIMER)

# include glade markup
builder = Gtk.Builder()
builder.add_from_file('glade.glade')

# include markup style
provider = Gtk.CssProvider()
provider.load_from_path('glade.css')
Gtk.StyleContext().add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

# create settings
settings = builder.get_object('settings')
# create overlay
overlay = builder.get_object('overlay')
overlay.fullscreen()
# create event handler
handler = Handler(timer, overlay, settings)
builder.connect_signals(handler)

# add handler in timer
timer.setHandler(handler)

# create menu in toolbar
menu = builder.get_object('menu1')
icon = TrayIcon(APPID, ICON, menu)

# init notificator
Notify.init(APPID)

# start working timer
timer.start()

# main loop
Gtk.main()