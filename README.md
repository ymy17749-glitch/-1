# 触屏扫雷 · Kivy 版 —— 用 GitHub Actions 免费打包 APK

本工程可以直接用 **GitHub Actions** 在云端免费编译成安卓 APK，
全程**只用手机浏览器**就能完成，不需要电脑、不需要装 Android SDK。

---

## 📁 工程结构

```
kivy_minesweeper/
├── main.py                          # 游戏主程序（Kivy）
├── buildozer.spec                   # 打包配置
├── .gitignore                       # 忽略生成物
├── .github/
│   └── workflows/
│       └── build-apk.yml            # GitHub Actions 自动编译脚本
└── README.md                        # 本文件
```

---

## 🚀 操作步骤（手机端可完成）

### 第 1 步：注册 GitHub 账号
手机浏览器打开 https://github.com ，注册并登录（已有账号跳过）。

### 第 2 步：新建仓库
1. 点右上角 `+` → **New repository**
2. Repository name 填 `minesweeper`
3. 选 **Public**（私有仓库的 Actions 有额度限制，公开最省事）
4. 点 **Create repository**

### 第 3 步：上传本项目文件
在新建的仓库页面点 **uploading an existing file**，
把 `kivy_minesweeper` 文件夹里的这些**全部**上传：

- `main.py`
- `buildozer.spec`
- `.github/workflows/build-apk.yml`

> ⚠️ **注意**：上传时**必须保留目录结构**！
> 尤其是 `.github/workflows/build-apk.yml` 这个路径不能改，
> 否则 GitHub 找不到编译脚本。
> 建议用 GitHub 网页的「拖拽整个文件夹」方式上传，或使用 GitHub 官方 App。

### 第 4 步：等它自动编译
上传/提交后，Actions 会**自动开始编译**：
1. 点仓库顶部的 **Actions** 标签
2. 能看到一个叫 **Build Android APK** 的任务在跑
3. 首次编译约 **10 ~ 30 分钟**（要下载 SDK/NDK），耐心等
4. 变成 ✅ 绿色勾就是成功了

> 如果没自动触发：进 Actions → 左侧选 `Build Android APK`
> → 右侧 **Run workflow** 按钮手动触发。

### 第 5 步：下载 APK
1. 点进那次成功的运行记录
2. 页面底部 **Artifacts** 区域，下载 **minesweeper-apk**
3. 得到的是一个 `.zip`，解压后就是 **`.apk`** 文件
4. 传到手机安装（需允许「安装未知来源应用」）

---

## ✅ 编译配置说明

`buildozer.spec` 中的关键设置：

| 配置项 | 值 | 含义 |
|---|---|---|
| `android.minapi` | `21` | 最低支持 Android 5.0 |
| `android.archs` | `arm64-v8a, armeabi-v7a` | 同时出 64 位 + 32 位 |
| `android.accept_sdk_license` | `True` | 自动接受 SDK 许可 |
| `orientation` | `portrait` | 竖屏 |

---

## ⚠️ 常见问题

**Q：Actions 报错 `BUILD FAILED` 怎么办？**
点进报错的那一步，展开日志，把最后 20~30 行发给 AI 助手看。

**Q：APK 装到老安卓（4.x）上能跑吗？**
不能。Kivy 2.x + 现代 NDK 最低只支持 **Android 5.0 (API 21)**。

**Q：想改游戏难度/雷数？**
改 `main.py` 里的 `self.difficulties` 字典，提交后 Actions 会自动重新编译。

**Q：想改成正式版（release）签名 APK？**
把 workflow 里的 `buildozer android debug` 改成 `buildozer android release`，
并额外配置签名密钥（较复杂，需要时再研究）。

---

## 🎮 游戏玩法

- **轻点**格子 → 翻开
- **长按**格子 0.4 秒 → 插旗 / 取消插旗
- **按住拖动** → 滑动浏览大棋盘

难度：
- 简单 7×7（10 雷）
- 中级 10×10（15 雷）
- 高级 15×15（30 雷）
