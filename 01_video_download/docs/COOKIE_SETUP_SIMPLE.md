# 🍪 Cookie配置 - 超简单方法

## ❌ 为什么脚本粘贴没反应？

原因：Cookie字符串太长（500-2000字符），终端输入有限制或特殊字符导致卡住。

---

## ✅ 解决方案：手动创建Cookie文件（3步搞定）

### 第1步：从浏览器获取Cookie

在抖音网页的开发者工具 Console 里运行：
```javascript
copy(document.cookie)
```
Cookie已复制到剪贴板！

---

### 第2步：创建Cookie文件

打开终端，运行以下**任意一种**方法：

#### 方法A：使用echo命令（推荐）

```bash
cd /Users/havpan/CC_Demo/finance/test_single_video

# 用引号包住你的Cookie，一次性粘贴
echo 'ttwid=1%7C你的完整Cookie内容...' > douyin_cookie.txt
```

⚠️ **注意**：
- 必须用**单引号** `'`，不是双引号
- Cookie中不能包含单引号，如果有，用方法B

#### 方法B：使用文本编辑器（最可靠）

```bash
cd /Users/havpan/CC_Demo/finance/test_single_video

# 使用nano编辑器
nano douyin_cookie.txt
```

然后：
1. 直接 **Cmd+V** 粘贴Cookie
2. 按 **Ctrl+O** 保存
3. 按 **Enter** 确认文件名
4. 按 **Ctrl+X** 退出

#### 方法C：使用VS Code或其他编辑器

```bash
# 在当前目录创建文件
code douyin_cookie.txt

# 或者用系统默认编辑器
open -e douyin_cookie.txt
```

粘贴Cookie → 保存 → 关闭

---

### 第3步：验证Cookie文件

```bash
# 检查文件是否存在
ls -lh douyin_cookie.txt

# 查看Cookie长度（应该有500+字符）
wc -c douyin_cookie.txt

# 查看前100个字符（确认内容正确）
head -c 100 douyin_cookie.txt
```

你应该看到：
```
-rw-r--r--  1 havpan  staff   1.2K  Apr 17 15:10 douyin_cookie.txt
     1234 douyin_cookie.txt
ttwid=1%7C...; passport_csrf_token=...; odin_tt=...
```

---

## 🧪 测试Cookie是否有效

运行测试脚本：

```bash
python3 test_cookie_download.py
```

我帮你创建一个专门的测试脚本！

---

## 📋 完整操作流程

```bash
# 1. 进入目录
cd /Users/havpan/CC_Demo/finance/test_single_video

# 2. 创建Cookie文件（选择下面任一方法）

# 方法1：使用nano
nano douyin_cookie.txt
# 粘贴Cookie → Ctrl+O → Enter → Ctrl+X

# 方法2：使用echo
echo '你的Cookie' > douyin_cookie.txt

# 3. 验证文件
cat douyin_cookie.txt

# 4. 测试下载
python3 test_cookie_download.py
```

---

## ⚠️ 常见问题

### Q1: echo命令报错 "unexpected EOF"

**原因**：Cookie中有特殊字符

**解决**：使用nano编辑器方法（方法B）

### Q2: Cookie粘贴后有换行

**解决**：
```bash
# 删除换行符
tr -d '\n' < douyin_cookie.txt > douyin_cookie_clean.txt
mv douyin_cookie_clean.txt douyin_cookie.txt
```

### Q3: 不确定Cookie是否完整

**检查**：Cookie应该包含这些关键字段：
- `ttwid=`
- `passport_csrf_token=`
- `odin_tt=`
- `sessionid=` 或 `sid_guard=`

运行：
```bash
grep -o 'ttwid=' douyin_cookie.txt && echo "✅ ttwid存在"
grep -o 'sessionid=' douyin_cookie.txt && echo "✅ sessionid存在"
```

---

## 🎯 推荐方法

**最简单可靠**：使用nano编辑器

```bash
cd /Users/havpan/CC_Demo/finance/test_single_video
nano douyin_cookie.txt
# Cmd+V粘贴 → Ctrl+O保存 → Ctrl+X退出
cat douyin_cookie.txt  # 确认内容
```

搞定！🎉
