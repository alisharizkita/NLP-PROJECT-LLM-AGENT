import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agent.agent_core import FoodieAgent
from src.agent.tools import execute_tool, calculate_calories

class TestFoodieAgent:
    """Test cases for FoodieAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return FoodieAgent()
    
    def test_agent_initialization(self, agent):
        """Test 1: Agent initializes correctly"""
        assert agent is not None
        assert agent.llm is not None
        assert agent.system_prompt is not None
        assert len(agent.tools) > 0
        assert isinstance(agent.conversations, dict)
        assert isinstance(agent.user_preferences, dict)
        print("✅ Test 1 passed: Agent initialization")
    
    def test_new_user_conversation(self, agent):
        """Test 2: New user gets empty conversation history"""
        user_id = "test_user_123"
        
        # Before first message
        assert user_id not in agent.conversations
        
        # Mock LLM response
        with patch.object(agent.llm, 'chat', return_value={
            "content": "Halo! Ada yang bisa aku bantu?",
            "tool_calls": None,
            "role": "assistant"
        }):
            response = agent.process_message(user_id, "testuser", "Halo")
            
            # After first message
            assert user_id in agent.conversations
            assert len(agent.conversations[user_id]) == 2  # user + assistant
            assert response is not None
            print("✅ Test 2 passed: New user conversation")
    
    def test_conversation_memory(self, agent):
        """Test 3: Agent remembers previous conversation"""
        user_id = "test_user_456"
        
        with patch.object(agent.llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                "content": "Response",
                "tool_calls": None,
                "role": "assistant"
            }
            
            # First message
            agent.process_message(user_id, "testuser", "Aku suka nasi goreng")
            assert len(agent.conversations[user_id]) == 2
            
            # Second message
            agent.process_message(user_id, "testuser", "Ada rekomendasi lain?")
            assert len(agent.conversations[user_id]) == 4
            
            # Check that history is passed to LLM
            calls = mock_chat.call_args_list
            second_call_messages = calls[1][0][0]
            assert len(second_call_messages) > 2  # system + history
            print("✅ Test 3 passed: Conversation memory")
    
    def test_reset_conversation(self, agent):
        """Test 4: Conversation reset works correctly"""
        user_id = "test_user_789"
        
        # Create conversation
        agent.conversations[user_id] = [
            {"role": "user", "content": "Test 1"},
            {"role": "assistant", "content": "Response 1"}
        ]
        
        assert len(agent.conversations[user_id]) == 2
        
        # Reset
        response = agent.reset_conversation(user_id)
        
        assert len(agent.conversations[user_id]) == 0
        assert "reset" in response.lower()
        print("✅ Test 4 passed: Conversation reset")
    
    def test_conversation_stats(self, agent):
        """Test 5: Conversation statistics are accurate"""
        user_id = "test_user_stats"
        
        # Empty stats
        stats = agent.get_conversation_stats(user_id)
        assert stats["total_messages"] == 0
        assert stats["user_messages"] == 0
        assert stats["bot_messages"] == 0
        
        # Add some messages
        agent.conversations[user_id] = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Reply 1"},
            {"role": "user", "content": "Msg 2"},
            {"role": "assistant", "content": "Reply 2"},
        ]
        
        stats = agent.get_conversation_stats(user_id)
        assert stats["total_messages"] == 4
        assert stats["user_messages"] == 2
        assert stats["bot_messages"] == 2
        print("✅ Test 5 passed: Conversation statistics")
    
    def test_tool_execution(self, agent):
        """Test 6: Tool execution works correctly"""
        # Test calorie calculator tool
        result = calculate_calories("nasi goreng", "medium")
        
        assert result["success"] == True
        assert "calories" in result
        assert result["calories"] > 0
        assert result["portion"] == "medium"
        
        # Test with unknown food
        result = calculate_calories("makanan_aneh_xyz", "medium")
        assert result["success"] == False or result["calories"] > 0  # Should estimate or fail gracefully
        
        print("✅ Test 6 passed: Tool execution")
    
    def test_error_handling(self, agent):
        """Test 7: Agent handles errors gracefully"""
        with patch.object(agent.llm, 'chat', side_effect=Exception("API Error")):
            response = agent.process_message("error_user", "testuser", "Test message")
            
            # Should return error message, not crash
            assert response is not None
            assert "kesalahan" in response.lower() or "error" in response.lower()
            print("✅ Test 7 passed: Error handling")