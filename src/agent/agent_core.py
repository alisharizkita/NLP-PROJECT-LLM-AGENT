from src.agent.llm_client import GroqClient
from src.agent.tools import get_tools_definition, execute_tool
from src.agent.prompts import get_system_prompt
from src.config import Config
from typing import Dict, List
import logging
import json

logger = logging.getLogger(__name__)

class FoodieAgent:
    """Main FoodieBot agent with in-memory conversation storage"""
    
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = get_system_prompt()
        self.tools = get_tools_definition()
        
        # In-memory storage for conversations (per user)
        # Format: {discord_id: [{"role": "user/assistant", "content": "..."}]}
        self.conversations = {}
        
        # User preferences (optional, in-memory)
        # Format: {discord_id: {"location": "Jakarta", "budget": 50000}}
        self.user_preferences = {}
        
        logger.info("FoodieAgent initialized with in-memory storage")
    
    def process_message(self, discord_id: str, username: str, message: str) -> str:
        """Process user message and return bot response"""
        try:
            # Get or create conversation
            if discord_id not in self.conversations:
                self.conversations[discord_id] = []
                logger.info(f"New conversation started for user {discord_id}")
            
            history = self.conversations[discord_id]
            
            # Add user message
            history.append({"role": "user", "content": message})
            
            # Keep only recent messages
            if len(history) > Config.MAX_CONVERSATION_HISTORY * 2:
                history = history[-Config.MAX_CONVERSATION_HISTORY * 2:]
                self.conversations[discord_id] = history
            
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + history
            
            # Call LLM (dengan tools)
            response = self.llm.chat(messages, tools=self.tools)
            
            # Handle tool calls
            if response["tool_calls"]:
                response_text = self._handle_tool_calls(response, messages, discord_id)
            else:
                response_text = response["content"]
            
            # FILTER: Remove exposed function syntax (safety net)
            if response_text:
                import re
                # Remove <function=...> tags
                response_text = re.sub(r'<function=.*?</function>', '', response_text)
                # Remove JSON-like tool calls
                response_text = re.sub(r'\{"location".*?\}', '', response_text)
                response_text = response_text.strip()
            
            # Save assistant response
            if response_text:
                history.append({"role": "assistant", "content": response_text})
            
            return response_text
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Maaf, terjadi kesalahan. Coba lagi ya! 😅"
    
    def _handle_tool_calls(self, response: Dict, messages: List[Dict], 
                          discord_id: str) -> str:
        """
        Handle function/tool calls from LLM
        
        Args:
            response: LLM response with tool calls
            messages: Current conversation messages
            discord_id: User ID
            
        Returns:
            Final response text
        """
        try:
            # Execute each tool call
            tool_results = []
            
            for tool_call in response["tool_calls"]:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {function_name} for user {discord_id}")
                
                # Execute the tool
                result = execute_tool(function_name, arguments)
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            
            # Add tool results to messages
            messages.append({
                "role": "assistant",
                "content": response["content"],
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response["tool_calls"]
                ]
            })
            
            for tool_result in tool_results:
                messages.append(tool_result)
            
            # Get final response from LLM
            final_response = self.llm.chat(messages)
            
            return final_response["content"]
        
        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            return "Maaf, terjadi kesalahan saat memproses request kamu. 😅"
    
    def reset_conversation(self, discord_id: str) -> str:
        """Reset conversation history for user"""
        if discord_id in self.conversations:
            self.conversations[discord_id] = []
            logger.info(f"Conversation reset for user {discord_id}")
            return "Conversation history berhasil direset! Mari mulai dari awal. 😊"
        else:
            return "Belum ada conversation history yang perlu direset."
    
    def get_conversation_stats(self, discord_id: str) -> Dict:
        """Get conversation statistics for user"""
        if discord_id not in self.conversations:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "bot_messages": 0
            }
        
        history = self.conversations[discord_id]
        user_msgs = len([m for m in history if m["role"] == "user"])
        bot_msgs = len([m for m in history if m["role"] == "assistant"])
        
        return {
            "total_messages": len(history),
            "user_messages": user_msgs,
            "bot_messages": bot_msgs
        }
    
    def set_user_preference(self, discord_id: str, key: str, value: any) -> bool:
        """Set user preference"""
        if discord_id not in self.user_preferences:
            self.user_preferences[discord_id] = {}
        
        self.user_preferences[discord_id][key] = value
        logger.info(f"Set preference {key}={value} for user {discord_id}")
        return True
    
    def get_user_preferences(self, discord_id: str) -> Dict:
        """Get user preferences"""
        return self.user_preferences.get(discord_id, {})
    
    def get_active_users_count(self) -> int:
        """Get count of users with active conversations"""
        return len(self.conversations)