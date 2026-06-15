import requests
from pydantic import BaseModel, Field


class Tools:

    def __init__(self):
        pass

    def docker_containers(self) -> str:
        """
        Get the list of running Docker containers from the homelab server.
        """

        try:
            response = requests.get(
                "http://192.168.178.79:5050/docker/containers", timeout=5
            )
            data = response.json()

            if not data:
                return "No running Docker containers found."

            result = "Running Docker containers:\n"

            for container in data:
                name = container.get("name", "unknown")
                status = container.get("status", "unknown")
                result += f"- {name} ({status})\n"

            return result

        except Exception as e:
            return f"Error retrieving Docker containers: {str(e)}"
