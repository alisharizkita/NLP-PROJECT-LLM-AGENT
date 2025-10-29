from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from src.database.models import User, Restaurant, MenuItem, UserFavorite, OrderHistory
from typing import List, Optional, Dict
import logging
import math
import googlemaps
from src.config import Config

logger = logging.getLogger(__name__)

def _get_haversine_formula(lat, lon, restaurant_model):
    """
    Helper function untuk formula Haversine (jarak) di SQL.
    Mengembalikan kolom jarak dalam KM.
    """
    # 6371 = radius bumi dalam km
    return (
        6371 * func.acos(
            func.cos(func.radians(lat)) *
            func.cos(func.radians(restaurant_model.latitude)) *
            func.cos(func.radians(restaurant_model.longitude) - func.radians(lon)) +
            func.sin(func.radians(lat)) *
            func.sin(func.radians(restaurant_model.latitude))
        )
    )

class DatabaseOperations:
    """Database CRUD operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ===== USER OPERATIONS =====
    
    def get_or_create_user(self, discord_id: str, username: str = None) -> User:
        """Get existing user or create new one"""
        user = self.session.query(User).filter(User.discord_id == discord_id).first()
        
        if not user:
            user = User(discord_id=discord_id, username=username)
            self.session.add(user)
            self.session.commit()
            logger.info(f"Created new user: {discord_id}")
        
        return user
    
    def update_user_preferences(self, user_id: int, budget: int = None, 
                                location: str = None, preferences: dict = None) -> User:
        """Update user preferences"""
        user = self.session.query(User).filter(User.id == user_id).first()
        
        if user:
            if budget:
                user.default_budget = budget
            if location:
                user.default_location = location
            if preferences:
                user.preferences = preferences
            
            self.session.commit()
            logger.info(f"Updated preferences for user {user_id}")
        
        return user
    
    # ===== RESTAURANT OPERATIONS =====
    
    def search_restaurants(self, location: str = None, budget: int = None,
                          cuisine_type: str = None, category: str = None,
                          radius_km: int = 5) -> List[Restaurant]:
        """Search restaurants based on criteria"""
        query = self.session.query(Restaurant)
        
        if location:
            try:
                # 1. Geocode lokasi user
                gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
                geocode_result = gmaps.geocode(location)
                
                if geocode_result:
                    user_lat = geocode_result[0]['geometry']['location']['lat']
                    user_lon = geocode_result[0]['geometry']['location']['lng']
                    
                    # 2. Buat kolom 'distance' menggunakan Haversine
                    distance_col = _get_haversine_formula(user_lat, user_lon, Restaurant).label("distance")
                    
                    # 3. Query dengan filter jarak dan urutkan
                    query = query.add_columns(distance_col).filter(
                        Restaurant.latitude != None,  # Pastikan resto punya koordinat
                        Restaurant.longitude != None,
                        distance_col <= radius_km
                    ).order_by(distance_col) # Urutkan berdasarkan terdekat
                    
                else:
                    # Fallback ke pencarian teks lama jika geocoding gagal
                    logger.warning(f"Gagal geocode '{location}', fallback ke pencarian teks.")
                    query = query.filter(Restaurant.location.ilike(f"%{location}%"))

            except Exception as e:
                logger.error(f"Error geocoding '{location}', fallback ke pencarian teks: {e}")
                query = query.filter(Restaurant.location.ilike(f"%{location}%"))
            # --- AKHIR LOGIKA LOKASI BARU ---
        
        else:
            # Jika tidak ada lokasi, urutkan berdasarkan rating
            query = query.order_by(Restaurant.rating.desc())
        
        if budget:
            query = query.filter(Restaurant.avg_price <= budget)
        
        if cuisine_type:
            query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
        
        if category:
            query = query.filter(Restaurant.category.ilike(f"%{category}%"))
        
        results = query.limit(10).all()
        
        # Jika query pakai lokasi, hasilnya (Restaurant, distance)
        # Kita hanya perlu return object Restaurant-nya
        if location and results and isinstance(results[0], tuple):
            restaurants = [r[0] for r in results] # Ambil object Restaurant (elemen pertama)
        else:
            restaurants = results

        return restaurants
    
    def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Restaurant]:
        """Get restaurant by ID"""
        return self.session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    
    def get_restaurant_menu(self, restaurant_id: int) -> List[MenuItem]:
        """Get menu items for a restaurant"""
        return self.session.query(MenuItem).filter(
            and_(MenuItem.restaurant_id == restaurant_id, MenuItem.is_available == True)
        ).all()
    
    # ===== FAVORITES OPERATIONS =====
    
    def add_favorite(self, user_id: int, restaurant_id: int) -> UserFavorite:
        """Add restaurant to user favorites"""
        existing = self.session.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.restaurant_id == restaurant_id)
        ).first()
        
        if existing:
            logger.info(f"Restaurant {restaurant_id} already in favorites")
            return existing
        
        favorite = UserFavorite(user_id=user_id, restaurant_id=restaurant_id)
        self.session.add(favorite)
        self.session.commit()
        logger.info(f"Added restaurant {restaurant_id} to favorites")
        
        return favorite
    
    def remove_favorite(self, user_id: int, restaurant_id: int) -> bool:
        """Remove restaurant from favorites"""
        favorite = self.session.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.restaurant_id == restaurant_id)
        ).first()
        
        if favorite:
            self.session.delete(favorite)
            self.session.commit()
            logger.info(f"Removed restaurant {restaurant_id} from favorites")
            return True
        
        return False
    
    def get_user_favorites(self, user_id: int) -> List[Restaurant]:
        """Get user's favorite restaurants"""
        favorites = self.session.query(Restaurant).join(UserFavorite).filter(
            UserFavorite.user_id == user_id
        ).all()
        
        return favorites
    
    # ===== ORDER HISTORY OPERATIONS =====
    
    def add_order(self, user_id: int, restaurant_id: int, menu_items: list,
                  total_price: int, mood: str = None) -> OrderHistory:
        """Add order to history"""
        order = OrderHistory(
            user_id=user_id,
            restaurant_id=restaurant_id,
            menu_items=menu_items,
            total_price=total_price,
            mood=mood
        )
        
        self.session.add(order)
        self.session.commit()
        logger.info(f"Added order for user {user_id}")
        
        return order
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[OrderHistory]:
        """Get user's order history"""
        orders = self.session.query(OrderHistory).filter(
            OrderHistory.user_id == user_id
        ).order_by(OrderHistory.order_date.desc()).limit(limit).all()
        
        return orders
    
    def add_review(self, order_id: int, rating: int, review: str = None) -> OrderHistory:
        """Add review to an order"""
        order = self.session.query(OrderHistory).filter(OrderHistory.id == order_id).first()
        
        if order:
            order.rating = rating
            order.review = review
            self.session.commit()
            logger.info(f"Added review for order {order_id}")
        
        return order
    
    # ===== CONVERSATION OPERATIONS =====
    
    # def save_conversation(self, user_id: int, role: str, content: str) -> Conversation:
    #     """Save conversation message"""
    #     conversation = Conversation(user_id=user_id, role=role, content=content)
    #     self.session.add(conversation)
    #     self.session.commit()
        
    #     return conversation
    
    # def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Conversation]:
    #     """Get recent conversation history"""
    #     conversations = self.session.query(Conversation).filter(
    #         Conversation.user_id == user_id
    #     ).order_by(Conversation.timestamp.desc()).limit(limit).all()
        
    #     return list(reversed(conversations))
    
    # def clear_conversation_history(self, user_id: int) -> bool:
    #     """Clear conversation history for user"""
    #     self.session.query(Conversation).filter(Conversation.user_id == user_id).delete()
    #     self.session.commit()
    #     logger.info(f"Cleared conversation history for user {user_id}")
        
    #     return True
    
    # ===== RECOMMENDATIONS =====
    
    def get_recommendations_by_mood(self, mood: str, budget: int = None, 
                                   location: str = None) -> List[Restaurant]:
        """Get restaurant recommendations based on mood"""
        
        # Map moods to categories/cuisine types
        mood_mapping = {
            "happy": ["dessert", "cafe", "italian"],
            "sad": ["comfort food", "indonesian", "pizza"],
            "stressed": ["cafe", "japanese", "healthy"],
            "hungry": ["all you can eat", "buffet", "indonesian"],
            "romantic": ["fine dining", "italian", "french"],
            "quick": ["fast food", "street food", "cafe"]
        }
        
        categories = mood_mapping.get(mood.lower(), [])
        
        query = self.session.query(Restaurant)
        
        if categories:
            filters = [or_(
                Restaurant.category.ilike(f"%{cat}%"),
                Restaurant.cuisine_type.ilike(f"%{cat}%")
            ) for cat in categories]
            query = query.filter(or_(*filters))
        
        if budget:
            query = query.filter(Restaurant.avg_price <= budget)
        
        if location:
            query = query.filter(Restaurant.location.ilike(f"%{location}%"))
        
        restaurants = query.order_by(Restaurant.rating.desc()).limit(5).all()
        return restaurants
