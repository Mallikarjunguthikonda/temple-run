[app]
title = Temple Run
package.name = templerun
package.domain = org.templerun
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt
version = 1.0.0
requirements = python3,kivy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.0
android.api = 31
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.enable_androidx = True
android.fullscreen = 1
android.presplash_color = #0A0A19
android.archs = arm64-v8a,armeabi-v7a
android.log_level = 2
android.entrypoint = main.py
android.window_background_color = 0A0A19
android.copy_apk = 1
android.immersive_mode = 1
android.dark_status_bar_icons = True

[buildozer]
log_level = 2
warn_on_root = 0
bin_dir = ./bin
android.build_timeout = 1800
