# 星黎宇宙官网

星黎宇宙 Stellae.AI 官方展示网站，同一套网页自适应 PC 与手机。

本仓库以 2026-10-21 的部署版本为基线，当前 2026-10-24 更新包含：84 秒产品片、四组 3D 装扮与场景、两张 2D 场景、功能实录、频道二维码内测入口与备案信息。除用户指定的版本按钮、内测弹窗、备案页脚、头像和图库外框外，保留原 UI 和全部动效。

[测试子路径](https://www.stellae.world/room/1023testing/) 已更新至网站内容提交 `9f9327b`，93 个文件经服务器与公网 HTTPS 全量哈希核验。[上游 PR #1](https://github.com/nightraven-bee/stellae-website/pull/1) 已提交，待上游合并。详见 [本轮内容与核查说明](docs/内容更新说明-20261024.md)。

## 目录

- `www/`：完整静态网站，部署时将此目录设为 Web 根目录。
- `docs/DEPLOYMENT.zh-CN.txt`：详细部署、配置与验收说明。
- `docs/manifest.json`：网站文件大小与 SHA-256 校验清单。
- `docs/测试部署-1023testing.md`：测试链接、发布版本、校验与回退记录。

## 部署

使用 Nginx、IIS、静态托管或 CDN 提供 `www/` 的内容，默认首页为 `index.html`。

这是无需构建的 HTML/CSS/JavaScript 网站，不需要 npm 安装、Node 服务或数据库。保持 `assets/` 的完整目录层级和文件名大小写，并使用正确的 JavaScript MIME；视频服务需要支持字节范围请求。

网站使用 `#home` 等 hash 导航，刷新会从首页开始。详细服务器设置见部署说明。

## 上线配置

编辑 `www/site-config.js`：

- 内测入口使用 `www/assets/channel-qrcode.jpg`，由用户提供；参与说明与二维码同步维护。
- 核实后填写 `legal.privacy`、`legal.terms`。
- 确认公司、备案信息和 `roomUrl`。页脚两项备案号码及公安查询链接在 `index.html` 中也有可见内容。

星黎频道地址为 `https://www.stellae.world/room/`。部署官网首页时保留线上已有的 `/room/` 应用与服务路由；本仓库不包含星黎频道应用或手机安装包。目前不提供 iOS / Android 版本下载按钮，参与内测统一扫码加入频道。

## 本地审阅与媒体重建

运行 `python3 tools/preview_server.py` 后打开 `http://127.0.0.1:8853/`。预览服务仅绑定本机，支持视频 Range 请求，并禁用缓存以避免看到旧视频或旧配置。

`tools/build_media_v4.py` 使用已脱敏重采素材与改前快照生成 84 秒主片、五个功能短片和封面；`tools/promo_style.py` 复用原产品片美术。需要本机 FFmpeg、Pillow、OpenCV、原字体及脚本标注的本地素材路径。修改配方后先清理相应分段缓存，再使用 `--reuse`。

图库包含四组 3D 装扮场景与两张新补拍的 2D 场景，外侧圆角透明。主片初见段明确展示 2D、3D、微信风格三种显示方式，日常段也保留微信风格聊天。视频只保留精简的产品主文案，拍摄与脱敏等注释留在制作记录；头像使用用户指定的眼镜校服版本。运行 `python3 tools/verify_media_v4.py` 可核查媒体、四角、界面代码保留范围和资源引用，并生成校验清单。

## 维护

直接修改 `www/` 内的源文件。发布更新时同步所有被修改的文件，并刷新同名资源的 CDN 缓存；HTML、JavaScript、CSS 与配置文件建议重新验证缓存。

`docs/manifest.json` 对应本次交付快照，修改资源后需要重新生成对应校验值。

## 第三方许可

随资源保留以下许可文件：

- `www/HOLO-REFERENCE-LICENSE.txt`
- `www/assets/vendor/rhine-boot-LICENSE.txt`
- `www/assets/vendor/three/LICENSE.txt`
