# 作品评论与粉丝关注模块重构设计

## 背景

Comments.vue 和 Followers.vue 两个模块存在以下问题：
1. 样式与系统其他页面不一致（使用硬编码渐变背景而非 CSS 变量）
2. 功能可能存在 bug 需要修复

## 设计方案：完全重构

按照 Works.vue 和 Users.vue 的模式完全重写两个页面。

## 重构目标

### 样式统一
- 使用 CSS 变量系统：`var(--bg-card)`, `var(--text-primary)`, `var(--border-color)` 等
- 移除硬编码的渐变背景
- 统一卡片、按钮、表格样式

### 功能完善
- 修复评论加载、采集、回复显示
- 修复粉丝/关注列表加载和采集

## 页面设计

### 1. Comments.vue（作品评论）

**页面结构：**
```
├── 页面头部
│   ├── 标题：作品评论
│   ├── 描述：查看和管理作品评论数据
│   └── 操作按钮：导出 Excel
├── 作品选择器
│   └── 下拉选择作品（带封面预览）
├── 统计卡片
│   ├── 评论总数
│   ├── 今日采集
│   └── 总点赞数
├── 评论列表（选择作品后显示）
│   ├── 操作栏：采集评论、刷新
│   ├── 评论卡片列表
│   │   ├── 用户头像
│   │   ├── 用户昵称
│   │   ├── 评论内容
│   │   ├── 点赞数
│   │   ├── 回复数
│   │   └── 查看回复按钮
│   └── 分页
└── 回复抽屉
    └── 显示评论的所有回复
```

### 2. Followers.vue（粉丝与关注）

**页面结构：**
```
├── 页面头部
│   ├── 标题：粉丝与关注
│   ├── 描述：查看和管理用户的粉丝与关注列表
│   └── 操作按钮：导出 Excel
├── 用户选择器
│   └── 下拉选择用户
├── 统计卡片
│   ├── 粉丝数
│   ├── 关注数
│   └── 互关数
├── Tab 切换
│   ├── 粉丝列表
│   └── 关注列表
├── 用户表格
│   ├── 头像
│   ├── 昵称
│   ├── 简介
│   ├── 粉丝数
│   ├── 关注数
│   ├── 作品数
│   └── 操作
└── 分页
```

## 后端 API 确认

### 评论相关
- `GET /works/{work_id}/comments` - 获取评论列表
- `GET /works/{work_id}/comments/{comment_id}/replies` - 获取评论回复
- `POST /works/{work_id}/collect-comments` - 采集评论

### 粉丝/关注相关
- `GET /users/{sec_uid}/followers` - 获取粉丝列表
- `GET /users/{sec_uid}/followings` - 获取关注列表
- `POST /users/{sec_uid}/collect-followers` - 采集粉丝
- `POST /users/{sec_uid}/collect-followings` - 采集关注

## 技术规范

### CSS 变量使用
```css
/* 背景 */
--bg-primary: #0a0a0f;
--bg-secondary: #12121a;
--bg-tertiary: #1a1a24;
--bg-card: rgba(26, 26, 36, 0.8);

/* 文字 */
--text-primary: #ffffff;
--text-secondary: #a0a0b0;
--text-muted: #6b6b7b;

/* 强调色 */
--accent-primary: #fe2c55;
--accent-secondary: #25f4ee;

/* 边框 */
--border-color: rgba(255, 255, 255, 0.08);

/* 圆角 */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
```

### 组件规范
- 使用 Element Plus 组件库
- 保持与 Works.vue、Users.vue 一致的结构
- 响应式布局支持移动端

## 实施计划

1. 重构 Comments.vue
2. 重构 Followers.vue
3. 测试验证功能
