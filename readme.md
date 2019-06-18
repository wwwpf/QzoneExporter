# QzoneExporter

QQ空间数据导出及显示。

- 导出日志、留言板、相册、说说等数据。
- 将说说、相册中的图片及视频下载至本地。
- 以网页形式显示本地数据，可在浏览时自动下载图片及视频。
- 支持 Exif 信息写回照片，时间写入文件名。（由[Yang-z](https://github.com/wwwpf/QzoneExporter/pull/8)及[greysign](https://github.com/wwwpf/QzoneExporter/pull/5)提供）

导出数据

```shell
usage: exporter.py [-h] [--blog] [--msgboard] [--photo] [--shuoshuo] [--like]
                   [--download] [--all]

optional arguments:
  -h, --help  show this help message and exit
  --blog      导出日志数据
  --msgboard  导出留言板数据
  --photo     导出相册数据
  --shuoshuo  导出说说数据
  --download  下载图片或视频至本地
  --all       导出所有数据
```

显示数据

```shell
usage: displayer.py [-h] [--download]

optional arguments:
  -h, --help  show this help message and exit
  --download  当本地不存在图片、视频时，尝试下载至本地
```

## 输入

- target_uin
  需要导出数据的QQ号。
- self_uin
  用于登录空间的QQ号。
- cookies_value
  从浏览器登录QQ空间，按 `F12`，点击 `Network` 选项卡，点击QQ空间“我的主页“，点击 `XHR`，点击 `main_page_cgi` 请求，从 `Header` 中找出 `cookie`，如图所示。
- g_tk
  可通过 cookies_value 中的 `p_skey` 计算，选填。
  ![获取g_tk及cookie](pic/1.png)

登录QQ需要有访问目标QQ空间的权限。

## 网页显示效果

### 预览

![预览](pic/html_preview.png)

### 日志

![blog](pic/html_blog0.png)

![blog](pic/html_blog1.png)

### 留言板

![msgboard](pic/html_msgboard.png)

### 相册

![photo](pic/html_photo0.png)

![photo](pic/html_photo1.png)

![photo](pic/html_photo2.png)

### 说说

![shuoshuo](pic/html_shuoshuo.png)

## 输出文件

```plain
target_uin/
    blog/
        日志分类/             // 譬如：个人日志
            日志正文.html
            日志评论.json
    msg_board/
        每20条留言分为1个json文件
    photo
        相册名_相册id/
            downloaded/       // 保存下载的数据
            照片数据
            评论数据
        相册信息.json
        downloaded.txt        // 已下载的url
        to_download.txt       // 待下载的url及文件名
    shuoshuo/
        downloaded/
        downloaded.txt
        to_download.txt
        shuoshuo_tid.txt      // 保存说说的tid
        每40条说说分为1个json文件
    main_page.json            // 日志、相册、说说的数量
    like_information.json     // 保存点赞数据
```

### 日志

![blog](pic/blog1.png)

![blog](pic/blog2.png)

### 留言板

![msgboard](pic/msgboard.png)

### 相册

![photo](pic/photo1.png)

![photo](pic/photo2.png)

### 说说

![shuoshuo](pic/shuoshuo.png)

## 说明

- 数据以json格式保存，可通过网页显示主要数据。
- 导出的数据是登录账号可见的数据，“仅主人可见”等数据无法获取。
- 导出的视频链接有时效性，超时无法访问。
- 如果相册图片数量较多并且未下载至本地时，网页显示会比较慢。

## 依赖

- requests
- bs4
- python3
- piexif（Exif 信息写回）
- Flask（网页显示）

## 使用

```python
# exporter.py
# 根据需要设定以下变量
target_uin = "需要导出数据的QQ号"
self_uin = "登录空间的QQ号"
cookies_value = "从浏览器获取"
g_tk = "从浏览器获取"   # 可选，会尝试通过 cookies 计算
q = QzoneExporter(self_uin, g_tk, cookies_value, args, target_uin)
q.export()
```

### 示例

#### 导出日志数据

命令行中运行

```shell
python exporter.py --blog
```

#### 下载相册照片

```shell
python exporter.py --photo
python exporter.py --download
```

或

```shell
python exporter.py --photo --download
```

#### 网页显示

```shell
python displayer.py [--download]
```

#### Exif 信息写回照片

具体使用参考 `photo_exif_recover.py` 内的说明。

## 存在的问题

- 某些图片通过sharpP格式传输，无法打开。
- 进度的保存。
- 由于数据未抓取到本地、不想写等原因，网页显示时忽略了一些无关紧要的数据。
- 未能完全测试所有情况，因此网页显示时可能会出现某些错误。

## 更新记录

- 2019.05.10 支持网页显示；使用多线程下载，去掉超时设置；去掉点赞数据的抓取；修复了文件名可能非法的问题。

## 参考

- [QQ 空间爬虫之爬取说说](https://kylingit.com/blog/qq-空间爬虫之爬取说说/)
  感谢这篇博客提供的思路。
- [QQ空间](https://qzone.qq.com/) 网页显示本地数据时使用的样式与布局均来自于QQ空间。

## LICENSE

GPL-3.0，额外条件：禁止商用。

## 捐赠

如果您认为该项目在一定程度上帮助了您，可以赞赏我:D

![赞赏码](https://raw.githubusercontent.com/wwwpf/ttt/master/qr.png)
