from src.agent.llm_client import GroqClient
from src.agent.tools import get_tools_definition, execute_tool
from src.agent.prompts import get_system_prompt
from src.database.connection import db_manager
from src.database.operations import DatabaseOperations
from src.config import Config
from typing import Dict, List
import logging
import json

logger = logging.getLogger(__name__)

class FoodieAgent:
    """Main FoodieBot agent orchestrator"""
    
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = get_system_prompt()
        self.tools = get_tools_definition()
        logger.info("FoodieAgent initialized")
    
    def process_message(self, discord_id: str, username: str, message: str) -> str:
        """
        Process user message and return bot response
        
        Args:
            discord_id: Discord user ID
            username: Discord username
            message: User message
            
        Returns:
            Bot response string
        """
        try:
            with db_manager.get_session() as session:
                db_ops = DatabaseOperations(session)
                
                # Get or create user
                user = db_ops.get_or_create_user(discord_id, username)
                
                # Get conversation history
                history = db_ops.get_conversation_history(user.id, limit=Config.MAX_CONVERSATION_HISTORY)
                
                # Build messages for LLM
                messages = [{"role": "system", "content": self.system_prompt}]
                
                # Add conversation history
                for conv in history:
                    messages.append({
                        "role": conv.role,
                        "content": conv.content
                    })
                
                # Add current user message
                messages.append({
                    "role": "user",
                    "content": message
                })
                
                # Save user message to DB
                db_ops.save_conversation(user.id, "user", message)
                
                # Call LLM with tools
                response = self.llm.chat(messages, tools=self.tools)
                
                # Handle tool calls if any
                if response["tool_calls"]:
                    response_text = self._handle_tool_calls(
                        response, messages, user.id, db_ops
                    )
                else:
                    response_text = response["content"]
                
                # Save assistant response to DB
                if response_text:
                    db_ops.save_conversation(user.id, "assistant", response_text)
                
                return response_text
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Maaf, terjadi kesalahan. Coba lagi ya! 😅"
    
    def _handle_tool_calls(self, response: Dict, messages: List[Dict], 
                          user_id: int, db_ops: DatabaseOperations) -> str:
        """
        Handle function/tool calls from LLM
        
        Args:
            response: LLM response with tool calls
            messages: Current conversation messages
            user_id: User ID
            db_ops: Database operations instance
            
        Returns:
            Final response text
        """
        try:
            # Execute each tool call
            tool_results = []
            
            for tool_call in response["tool_calls"]:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Inject user_id if needed
                if "user_id" in arguments and arguments["user_id"] is None:
                    arguments["user_id"] = user_id
                
                logger.info(f"Executing tool: {function_name}")
                
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
        try:
            with db_manager.get_session() as session:
                db_ops = DatabaseOperations(session)
                user = db_ops.get_or_create_user(discord_id)
                db_ops.clear_conversation_history(user.id)
                
                return "Conversation history berhasil direset! Mari mulai dari awal. 😊"
        
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            return "Gagal reset conversation. Coba lagi ya!"
    
    def get_user_info(self, discord_id: str) -> Dict:
        """Get user information"""
        try:
            with db_manager.get_session() as session:
                db_ops = DatabaseOperations(session)
                user = db_ops.get_or_create_user(discord_id)
                
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "default_budget": user.default_budget,
                    "default_location": user.default_location,
                    "preferences": user.preferences
                }
        
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {}