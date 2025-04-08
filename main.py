from pkg.plugin.context import register, BasePlugin, APIHost
from pkg.platform.types import Plain, MessageChain
import asyncio
from datetime import datetime, timedelta, timezone

# 创建 UTC+8 时区对象（中国标准时间）
china_tz = timezone(timedelta(hours=8))

@register(
    name="GlobalReminderPlugin",
    description="全体好友提醒插件，支持直接修改提醒内容及分时差发送消息以规避 QQ 风控",
    version="1.0",
    author="YourName"
)
class GlobalReminderPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        super().__init__()
        self.host = host
        # 直接在代码中设置提醒消息内容，后续可根据需要修改
        self.reminder_message = (
            "【温馨提醒】\n"
            "请注意查收每日通知，别忘了查看重要消息哦！\n"
            f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # 设置每天发送提醒的时间（24小时制，字符串格式 HH:MM）
        self.reminder_time = "09:00"
        # 设置每条消息发送后与下一位好友之间的延迟（单位：秒）
        self.friend_delay = 3

        # 启动定时任务，周期性检查是否达到触发条件
        self.broadcast_task = asyncio.create_task(self.reminder_schedule())

    async def reminder_schedule(self):
        """
        无限循环，每隔一段时间检查一次当前时间，
        当达到设定的提醒时间时触发全体好友提醒任务，
        为防止连续触发，在成功触发一次后等待超过1分钟。
        """
        while True:
            now = datetime.now(china_tz)
            current_time_str = now.strftime("%H:%M")
            if current_time_str == self.reminder_time:
                self.logger.info("触发全体好友提醒任务")
                await self.broadcast_reminder()
                # 成功触发后等待 61 秒，确保不会在同一分钟内重复发送
                await asyncio.sleep(61)
            else:
                # 每隔 30 秒检查一次（可根据需要调整）
                await asyncio.sleep(30)

    async def broadcast_reminder(self):
        """
        获取所有好友列表，更新提醒消息内容（附加当前时间），
        并依次向每个好友发送提醒，两个好友之间有固定延迟以规避风控。
        """
        try:
            # 调用 API 获取好友列表，实际实现请参考你的 langbot 平台接口
            friend_list = await self.host.get_friend_list()
        except Exception as e:
            self.logger.error(f"获取好友列表失败: {e}")
            return

        self.logger.info(f"开始向 {len(friend_list)} 个好友发送提醒消息")
        # 每次广播前更新提醒内容中的时间戳
        self.reminder_message = (
            "【温馨提醒】\n"
            "请注意查收每日通知，别忘了查看重要消息哦！\n"
            f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # 将文本消息转换为 langbot 的消息链格式
        msg = MessageChain([Plain(self.reminder_message)])
        for friend in friend_list:
            try:
                # 发送提醒消息，target_type 设为 "person" 表示私聊（好友消息）
                await self.host.send_active_message(
                    adapter=self.host.get_platform_adapters()[0],
                    target_type="person",
                    target_id=str(friend),
                    message=msg,
                )
                self.logger.info(f"成功向 {friend} 发送提醒消息")
            except Exception as e:
                self.logger.error(f"向 {friend} 发送提醒消息失败: {e}")
            # 等待设定的时差再发送下一条，规避风控
            await asyncio.sleep(self.friend_delay)

    async def on_unregister(self) -> None:
        """
        插件注销时，取消定时任务以确保不会产生残留的任务。
        """
        if self.broadcast_task:
            self.broadcast_task.cancel()
            self.broadcast_task = None
