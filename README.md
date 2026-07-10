# 飞机大战 - Airplane Shooter

一个用 Python 和 Tkinter 编写的纵版射击游戏，运行在 macOS 本地。

A vertical scrolling shooter game built with Python and Tkinter, running natively on macOS.

## 游戏说明 / How to Play

| 按键 / Key | 功能 / Action |
|-----------|-------------|
| ← → ↑ ↓   | 移动飞机 / Move |
| W A S D   | 移动飞机 / Move |
| Space     | 额外火力 / Extra Fire |
| -         | 自动射击 / Auto-fire |
| P         | 暂停 / Pause |
| R         | 暂停时继续 / Resume |

- 消灭敌人获取分数 / Shoot enemies to score points
- 拾取道具升级武器 / Collect power-ups to upgrade your weapon
- 共有 3 条命，好好珍惜 / You have 3 lives
- 最高分会被自动保存 / High score is saved automatically

## 运行方式 / How to Run

```bash
python3 game.py
```

## 敌人类型 / Enemy Types

| 类型 | 外观 | 分值 | 特点 |
|------|------|------|------|
| 轻敌 | 红色战斗机 | 100 | 直线下落 |
| 侦察机 | 橙色高速机 | 150 | 蛇形移动 |
| 重装兵 | 紫色轰炸机 | 250 | 2 条命 |
| Boss | 红色巨型星舰 | 1000 | 高血量，会反击 |

## 道具类型 / Power-up Types

| 图标 | 效果 |
|------|------|
| P (橙色星) | 武器升级 / Weapon upgrade |
| S (蓝色星) | 护盾 / Shield |
| L (绿色星) | 额外一条命 / Extra life |

## 最高分 / High Score

最高分会自动保存在 `highscore.dat` 文件中，下次启动自动加载。

## 目标 / Goals

这个项目用于学习 GitHub 的版本控制功能：
1. 初始化 Git 仓库
2. 分步提交实现代码
3. 创建分支做实验
4. 推送到 GitHub 远程仓库
5. 管理 Pull Request 和 Issue

This project is designed to practice GitHub workflows:
1. Initialize a Git repository
2. Commit code incrementally
3. Create branches for experimentation
4. Push to GitHub remote
5. Manage Pull Requests and Issues

## 音效与音乐 / Sound & Music

- 射击、爆炸、拾取道具、受击均有音效
- 背景音乐在游戏开始时自动播放
- 使用 macOS 系统 `afplay` 命令播放
- 音效文件存放在 `sounds/` 目录下

## 更新日志 / Changelog

- 修复 BUG: 暂停恢复时清空按键状态
- 修复 BUG: 8位色值不支持问题
- 调整: 子弹速度提高 (8 -> 14)
- 调整: 玩家移动速度提高 (5 -> 8)
- 调整: 自动射击 (无需按 Space)
- 新增: 敌机采用飞机形状绘制
- 新增: 道具改为旋转星星 + 发光效果
- 新增: 音效和背景音乐

🎮 GitHub 仓库: [desert991/plane-shooter](https://github.com/desert991/plane-shooter)
