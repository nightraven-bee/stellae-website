# 2026-10-24 测试子路径更新

- 测试地址：<https://www.stellae.world/room/1023testing/>
- 上游 PR：<https://github.com/nightraven-bee/stellae-website/pull/1>，开放、非草稿，待上游合并。
- 网站内容提交：`9f9327b60803993ece8680a0fadc3a01d9b9aaa3`。后续文档和制作工具提交不改变 `www/`。
- 发布范围：提交中的 `www/`，93 个文件，59,622,155 字节；未上传私密原录屏、核查目录或制作交接包。
- 服务器目录：`/www/stellae/room/1023testing`；未修改或重载 Nginx。

## 本次已验证

1. 发布归档从 Git 提交导出，服务器验证全部93个文件的大小与 SHA-256 后替换测试目录。
2. 公网 HTTPS 下载全部93个文件，HTTP200，文件大小与 SHA-256 全部一致。
3. 主片 Range 返回 HTTP206，`Content-Range: bytes 0-1023/15690503`，`Content-Type: video/mp4`。
4. 无末尾斜线路径正常跳转，返回本次首页。
5. 正式官网、频道首页的公网哈希与部署前一致；服务器另外三处已有页面及两份 Nginx 配置的哈希也保持一致。
6. 线上浏览器打开新版首页与二维码弹窗，确认“参与方式与版本更新”文案及移除的补充说明；保留实际截图。此项为有限页面检查，未记作全站线上交互验收。

## 回退与发布记录

- 服务器记录：`/home/ai_test/releases/stellae-1023testing-9f9327b/`。
- 归档 SHA-256：`9cd74370baec19bcb18c9d80d67f15013915ff4557d8fc080c1a770105fe1b4d`。
- `previous-www/` 保留本次更新前完整测试目录。
- 回退命令：`python3 /home/ai_test/releases/stellae-1023testing-9f9327b/rollback.py`。先校验当前目录仍为本次版本，再将其移至 `withdrawn-www/` 并恢复旧测试目录；不会碰正式首页或频道首页。回退未执行。
- 本地完整 HTTP 报告与线上截图保存在制作目录 `官网更新-20261024/部署-1023testing/`；不提交包含本机隐私检查的目录。

媒体检查见 [内容更新说明](内容更新说明-20261024.md)。连续人工听检仍为 `NOT_PERFORMED`。上游合并与正式首页发布是单独状态。

---

## 历史记录（2026-10-23；以下状态仅对应当时）

# 2026-10-23 测试子路径部署

- 测试地址：<https://www.stellae.world/room/1023testing/>
- 审阅 PR：<https://github.com/nightraven-bee/stellae-website/pull/1>（草稿，未合并）
- 网站内容提交：`78f5900309a8665a0ec076b780938fe56f462efb`。后续部署说明提交只修改文档，`www/` 内容不变。
- 发布范围：提交中的 `www/`，89 个文件、50,425,725 字节。未上传原始录屏、隐私核查图或回退副本。
- 服务器目录：`/www/stellae/room/1023testing`。利用现有 `/room/` 静态路由，未修改或重载 Nginx。

## 已验证

1. 从 Git 提交生成归档，在本机及服务器上按 `docs/manifest.json` 校验全部 89 个文件的大小和 SHA-256。
2. 从公网 HTTPS 下载全部 89 个文件，HTTP 200，文件大小和 SHA-256 全部一致。
3. 产品视频 Range 请求返回 HTTP 206、`Content-Range: bytes 0-1023/15231497`，MIME 为 `video/mp4`。
4. 无末尾斜线的 `/room/1023testing` 自动跳转到相同 HTTPS 地址的末尾斜线路径，返回正确首页。
5. 正式官网与 `/room/` 首页公网 HTTP 200，内容哈希与部署前一致。服务器 `/bp/`、`/AlphaTesting/`、`/cocreate/` 首页及两份 Nginx 配置也与部署前一致。

本地播放器与视觉验收见[内容更新说明](内容更新说明-20261023.md)。线上浏览器检查工具绑定页面连续超时，本次线上结果以完整 HTTPS 文件校验和视频 Range 检查为依据，未将其记为线上交互验收通过。

## 发布记录与回退

- 服务器发布记录：`/home/ai_test/releases/stellae-1023testing-78f5900/`，保留归档、清单、来源记录、`release.json` 和公网校验报告。
- 归档 SHA-256：`2007e26f2d44100e48a301b315c27ece5a96cfc01f4a8a14640a4133e07b1375`。
- 回退脚本：上述发布目录的 `rollback.py`。脚本先确认当前测试目录仍与发布清单一致，再将该目录移动至发布记录目录的 `www-withdrawn`；不会覆盖正式首页或现有频道首页。尚未执行回退。

场景图库仍等待用户定义后重新截图；配乐 `listening_check: NOT_PERFORMED`，连续实际听感验收待完成。
