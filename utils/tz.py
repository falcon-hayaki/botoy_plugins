from datetime import datetime, timezone, timedelta

SHA_TZ = timezone(
    timedelta(hours=8),
    name='Asia/Shanghai',
)

def beijingnow():
    return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(SHA_TZ)