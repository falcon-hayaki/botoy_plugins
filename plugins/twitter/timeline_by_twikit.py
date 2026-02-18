import asyncio
import copy
import traceback
from os.path import join
from croniter import croniter
from datetime import datetime, timedelta
from dateutil import parser
from botoy import ctx, action, jconfig
import logging

from utils.twikit_manager import TwikitManager
from utils.tz import beijingnow, SHA_TZ
from utils import fileio

# Initialize TwikitManager
tm = TwikitManager()

logger = logging.getLogger(__name__)

resource_path = 'resources/twitter_tl_twikit'

lock = asyncio.Lock()
crontab = croniter('*/2 * * * *', beijingnow())
crontab_next = crontab.get_next(datetime)

# Configurable interval between same API calls
# This satisfies the requirement "同名接口之间间隔30秒请求，并且这个间隔可配置"
API_INTERVAL = jconfig.get('twitter.twikit_interval', 30) 

async def timeline_by_twikit():
    global lock, crontab, crontab_next, resource_path
    if msg := ctx.g and not lock.locked():
        async with lock:
            if beijingnow() >= crontab_next:
                try:
                    subscribes = await fileio.read_json(join(resource_path, 'subscribes.json'))
                    if not subscribes:
                        return

                    data = await fileio.read_json(join(resource_path, 'data.json'))

                    for screen_name in subscribes:
                        try:
                            # ---------------- GET USER INFO ----------------
                            # Configurable delay before interface call (per user iteration)
                            # Or after. Let's do it after to ensure spacing between users.
                            # But first call shouldn't wait if it's the start of the batch?
                            # The requirement is "interval between same name interfaces".
                            # So between User A's get_user_info and User B's get_user_info.
                            # We can just sleep at end of loop.
                            
                            user_info = await tm.get_user_info(screen_name)
                            if not user_info:
                                logger.error(f"get_user_info failed for {screen_name}")
                                continue

                            # Initialize user data if new
                            if screen_name not in data:
                                data[screen_name] = copy.deepcopy(user_info)
                                # Fetch initial timeline
                                # ENFORCE INTERVAL for timeline call relative to previous timeline call?
                                # Actually, get_user_info and get_user_timeline are different interfaces.
                                # But we should respect the "30s interval" rule generally.
                                # Let's assume the safe approach is to space out EVERYTHING.
                                await asyncio.sleep(API_INTERVAL)
                                
                                timeline = await tm.get_user_timeline(user_info['id'])
                                if not timeline: # Empty or failed
                                    timeline = {}
                                
                                data[screen_name]['timeline'] = timeline
                                await fileio.write_json(join(resource_path, "data.json"), data)
                            
                            else:
                                # Update user info check
                                old_info = data[screen_name]
                                has_update = False
                                for k, v in user_info.items():
                                    if k == 'following_count': continue
                                    if v != old_info.get(k):
                                        groups = subscribes[screen_name].get('groups', [])
                                        for group in groups:
                                            if k == 'icon':
                                                t = f"{user_info['name']}更新了{k}\n"
                                                await action.sendGroupPic(group=group, text=t, url=v)
                                            elif k == 'followers_count':
                                                if int(v/1000) > int(old_info.get(k, 0)/1000):
                                                    t = f"{user_info['name']}粉丝数到达{v}"
                                                    await action.sendGroupText(group=group, text=t)
                                            else:
                                                t = f"{user_info['name']}更新了{k}\n从\n{old_info.get(k)}\n更改为\n{v}"
                                                await action.sendGroupText(group=group, text=t)
                                        data[screen_name][k] = v
                                        has_update = True
                                
                                if has_update:
                                    await fileio.write_json(join(resource_path, "data.json"), data)

                                # ---------------- GET TIMELINE ----------------
                                # Wait before calling timeline to be safe
                                await asyncio.sleep(API_INTERVAL)

                                timeline = await tm.get_user_timeline(user_info['id'])
                                if timeline:
                                    # Compare for new tweets
                                    old_timeline = data[screen_name].get('timeline', {})
                                    new_ids = [tid for tid in timeline if tid not in old_timeline]
                                    
                                    # Inverse check: deleted tweets
                                    # (Optional, as per original logic)
                                    deleted_ids = [tid for tid in old_timeline if tid not in timeline]
                                    if deleted_ids:
                                        for tid in deleted_ids:
                                            del data[screen_name]['timeline'][tid]
                                        await fileio.write_json(join(resource_path, "data.json"), data)

                                    if new_ids:
                                        for tid in new_ids:
                                            tdata = timeline[tid]
                                            # Process new tweet
                                            await process_new_tweet(screen_name, user_info, tdata, subscribes[screen_name].get('groups', []))
                                            data[screen_name]['timeline'][tid] = tdata
                                        
                                        await fileio.write_json(join(resource_path, "data.json"), data)

                        except Exception as e:
                            logger.exception(f"Error processing {screen_name}")
                        
                        # Wait before next user to enforce interval between same interfaces (get_user_info next loop)
                        await asyncio.sleep(API_INTERVAL)

                    # Cleanup unsubscribed
                    data = await fileio.read_json(join(resource_path, "data.json"))
                    to_remove = [k for k in data if k not in subscribes]
                    if to_remove:
                        for k in to_remove:
                            del data[k]
                        await fileio.write_json(join(resource_path, "data.json"), data)

                except Exception as e:
                    logger.exception("timeline_by_twikit global error")

                crontab_next = crontab.get_next(datetime)


async def process_new_tweet(screen_name, user_info, tdata, groups):
    try:
        url = f'https://twitter.com/{screen_name}/status/{tdata["id"]}'
        tweet_type = tdata.get('tweet_type', 'default')
        
        # Parse created_at safely
        # Twikit might return different format, usually Fri Feb 13 ...
        # parser.parse handles most formats
        try:
            created_at = parser.parse(tdata['created_at']).astimezone(SHA_TZ)
        except:
            created_at = datetime.now(SHA_TZ) # Fallback

        # Check for 10 min expiry
        now = datetime.now(SHA_TZ)
        if now - created_at > timedelta(minutes=10):
            return

        imgs = None
        t = ""
        
        if tweet_type == 'default':
            t = f"{user_info['name']}的新推\n发布于{created_at}\n\n{tdata['text']}\n\n{url}"
            imgs = tdata.get('imgs')
        elif tweet_type == 'retweet':
            retweet_data = tdata.get('retweet_data', {})
            r_user = retweet_data.get('user_info', {})
            r_data = retweet_data.get('data', {})
            try:
                origin_created_at = parser.parse(r_data.get('created_at', str(now))).astimezone(SHA_TZ)
            except:
                origin_created_at = now
            t = f"{user_info['name']}转推了\n转发自:\n{r_user.get('name')}发布于{origin_created_at}\n\n{r_data.get('text')}\n\n{url}"
            imgs = r_data.get('imgs')
        elif tweet_type == 'quote':
            quote_data = tdata.get('quote_data', {})
            q_user = quote_data.get('user_info', {})
            q_data = quote_data.get('data', {})
            try:
                origin_created_at = parser.parse(q_data.get('created_at', str(now))).astimezone(SHA_TZ)
            except:
                origin_created_at = now
            t = f"{user_info['name']}转推了\n发布于{created_at}\n\n{tdata['text']}\n\n转发自:\n{q_user.get('name')}发布于{origin_created_at}\n\n{q_data.get('text')}\n\n{url}"
            imgs = q_data.get('imgs')

        for group in groups:
            if imgs:
                # Send first image or all? original code sends 'imgs' which might be list
                # botoy sendGroupPic usually accepts list or string
                await action.sendGroupPic(group=group, text=t, url=imgs)
            else:
                await action.sendGroupText(group=group, text=t)
                
    except Exception:
        logger.exception(f"Error processing tweet {tdata.get('id')}")
