控制脚本说明

- `daemon.sh start|stop|restart|status`：以守护进程方式启动/停止/重启 bot，日志写入 `logs/botoy.log`，当日志超过 500KB 时自动轮转，保留 5 份备份（`botoy.log.1`...`botoy.log.5`）。
- `view_log.sh [--follow] [lines]`：查看日志，默认显示最近 200 行；加 `--follow` 或 `-f` 可实时跟踪。

使用示例：
```bash
# 启动
./scripts/daemon.sh start

# 查看最新 300 行，并跟随
./scripts/view_log.sh -f 300

# 停止
./scripts/daemon.sh stop
```

注意：脚本使用 `nohup` 启动进程并写 PID 于 `run/botoy.pid`。建议改用 `systemd` 做为长期运行方案。
