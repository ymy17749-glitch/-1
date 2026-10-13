[app]

# (str) 应用名称（会显示在手机桌面）
title = 触屏扫雷

# (str) 包名，必须唯一
package.name = minesweeper

# (str) 域名（与包名组成完整包 ID: org.test.minesweeper）
package.domain = org.test

# (str) 程序入口文件（main.py 所在处）
source.dir = .

# (list) 需要一起打包进 APK 的文件/目录（用逗号分隔）
source.include_exts = py,png,jpg,kv,atlas

# (list) 要排除的目录
source.exclude_dirs = bin, .buildozer, __pycache__

# (str) 应用版本
version = 0.1

# (list) 需要的 Python 依赖（kivy 已内置）
requirements = python3,kivy

# (str) 使用的 Python 版本
# (list) 需要使用的预设配置，如 android 的权限
android.permissions = VIBRATE

# 目标/最低支持的 Android API 等级（21 = Android 5.0）
android.minapi = 21

# 需要打包的 CPU 架构（32 位 + 64 位，兼容绝大多数手机）
android.archs = arm64-v8a, armeabi-v7a

# 自动接受 Android SDK 许可（云端编译必备，否则会卡在交互确认）
android.accept_sdk_license = True

# (str) 应用的显示方向：portrait 竖屏 / landscape 横屏 / all 跟随系统
orientation = portrait

# (bool) 是否全屏（隐藏状态栏）
fullscreen = 0

# (str) 应用图标（可选，把 icon.png 放到目录里即可）
# icon.filename = %(source.dir)s/icon.png

# (str) 启动图片（可选，有图片时再取消注释）
# presplash.filename = %(source.dir)s/presplash.png

# (list) 需要拷贝到私有目录的资源
android.add_src =

# --------------------------------------------------------------------

[buildozer]

# (int) 日志级别（2 = 显示更多信息）
log_level = 2

# (str) APK 生成后存放的目录
bin_dir = ./bin

# (bool) 在 Android 上是否使用 SDK 的默认库
warn_on_root = 1
