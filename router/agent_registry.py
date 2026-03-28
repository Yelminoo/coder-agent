import json
import os
from typing import Dict, List, Optional


class AgentRegistry:
    def __init__(self, path: str = "data/agents.json"):
        self.path = path
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.path):
            return {
                "default_agent": "context_agent",
                "agents": [
                    {
                        "id": "context_agent",
                        "name": "Context Agent",
                        "mode": "contextual",
                        "description": "Context-aware responses with optional code when requested.",
                        "system_prompt": "You are a context-aware assistant. Generate code only when requested."
                    }
                ]
            }
        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def reload(self) -> None:
        self._config = self._load_config()

    def list_agents(self) -> List[Dict]:
        return self._config.get("agents", [])

    def get_default_agent_id(self) -> str:
        return self._config.get("default_agent", "context_agent")

    def save_config(self) -> None:
        """Save current configuration to file."""
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self._config, file, indent=2, ensure_ascii=False)
    
    def update_agent(self, agent_id: str, updates: Dict) -> bool:
        """Update an agent's properties."""
        agents = self._config.get("agents", [])
        for agent in agents:
            if agent.get("id") == agent_id:
                # Update allowed fields
                if "name" in updates:
                    agent["name"] = updates["name"]
                if "system_prompt" in updates:
                    agent["system_prompt"] = updates["system_prompt"]
                if "description" in updates:
                    agent["description"] = updates["description"]
                self.save_config()
                self.reload()
                return True
        return False
    
    def create_agent(self, agent_data: Dict) -> Dict:
        """Create a new agent."""
        agent_id = agent_data.get("id")
        if not agent_id:
            return {"success": False, "error": "Agent ID is required"}
        
        # Check if agent ID already exists
        agents = self._config.get("agents", [])
        if any(agent.get("id") == agent_id for agent in agents):
            return {"success": False, "error": f"Agent ID '{agent_id}' already exists"}
        
        # Create new agent
        new_agent = {
            "id": agent_id,
            "name": agent_data.get("name", "New Agent"),
            "mode": agent_data.get("mode", "contextual"),
            "description": agent_data.get("description", ""),
            "system_prompt": agent_data.get("system_prompt", "You are a helpful assistant.")
        }
        
        agents.append(new_agent)
        self.save_config()
        self.reload()
        return {"success": True, "agent": new_agent}
    
    def delete_agent(self, agent_id: str) -> Dict:
        """Delete an agent."""
        agents = self._config.get("agents", [])
        
        # Prevent deleting if it's the only agent
        if len(agents) <= 1:
            return {"success": False, "error": "Cannot delete the last agent"}
        
        # Prevent deleting default agent
        if agent_id == self.get_default_agent_id():
            return {"success": False, "error": "Cannot delete the default agent"}
        
        # Find and remove agent
        original_count = len(agents)
        self._config["agents"] = [a for a in agents if a.get("id") != agent_id]
        
        if len(self._config["agents"]) == original_count:
            return {"success": False, "error": "Agent not found"}
        
        self.save_config()
        self.reload()
        return {"success": True}

    def get_agent(self, agent_id: Optional[str]) -> Dict:
        selected_id = agent_id or self.get_default_agent_id()
        for agent in self.list_agents():
            if agent.get("id") == selected_id:
                return agent

        default_id = self.get_default_agent_id()
        for agent in self.list_agents():
            if agent.get("id") == default_id:
                return agent

        agents = self.list_agents()
        return agents[0] if agents else {
            "id": "context_agent",
            "name": "Context Agent",
            "mode": "contextual",
            "description": "Fallback context-aware agent",
            "system_prompt": "You are a context-aware assistant."
        }
