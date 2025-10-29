from src.agent.llm_client import GroqClient
from src.agent.tools import get_tools_definition, execute_tool
from src.agent.prompts import get_system_prompt, get_time_based_greeting
from src.database.connection import db_manager
from src.database.operations import DatabaseOperations
from src.config import Config
from typing import Dict, List
import logging
import json
import re
from types import SimpleNamespace

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

                messages = [{"role": "system", "content": self.system_prompt}]

                user_message_clean = message.lower().strip("!?. ")
                greetings = ["halo", "hi", "hai", "pagi", "siang", "sore", "malam", "hey", "oi"]
                
                processed_message_content = message

                is_greeting = False
                
                if user_message_clean in greetings:
                    is_greeting = True
                
                if is_greeting:
                    current_greeting = get_time_based_greeting()
                    processed_message_content = f"{message} (Info Konteks: Saat ini adalah {current_greeting})"
                    logger.info(f"Injecting time context into generic greeting: {processed_message_content}")
                    
                messages.append({
                    "role": "user",
                    "content": processed_message_content
                })
                
                # Call LLM with tools
                response = self.llm.chat(messages, tools=self.tools)

                if not response["tool_calls"] and response["content"] and "<function=" in response["content"]:
                    logger.warning("LLM returned dirty tool call. Parsing manually...")
                    
                    # Cari <function=...>{...}<function> menggunakan regex
                    match = re.search(r"<function=([\w_]+)>(.*?)</function>", response["content"], re.DOTALL)
                    
                    if match:
                        func_name = match.group(1).strip()
                        func_args_str = match.group(2).strip()
                        
                        # Buat objek tool_call tiruan (mock)
                        mock_tool_call = SimpleNamespace()
                        mock_tool_call.id = "manual_call_001"
                        mock_tool_call.type = "function"
                        mock_tool_call.function = SimpleNamespace()
                        mock_tool_call.function.name = func_name
                        mock_tool_call.function.arguments = func_args_str  # Ini adalah string JSON
                        
                        # Timpa respons agar seolah-olah ini adalah panggilan tool bersih
                        response["tool_calls"] = [mock_tool_call]
                        response["content"] = None  # Buang teks obrolan yang kotor
                        logger.info(f"Manually parsed tool call: {func_name}")
                
                # Handle tool calls if any
                if response["tool_calls"]:
                    response_text = self._handle_tool_calls(
                        response, messages, user.id, db_ops
                    )
                else:
                    response_text = response["content"]
                
                # Save assistant response to DB
                # if response_text:
                #     db_ops.save_conversation(user.id, "assistant", response_text)
                
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
            
            for tool_call in response.get("tool_calls", []): 
                function_name = tool_call.function.name
                
                # Cek jika argumen sudah JSON string atau perlu di-load
                if isinstance(tool_call.function.arguments, str):
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON arguments from string: {tool_call.function.arguments}")
                        arguments = {} # Gagal parse, gunakan dict kosong
                else:
                    # Jika sudah dict (kasus normal, tapi sepertinya Groq selalu string)
                    arguments = tool_call.function.arguments
                
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
            assistant_content = response.get("content")

            # Buat list tool_calls yang bisa di-serialize
            serializable_tool_calls = []
            for tc in response.get("tool_calls", []):
                serializable_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments if isinstance(tc.function.arguments, str) else json.dumps(tc.function.arguments)
                    }
                })

            messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": serializable_tool_calls
            })
            
            for tool_result in tool_results:
                messages.append(tool_result)
            
            # Get final response from LLM
            final_response = self.llm.chat(messages)
            
            return final_response["content"]
        
        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            return "Maaf, terjadi kesalahan saat memproses request kamu. 😅"
    
    # def reset_conversation(self, discord_id: str) -> str:
    #     """Reset conversation history for user"""
    #     try:
    #         with db_manager.get_session() as session:
    #             db_ops = DatabaseOperations(session)
    #             user = db_ops.get_or_create_user(discord_id)
    #             db_ops.clear_conversation_history(user.id)
                
    #             return "Conversation history berhasil direset! Mari mulai dari awal. 😊"
        
    #     except Exception as e:
    #         logger.error(f"Error resetting conversation: {e}")
    #         return "Gagal reset conversation. Coba lagi ya!"
    
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