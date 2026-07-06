"""
Temple Run - Endless Runner Game for Android
Built with Kivy, runs on Termux or packaged as APK.
"""
from kivy.config import Config

# Configure before importing Kivy modules
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'fullscreen', 'auto')
Config.set('input', 'touch', 'mouse')
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
        # Set window size for desktop testing
        if platform == 'android':
            # Full screen on Android
            from kivy.core.window import Window
            Window.fullscreen = 'auto'
        else:
            # Desktop: reasonable size for testing
            Window.size = (400, 720)
            Window.top = 50

        Window.clearcolor = (0.06, 0.06, 0.10, 1.0)

        # Create and return the game widget
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
