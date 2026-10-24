[app]
title = FolyanApp
package.name = folyanapp
package.domain = org.folyan

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf, pyx
source.exclude_patterns = core.pyx

version = 0.2.1

requirements = python3, kivy, https://github.com/kivymd/KivyMD/archive/master.zip, materialyoucolor==3.0.3, materialshapes, pycairo, pillow, exceptiongroup, asyncgui, asynckivy, cython==3.2.6

orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 24
android.ndk = 25b

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 0
warn_on_root = 0
