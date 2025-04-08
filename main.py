from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
import asyncio

"""
定时向所有好友发送内容的插件
你可以直接在代码里修改要发送的内容和发送间隔。
"""

# 注册插件
@register(name="PeriodicMessage", description="定时向所有好友发送内容的插件", version="0.1", author="YourName")
class PeriodicMessagePlugin(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        self.ap = host
        # 在此修改要发送的内容
        self.message_content = "这里是定时发送的消息内容"
        # 定时发送间隔（单位：秒），可在此修改发送频率
        self.send_interval = 3600  # 例如：3600秒 = 1小时

    # 异步初始化
    async def initialize(self):
        self.ap.logger.debug("PeriodicMessagePlugin 初始化完成，开始启动定时发送任务。")
        # 创建一个后台异步任务进行定时发送
        asyncio.create_task(self.periodic_send_task())

    # 定时发送消息的异步任务
    async def periodic_send_task(self):
        while True:
            try:
                # 获取所有好友的ID列表
                # 请根据实际API调整此方法名称，如果没有该方法，可自行实现好友列表获取机制
                friend_list = self.ap.get_all_friend_ids()  
                self.ap.logger.debug("开始向所有好友发送定时消息，好友列表：{}".format(friend_list))
                
                # 遍历好友列表并发送消息
                for friend_id in friend_list:
                    await self.ap.send_message(friend_id, self.message_content)
                
                # 等待设定的时间间隔后再次发送
                await asyncio.sleep(self.send_interval)
            except Exception as e:
                self.ap.logger.error("定时发送任务发生异常：{}".format(e))
                # 出现异常时同样等待设定的时间间隔后重试
                await asyncio.sleep(self.send_interval)

    # 插件卸载时触发
    def __del__(self):
        # 如有必要，可在此处加入插件卸载时的清理工作
        pass
