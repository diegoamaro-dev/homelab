import psutil


class Tools:

    def __init__(self):
        pass

    def system_status(self) -> str:
        """
        Get CPU, RAM and disk usage of the homelab server.
        """

        cpu = psutil.cpu_percent(interval=1)

        ram = psutil.virtual_memory()
        ram_used = ram.percent

        disk = psutil.disk_usage("/")
        disk_used = disk.percent

        result = f"""
Server status:

CPU usage: {cpu}%
RAM usage: {ram_used}%
Disk usage: {disk_used}%
"""

        return result
