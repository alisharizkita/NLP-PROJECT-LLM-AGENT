from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, ForeignKey, TIMESTAMP, JSON, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100))
    default_budget = Column(Integer, default=50000)
    default_location = Column(String(200))
    preferences = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    favorites = relationship("UserFavorite", back_populates="user")
    orders = relationship("OrderHistory", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Restaurant(Base):
    __tablename__ = 'restaurants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    category = Column(String(100))
    price_range = Column(String(50))
    avg_price = Column(Integer)
    rating = Column(DECIMAL(3, 2))
    cuisine_type = Column(String(100))
    opening_hours = Column(String(100))
    contact = Column(String(100))
    description = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant")
    favorites = relationship("UserFavorite", back_populates="restaurant")
    orders = relationship("OrderHistory", back_populates="restaurant")

class MenuItem(Base):
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    category = Column(String(100))
    is_available = Column(Boolean, default=True)
    image_url = Column(String(500))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")

class UserFavorite(Base):
    __tablename__ = 'user_favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))
    added_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    restaurant = relationship("Restaurant", back_populates="favorites")

class OrderHistory(Base):
    __tablename__ = 'order_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))
    menu_items = Column(JSON)
    total_price = Column(Integer)
    order_date = Column(TIMESTAMP, default=datetime.utcnow)
    mood = Column(String(100))
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    review = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
