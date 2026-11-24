import sys

from .constants import APP_DISPLAY_NAME, APP_ID
from .environment import install_kwin_rule_if_needed
from .gtk import Gio, GLib, Gtk
from .window import BUG_REPORT_URL, VirtualKeyboard


USAGE = f"""Usage: vboard [OPTION]

Options:
  --toggle    Toggle the vboard window show/hide status
  --help      Show this help message

Report bugs: {BUG_REPORT_URL}
"""


class VboardApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        GLib.set_prgname(APP_ID)
        GLib.set_application_name(APP_DISPLAY_NAME)

    def ensure_window(self):
        created = self.window is None
        if created:
            install_kwin_rule_if_needed()
            self.window = VirtualKeyboard(application=self)
            self.window.connect("destroy", self.on_window_destroy)
            self.window.connect("configure-event", self.window.on_resize)
            if self.window.config_pos_x > 0 or self.window.config_pos_y > 0:
                self.window.move(self.window.config_pos_x, self.window.config_pos_y)
            self.window.show_all()
            self.window.change_visibility()
            if self.window.start_minimized and self.window.tray_icon is not None:
                self.window.hide()
            self.window.update_tray_menu()
        return self.window, created

    def do_activate(self):
        window, created = self.ensure_window()
        if created and window.start_minimized and window.tray_icon is not None:
            return
        window.show()
        window.present()
        window.request_keep_above()
        window.update_tray_menu()

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        if args in (["--help"], ["-h"]):
            command_line.print_literal(USAGE)
            return 0

        if args == ["--toggle"]:
            if self.window is None:
                window, _created = self.ensure_window()
                window.show()
                window.present()
                window.request_keep_above()
                window.update_tray_menu()
            else:
                self.window.toggle_visibility()
            return 0

        if not args:
            self.activate()
            return 0

        command_line.printerr_literal(USAGE)
        return 1

    def on_window_destroy(self, window):
        window.cleanup_on_destroy()
        self.window = None
        self.quit()


def main(argv=None):
    args = list(sys.argv if argv is None else argv)
    if args[1:] in (["--help"], ["-h"]):
        sys.stdout.write(USAGE)
        return 0
    app = VboardApplication()
    return app.run(args)
