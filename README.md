# 论坛坞（ForumDock）儿童安全标准

[![Deploy to GitHub Pages](https://github.com/xuxiaowei-io/child-safety/actions/workflows/pages.yml/badge.svg)](https://github.com/xuxiaowei-io/child-safety/actions/workflows/pages.yml)

论坛坞（ForumDock）面向儿童性虐待和性剥削（CSAE / CSAM）的防范、举报与处置标准，中英双语，公开发布在 GitHub Pages：

**<https://xuxiaowei-io.github.io/child-safety/>**

这个网址就是 Google Play Console「儿童安全标准」表单里 **「安全标准」网址** 一栏要填的地址。页面内容与表单另外两栏是对应的：

| 表单字段 | 本页面对应内容 |
|--|--|
| 「安全标准」网址 | 整个页面（`site/index.html`） |
| 联系信息 | 第 09 节「儿童安全联系人」：`xuxiaowei@xuxiaowei.com.cn` |
| 条款：允许用户在应用内举报 | 第 06 节「举报渠道」 |
| 条款：遵守儿童安全法并上报 | 第 07、08 节（处置流程、与执法机构合作） |

## 目录结构

```text
.
├─ .github/
│  ├─ workflows/pages.yml    # CI：先校验，再发布 site/ 到 GitHub Pages
│  └─ dependabot.yml         # 每月检查 GitHub Actions 版本
├─ site/                     # 发布根目录，整个目录就是网站
│  ├─ index.html             # 标准正文（中文 / English 切换）
│  ├─ 404.html               # 找不到页面时显示
│  ├─ robots.txt
│  ├─ sitemap.xml
│  ├─ .nojekyll
│  └─ assets/
│     ├─ app-icon-96.png     # 页头、页脚用的小图标
│     ├─ icon-192.png        # 站点图标（由应用图标生成）
│     ├─ favicon-32.png
│     ├─ apple-touch-icon.png
│     └─ og.png              # 1200×630 社交预览图
├─ scripts/check_site.py     # 零依赖校验脚本（本地与 CI 共用）
├─ .editorconfig
├─ .gitignore
└─ README.md
```

页面是**单个自包含 HTML**：样式与脚本内联，不加载任何 CDN、字体或第三方脚本，因此在审核环境和网络受限的地区都能正常打开，也便于长期归档。

图标、favicon 与社交预览图都以应用图标 `app-icon-1024.png` 为基础生成（等比缩放、圆角），没有另画一套品牌标识；404 页的图标额外内联成 data URI，这样它出现在任意路径下都能正常显示。

## 本地预览

```bash
python3 -m http.server 8080 -d site
# http://localhost:8080/
```

## 校验

```bash
python3 scripts/check_site.py
```

脚本只用 Python 标准库，检查这些内容，任何一项不通过都会让 CI 失败、不发布：

- 必需的文件是否都在（`site/` 下的页面、图标、`robots.txt`、`sitemap.xml`、`.nojekyll`）；
- 页面里的本地链接与 `#锚点` 是否都能解析，`id` 是否齐全（中英各 11 节）；
- 是否引用了外部资源（页面必须自包含）；
- `canonical`、`og:url`、`og:image` 是否等于线上地址，`og:image` 是否为 1200×630；
- `sitemap.xml` 的 `<loc>` 与 `robots.txt` 的 Sitemap 是否与 canonical 一致；
- 联系人邮箱是否出现在正文、`mailto:` 链接是否还在；
- 是否残留 `TODO` 或 `example.com` 占位符。

## 发布

工作流在 `.github/workflows/pages.yml`：推到 `main` 或手动 `Run workflow` 都会触发，先跑校验，再上传 `site/` 并以 `actions/deploy-pages` 发布。

**首次发布前只需做一次设置：**

1. 打开仓库 **Settings → Pages**；
2. **Build and deployment → Source** 选 **GitHub Actions**（不要选 “Deploy from a branch”）。

之后每次推 `main`，一分钟左右即可在 <https://xuxiaowei-io.github.io/child-safety/> 看到更新。

> 不需要在仓库里放 `gh-pages` 分支，也不需要提交构建产物；发布目录就是 `site/`。

## 修改内容

绝大多数改动只碰 `site/index.html`：

- **版本号、生效日期**：页面顶部 `.meta`、`<title>` 之外的 `og:title` 不用动；同时改 `site/sitemap.xml` 的 `<lastmod>`；
- **联系邮箱**：第 06、09 节与页脚共 5 处 `mailto:`，搜索 `xuxiaowei@xuxiaowei.com.cn` 一次改全，表单里的联系信息也要一致；
- **正文**：中英两段都要改（`#doc-zh` 与 `#doc-en`），两边的章节编号一一对应；
- 改完跑一遍 `python3 scripts/check_site.py`。

## 换域名（可选）

如果要换成自定义域名（例如 `child-safety.xuxiaowei.com.cn`）：

1. 新建 `site/CNAME`，内容为域名（不要带 `https://`）；
2. DNS 加一条 CNAME 指向 `xuxiaowei-io.github.io`；
3. Settings → Pages → Custom domain 填同一个域名并开启 HTTPS；
4. 同步改这几处的线上地址，然后跑校验：
   - `site/index.html` 的 `canonical`、`og:url`、`og:image`、`twitter:image`；
   - `site/sitemap.xml` 的 `<loc>`、`site/robots.txt` 的 `Sitemap`；
   - `site/404.html` 里 `/child-safety/` 开头的链接；
   - `scripts/check_site.py` 顶部的 `BASE_PATH`、`ORIGIN`、`PAGE_URL`、`OG_IMAGE`。

## 维护约定

- 至少每年复核一次正文与生效日期；产品功能（例如新增发帖、私信举报入口）或商店政策变化时同步更新第 05、06 节。
- 页面上的承诺（1 个工作日内确认、24 小时内阻断）要能真正执行；做不到就改文案，不要留空头承诺。
- 本页是公开合规页面，改动以「准确、可核查」优先，不要写无法验证的措辞。

## 版权

© 徐晓伟 · 论坛坞（ForumDock）。页面文字为面向 Google Play 审核公开的合规声明。
