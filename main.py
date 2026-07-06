"""
Temple Run - Endless Runner Game for Android
Built with Kivy, runs on Termux or packaged as APK.
"""
from kivy.config import Config

# Configure before importing Kivy modules
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'fullscreen', 'auto')
Config.set('kivy', 'log_level', 'warning')

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform

from src.gamewidget import GameWidget


class TempleRunApp(App):
    """Main Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Temple Run'
        self.icon = None

    def build(self):
        """Build the application UI."""
        Window.clearcolor = (0.06, 0.06, 0.10, 1.0)
        game = GameWidget()
        return game

    def on_pause(self):
        """Handle app pause (Android)."""
        return True

    def on_resume(self):
        """Handle app resume (Android)."""
        pass


if __name__ == '__main__':
    TempleRunApp().run()
