[app]
title = FolyanApp
package.name = folyan.app
package.domain = folyan.app

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1

requirements = python3,kivy,kivymd,pillow

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 0
warn_on_root = 0
android.api = 34
android.minapi = 21
android.ndk = 25b
