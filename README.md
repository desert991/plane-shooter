# 飞机大战 - Airplane Shooter

一个用 Python 和 Tkinter 编写的纵版射击游戏，运行在 macOS 本地。

A vertical scrolling shooter game built with Python and Tkinter, running natively on macOS.

## 游戏说明 / How to Play

| 按键 / Key | 功能 / Action |
|-----------|-------------|
| ← → ↑ ↓   | 移动飞机 / Move |
| W A S D   | 移动飞机 / Move |
| Space     | 发射子弹 / Fire |
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
| 轻敌 | 红色三角形 | 100 | 直线下落 |
| 侦察机 | 橙色菱形 | 150 | 蛇形移动 |
| 重装兵 | 紫色六边形 | 250 | 2 条命 |
| Boss | 红色大圆 | 1000 | 高血量，会反击 |

## 道具类型 / Power-up Types

| 图标 | 效果 |
|------|------|
| P (橙色) | 武器升级 / Weapon upgrade |
| S (蓝色) | 护盾 / Shield |
| L (绿色) | 额外一条命 / Extra life |

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

🎮 GitHub 仓库: [desert991/plane-shooter](https://github.com/desert991/plane-shooter)
