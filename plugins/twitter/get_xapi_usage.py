from botoy import ctx, S, jconfig
import logging
import json

from . import xm

logger = logging.getLogger(__name__)

async def get_xapi_usage():
    """
    查询 X API 使用情况
    
    当用户发送 /xapi 时，返回当前的 API 配额使用情况
    接口: GET /2/usage/tweets
    """
    if msg := ctx.g:
        # 检查是否是 /xapi 指令
        if msg.text and msg.text.strip().lower() == '/xapi':
            try:
                # 调用 API 获取用量
                resp = xm.get_usage()
                
                if resp.status_code != 200:
                    error_msg = f"❌ 查询失败 ({resp.status_code})"
                    try:
                        error_detail = resp.json()
                        if 'detail' in error_detail:
                            error_msg += f": {error_detail['detail']}"
                    except:
                        pass
                    await S.text(error_msg)
                    return

                data = resp.json().get('data', {})
                
                if not data:
                    await S.text("❌ 未获取到用量数据")
                    return
                
                # 解析数据
                project_cap = int(data.get('project_cap', 0))
                project_usage = int(data.get('project_usage', 0))
                cap_reset_day = data.get('cap_reset_day')
                
                usage_percent = (project_usage / project_cap * 100) if project_cap > 0 else 0
                
                lines = ["📊 X API 用量统计"]
                lines.append(f"总配额: {project_cap:,}")
                lines.append(f"已使用: {project_usage:,}")
                lines.append(f"使用率: {usage_percent:.1f}%")
                lines.append(f"重置日: 每月 {cap_reset_day} 号")
                
                #每日详细用量 (最近3天)
                daily_usage = data.get('daily_client_app_usage', [])
                if daily_usage:
                    lines.append("\n📅 最近每日用量:")
                    # 按日期排序
                    sorted_daily = sorted(daily_usage, key=lambda x: x['date'], reverse=True)
                    for day in sorted_daily[:3]:
                        usage = day.get('usage', '0')
                        date = day.get('date', '未知')
                        lines.append(f"  {date}: {usage} 次")
                
                await S.text("\n".join(lines))
                
            except Exception as e:
                logger.exception(f"Error getting X API usage: {e}")
                await S.text(f'❌ 发生错误: {str(e)}')
