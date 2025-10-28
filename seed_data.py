#!/usr/bin/env python3
"""
Seed database with sample restaurant data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import db_manager
from src.database.models import Restaurant, MenuItem
from src.utils.logger import setup_logger

logger = setup_logger()

SAMPLE_RESTAURANTS = [
    {
        "name": "Warung Tekko",
        "location": "Kebayoran Baru, Jakarta Selatan",
        "category": "Indonesian",
        "price_range": "Rp 50.000 - 100.000",
        "avg_price": 75000,
        "rating": 4.5,
        "cuisine_type": "Indonesian",
        "opening_hours": "10:00 - 22:00",
        "contact": "021-12345678",
        "description": "Restoran Indonesia dengan suasana tradisional dan menu comfort food",
        "menu": [
            {"name": "Nasi Goreng Kambing", "price": 65000, "category": "Main Course", "description": "Nasi goreng dengan daging kambing empuk"},
            {"name": "Soto Betawi", "price": 55000, "category": "Main Course", "description": "Soto khas Betawi dengan santan"},
            {"name": "Es Teh Manis", "price": 8000, "category": "Beverage", "description": "Teh manis segar"},
            {"name": "Es Jeruk", "price": 12000, "category": "Beverage", "description": "Jus jeruk segar"},
        ]
    },
    {
        "name": "Kopi Kenangan Premium",
        "location": "Senopati, Jakarta Selatan",
        "category": "Cafe",
        "price_range": "Rp 25.000 - 60.000",
        "avg_price": 40000,
        "rating": 4.3,
        "cuisine_type": "Cafe",
        "opening_hours": "08:00 - 23:00",
        "contact": "021-23456789",
        "description": "Kafe modern dengan berbagai pilihan kopi dan dessert",
        "menu": [
            {"name": "Kopi Kenangan Mantan", "price": 28000, "category": "Beverage", "description": "Kopi susu gula aren signature"},
            {"name": "Es Kopi Susu Tetangga", "price": 32000, "category": "Beverage", "description": "Kopi susu dengan foam creamy"},
            {"name": "Croissant", "price": 35000, "category": "Snack", "description": "Croissant butter fresh"},
            {"name": "Cake Coklat", "price": 45000, "category": "Dessert", "description": "Cake coklat lembut"},
        ]
    },
    {
        "name": "Warteg Bahari",
        "location": "Blok M, Jakarta Selatan",
        "category": "Indonesian",
        "price_range": "Rp 15.000 - 30.000",
        "avg_price": 22000,
        "rating": 4.2,
        "cuisine_type": "Indonesian",
        "opening_hours": "06:00 - 21:00",
        "contact": "021-34567890",
        "description": "Warteg dengan menu lengkap dan harga terjangkau",
        "menu": [
            {"name": "Nasi + 2 Lauk", "price": 20000, "category": "Main Course", "description": "Nasi putih dengan pilihan 2 lauk"},
            {"name": "Nasi + 3 Lauk", "price": 25000, "category": "Main Course", "description": "Nasi putih dengan pilihan 3 lauk"},
            {"name": "Tempe Goreng", "price": 5000, "category": "Side Dish", "description": "Tempe goreng crispy"},
            {"name": "Ayam Goreng", "price": 12000, "category": "Side Dish", "description": "Ayam goreng bumbu kuning"},
        ]
    },
    {
        "name": "Sushi Tei",
        "location": "Grand Indonesia, Jakarta Pusat",
        "category": "Japanese",
        "price_range": "Rp 100.000 - 300.000",
        "avg_price": 180000,
        "rating": 4.6,
        "cuisine_type": "Japanese",
        "opening_hours": "10:00 - 22:00",
        "contact": "021-45678901",
        "description": "Restoran Jepang dengan berbagai pilihan sushi dan sashimi",
        "menu": [
            {"name": "Salmon Sashimi", "price": 95000, "category": "Sashimi", "description": "Sashimi salmon premium"},
            {"name": "California Roll", "price": 58000, "category": "Sushi", "description": "Sushi roll dengan kepiting dan alpukat"},
            {"name": "Ramen Original", "price": 68000, "category": "Main Course", "description": "Ramen kuah original dengan chashu"},
            {"name": "Green Tea Ice Cream", "price": 35000, "category": "Dessert", "description": "Es krim green tea"},
        ]
    },
    {
        "name": "Pizza Hut",
        "location": "Pondok Indah Mall, Jakarta Selatan",
        "category": "Fast Food",
        "price_range": "Rp 50.000 - 150.000",
        "avg_price": 90000,
        "rating": 4.0,
        "cuisine_type": "Italian",
        "opening_hours": "10:00 - 22:00",
        "contact": "021-56789012",
        "description": "Chain pizza internasional dengan berbagai varian topping",
        "menu": [
            {"name": "Meat Lovers Personal", "price": 65000, "category": "Pizza", "description": "Pizza dengan berbagai daging"},
            {"name": "Super Supreme Regular", "price": 120000, "category": "Pizza", "description": "Pizza dengan topping lengkap"},
            {"name": "Spaghetti Bolognese", "price": 55000, "category": "Pasta", "description": "Spaghetti dengan saus daging"},
            {"name": "Chicken Wings", "price": 45000, "category": "Appetizer", "description": "Sayap ayam goreng crispy"},
        ]
    },
    {
        "name": "Bakso Boedjangan",
        "location": "Tebet, Jakarta Selatan",
        "category": "Indonesian",
        "price_range": "Rp 25.000 - 60.000",
        "avg_price": 40000,
        "rating": 4.4,
        "cuisine_type": "Indonesian",
        "opening_hours": "10:00 - 21:00",
        "contact": "021-67890123",
        "description": "Bakso dengan berbagai pilihan ukuran dan toping",
        "menu": [
            {"name": "Bakso Jumbo", "price": 45000, "category": "Main Course", "description": "Bakso ukuran jumbo dengan mie"},
            {"name": "Bakso Urat", "price": 38000, "category": "Main Course", "description": "Bakso dengan urat sapi"},
            {"name": "Mie Ayam Bakso", "price": 32000, "category": "Main Course", "description": "Mie ayam dengan bakso"},
            {"name": "Es Teh Jumbo", "price": 10000, "category": "Beverage", "description": "Es teh manis ukuran besar"},
        ]
    },
    {
        "name": "Geprek Bensu",
        "location": "Kemang, Jakarta Selatan",
        "category": "Indonesian",
        "price_range": "Rp 20.000 - 50.000",
        "avg_price": 32000,
        "rating": 4.3,
        "cuisine_type": "Indonesian",
        "opening_hours": "10:00 - 23:00",
        "contact": "021-78901234",
        "description": "Ayam geprek dengan level kepedasan yang bisa dipilih",
        "menu": [
            {"name": "Geprek Original", "price": 25000, "category": "Main Course", "description": "Ayam geprek level 1-5"},
            {"name": "Geprek Keju", "price": 32000, "category": "Main Course", "description": "Ayam geprek dengan keju meleleh"},
            {"name": "Geprek Mozarella", "price": 38000, "category": "Main Course", "description": "Ayam geprek dengan mozarella premium"},
            {"name": "Es Lemon Tea", "price": 8000, "category": "Beverage", "description": "Lemon tea segar"},
        ]
    },
    {
        "name": "Madam Wang",
        "location": "Senayan City, Jakarta Pusat",
        "category": "Chinese",
        "price_range": "Rp 80.000 - 200.000",
        "avg_price": 130000,
        "rating": 4.5,
        "cuisine_type": "Chinese",
        "opening_hours": "11:00 - 22:00",
        "contact": "021-89012345",
        "description": "Restoran Chinese dengan menu dimsum dan hotpot",
        "menu": [
            {"name": "Hakau", "price": 45000, "category": "Dimsum", "description": "Dimsum udang klasik"},
            {"name": "Siomay", "price": 42000, "category": "Dimsum", "description": "Dimsum ayam"},
            {"name": "Nasi Goreng Hongkong", "price": 68000, "category": "Main Course", "description": "Nasi goreng khas hongkong"},
            {"name": "Chinese Tea", "price": 25000, "category": "Beverage", "description": "Teh chinese premium"},
        ]
    },
    {
        "name": "Burger King",
        "location": "Plaza Semanggi, Jakarta Selatan",
        "category": "Fast Food",
        "price_range": "Rp 35.000 - 80.000",
        "avg_price": 55000,
        "rating": 4.1,
        "cuisine_type": "American",
        "opening_hours": "10:00 - 22:00",
        "contact": "021-90123456",
        "description": "Fast food dengan signature flame-grilled burger",
        "menu": [
            {"name": "Whopper", "price": 55000, "category": "Burger", "description": "Signature beef burger"},
            {"name": "Chicken Burger", "price": 45000, "category": "Burger", "description": "Crispy chicken burger"},
            {"name": "French Fries Regular", "price": 20000, "category": "Side Dish", "description": "Kentang goreng"},
            {"name": "Ice Cream Sundae", "price": 15000, "category": "Dessert", "description": "Es krim dengan topping"},
        ]
    },
    {
        "name": "Pasta de Waraku",
        "location": "Gandaria City, Jakarta Selatan",
        "category": "Italian",
        "price_range": "Rp 60.000 - 150.000",
        "avg_price": 95000,
        "rating": 4.4,
        "cuisine_type": "Italian",
        "opening_hours": "10:00 - 22:00",
        "contact": "021-01234567",
        "description": "Restoran Italian casual dengan berbagai pasta dan pizza",
        "menu": [
            {"name": "Carbonara", "price": 85000, "category": "Pasta", "description": "Pasta dengan saus carbonara creamy"},
            {"name": "Aglio Olio", "price": 75000, "category": "Pasta", "description": "Pasta dengan minyak bawang pedas"},
            {"name": "Margherita Pizza", "price": 95000, "category": "Pizza", "description": "Pizza klasik dengan tomat dan basil"},
            {"name": "Tiramisu", "price": 45000, "category": "Dessert", "description": "Dessert khas Italia"},
        ]
    }
]

def seed_database():
    """Populate database with sample data"""
    try:
        logger.info("Initializing database...")
        db_manager.initialize()
        db_manager.create_tables()
        
        logger.info("Seeding restaurant data...")
        
        with db_manager.get_session() as session:
            for resto_data in SAMPLE_RESTAURANTS:
                # Create restaurant
                menu_items = resto_data.pop("menu")
                
                restaurant = Restaurant(**resto_data)
                session.add(restaurant)
                session.flush()  # Get restaurant ID
                
                # Create menu items
                for item_data in menu_items:
                    menu_item = MenuItem(
                        restaurant_id=restaurant.id,
                        **item_data
                    )
                    session.add(menu_item)
                
                logger.info(f"Added: {restaurant.name}")
            
            session.commit()
        
        logger.info(f"✅ Successfully seeded {len(SAMPLE_RESTAURANTS)} restaurants!")
        print(f"\n✅ Database seeded with {len(SAMPLE_RESTAURANTS)} restaurants and their menus!")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db_manager.close()

if __name__ == "__main__":
    seed_database()
