import requests


class Tools:

    def docker_logs(self, container_name: str = "openwebui", lines: int = 30) -> str:
        """
        REQUIRED TOOL.

        Always call this tool when the user asks for:
        - logs
        - container output
        - docker errors
        - openwebui logs
        - ollama logs
        - service logs
        """

        url = "http://192.168.178.79:5050/docker/logs"

        r = requests.get(
            url, params={"container": container_name, "lines": lines}, timeout=10
        )

        data = r.json()

        return data["logs"]
