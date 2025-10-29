from typing import Dict, List, Any
from src.database.connection import db_manager
from src.database.operations import DatabaseOperations
import logging
import json
import googlemaps
from src.config import Config

logger = logging.getLogger(__name__)

try:
    gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Google Maps client: {e}")
    gmaps = None

def get_tools_definition() -> List[Dict]:
    """
    Get OpenAI function calling format tool definitions
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Cari restoran berdasarkan lokasi, budget, jenis masakan, atau kategori",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Lokasi restoran (contoh: Jakarta Selatan, Kemang, BSD)"
                        },
                        "budget": {
                            "type": ["integer", "null"],
                            "description": "Budget maksimal dalam Rupiah (contoh: 50000)"
                        },
                        "cuisine_type": {
                            "type": "string",
                            "description": "Jenis masakan (contoh: Indonesian, Japanese, Italian)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Kategori restoran (contoh: cafe, fine dining, fast food)"
                        },
                        "radius_km": {
                            "type": "integer",
                            "description": "Jarak radius pencarian dalam kilometer (default 5km)",
                            "default": 5
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_google_maps_restaurants",
                "description": "Cari restoran di lokasi mana pun menggunakan Google Maps. Gunakan ini jika database internal tidak menemukan hasil atau jika lokasi berada di luar Jakarta.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Kueri pencarian (contoh: 'restoran murah dekat Jalan Kaliurang Yogyakarta')"
                        },
                        "budget": {
                            "type": ["integer", "null"],
                            "description": "Budget dalam Rupiah (opsional)"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_google_maps_details",
                "description": "Dapatkan detail info (website, no. telepon, jam buka) untuk restoran spesifik dari Google Maps menggunakan 'place_id'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "place_id": {
                            "type": "string",
                            "description": "ID unik Google Places untuk restoran, didapat dari 'search_google_maps_restaurants'."
                        }
                    },
                    "required": ["place_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_restaurant_details",
                "description": "Dapatkan detail lengkap restoran termasuk menu",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": "ID restoran"
                        }
                    },
                    "required": ["restaurant_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_to_favorites",
                "description": "Tambahkan restoran ke daftar favorit user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID user"
                        },
                        "restaurant_id": {
                            "type": "integer",
                            "description": "ID restoran"
                        }
                    },
                    "required": ["user_id", "restaurant_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_favorites",
                "description": "Dapatkan daftar restoran favorit user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID user"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_order",
                "description": "Simpan pesanan ke history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID user"
                        },
                        "restaurant_id": {
                            "type": "integer",
                            "description": "ID restoran"
                        },
                        "menu_items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Daftar menu yang dipesan"
                        },
                        "total_price": {
                            "type": "integer",
                            "description": "Total harga pesanan"
                        },
                        "mood": {
                            "type": "string",
                            "description": "Mood saat memesan"
                        }
                    },
                    "required": ["user_id", "restaurant_id", "menu_items", "total_price"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_order_history",
                "description": "Dapatkan riwayat pesanan user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID user"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Jumlah maksimal riwayat yang ditampilkan",
                            "default": 5
                        }
                    },
                    "required": ["user_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recommend_by_mood",
                "description": "Rekomendasikan restoran berdasarkan mood user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mood": {
                            "type": "string",
                            "description": "Mood user (happy, sad, stressed, hungry, romantic, quick)",
                            "enum": ["happy", "sad", "stressed", "hungry", "romantic", "quick"]
                        },
                        "budget": {
                            "type": ["integer", "null"],
                            "description": "Budget maksimal"
                        },
                        "location": {
                            "type": "string",
                            "description": "Lokasi preferensi"
                        }
                    },
                    "required": ["mood"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_user_preferences",
                "description": "Update preferensi default user (budget, lokasi)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID user"
                        },
                        "default_budget": {
                            "type": "integer",
                            "description": "Budget default"
                        },
                        "default_location": {
                            "type": "string",
                            "description": "Lokasi default"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
    ]


def execute_tool(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tool/function and return result
    """
    try:
        logger.info(f"Executing tool: {function_name} with args: {arguments}")
        
        with db_manager.get_session() as session:
            db_ops = DatabaseOperations(session)
            
            if function_name == "search_restaurants":
                location = arguments.get("location")
                budget = arguments.get("budget")
                cuisine_type = arguments.get("cuisine_type")
                category = arguments.get("category")

                restaurants = db_ops.search_restaurants(
                    location=location,
                    budget=budget,
                    cuisine_type=cuisine_type,
                    category=category
                )
                
                result = []
                for r in restaurants:
                    result.append({
                        "id": r.id,
                        "name": r.name,
                        "location": r.location,
                        "cuisine_type": r.cuisine_type,
                        "avg_price": r.avg_price,
                        "rating": float(r.rating) if r.rating else 0,
                        "description": r.description
                    })
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Ditemukan {len(result)} restoran"
                }
            
            elif function_name == "search_google_maps_restaurants":
                if not gmaps:
                    return {"success": False, "message": "Google Maps API client tidak terinisialisasi. Periksa API Key."}
                
                query = arguments.get("query")
                
                # Google Maps API memiliki 'price_level' (0-4), bukan budget integer
                # Kita bisa tambahkan 'murah', 'sedang', 'mahal' ke query
                budget = arguments.get("budget")
                if budget:
                    if budget <= 30000:
                        query = f"murah {query}"
                    elif budget <= 70000:
                        query = f"sedang {query}"
                    else:
                        query = f"mewah {query}"

                places_result = gmaps.places(query=query, region="ID", language="id")
                
                results = []
                for place in places_result.get("results", [])[:5]: # Ambil 5 teratas
                    results.append({
                        "name": place.get("name"),
                        "location": place.get("vicinity", place.get("formatted_address")),
                        "rating": place.get("rating", 0),
                        "total_ratings": place.get("user_ratings_total", 0),
                        "place_id": place.get("place_id"),
                        "price_level": place.get("price_level", "N/A"),
                        "status": place.get("business_status", "N/A")
                    })
                
                return {
                    "success": True,
                    "data": results,
                    "message": f"Ditemukan {len(results)} restoran dari Google Maps"
                }
            
            elif function_name == "get_google_maps_details":
                if not gmaps:
                    return {"success": False, "message": "Google Maps API client tidak terinisialisasi."}
                
                place_id = arguments.get("place_id")
                if not place_id:
                    return {"success": False, "message": "Error: 'place_id' diperlukan."}
                
                # Tentukan field apa saja yang kita inginkan (untuk menghemat biaya API)
                fields = ['name', 'website', 'formatted_phone_number', 'opening_hours', 'vicinity']
                
                try:
                    details_result = gmaps.place(
                        place_id=place_id,
                        fields=fields,
                        language="id"
                    )
                    
                    result_data = details_result.get('result', {})
                    
                    # Format jam buka agar lebih mudah dibaca LLM
                    opening_hours = "Tidak diketahui"
                    if 'opening_hours' in result_data:
                        opening_hours = ", ".join(result_data['opening_hours'].get('weekday_text', []))

                    return {
                        "success": True,
                        "data": {
                            "name": result_data.get('name'),
                            "address": result_data.get('vicinity'),
                            "website": result_data.get('website', 'Tidak ada website'),
                            "phone": result_data.get('formatted_phone_number', 'Tidak ada telepon'),
                            "opening_hours": opening_hours
                        },
                        "message": "Detail restoran berhasil diambil dari Google Maps."
                    }
                except Exception as e:
                    logger.error(f"Google Maps Place Details API error: {e}")
                    return {"success": False, "message": f"Google Maps API Error: {str(e)}"}
            
            elif function_name == "get_restaurant_details":
                restaurant = db_ops.get_restaurant_by_id(arguments["restaurant_id"])
                
                if not restaurant:
                    return {"success": False, "message": "Restoran tidak ditemukan"}
                
                menu_items = db_ops.get_restaurant_menu(arguments["restaurant_id"])
                
                menu_list = []
                for item in menu_items:
                    menu_list.append({
                        "id": item.id,
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category
                    })
                
                return {
                    "success": True,
                    "data": {
                        "id": restaurant.id,
                        "name": restaurant.name,
                        "location": restaurant.location,
                        "cuisine_type": restaurant.cuisine_type,
                        "avg_price": restaurant.avg_price,
                        "rating": float(restaurant.rating) if restaurant.rating else 0,
                        "opening_hours": restaurant.opening_hours,
                        "contact": restaurant.contact,
                        "description": restaurant.description,
                        "menu": menu_list
                    }
                }
            
            elif function_name == "add_to_favorites":
                favorite = db_ops.add_favorite(
                    arguments["user_id"],
                    arguments["restaurant_id"]
                )
                
                return {
                    "success": True,
                    "message": "Restoran berhasil ditambahkan ke favorit!"
                }
            
            elif function_name == "get_favorites":
                favorites = db_ops.get_user_favorites(arguments["user_id"])
                
                result = []
                for r in favorites:
                    result.append({
                        "id": r.id,
                        "name": r.name,
                        "location": r.location,
                        "cuisine_type": r.cuisine_type,
                        "avg_price": r.avg_price,
                        "rating": float(r.rating) if r.rating else 0
                    })
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Kamu punya {len(result)} restoran favorit"
                }
            
            elif function_name == "save_order":
                order = db_ops.add_order(
                    user_id=arguments["user_id"],
                    restaurant_id=arguments["restaurant_id"],
                    menu_items=arguments["menu_items"],
                    total_price=arguments["total_price"],
                    mood=arguments.get("mood")
                )
                
                return {
                    "success": True,
                    "data": {"order_id": order.id},
                    "message": "Pesanan berhasil disimpan!"
                }
            
            elif function_name == "get_order_history":
                orders = db_ops.get_user_orders(
                    arguments["user_id"],
                    limit=arguments.get("limit", 5)
                )
                
                result = []
                for order in orders:
                    result.append({
                        "id": order.id,
                        "restaurant_id": order.restaurant_id,
                        "menu_items": order.menu_items,
                        "total_price": order.total_price,
                        "order_date": order.order_date.isoformat(),
                        "mood": order.mood,
                        "rating": order.rating
                    })
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Riwayat {len(result)} pesanan terakhir"
                }
            
            elif function_name == "recommend_by_mood":
                restaurants = db_ops.get_recommendations_by_mood(
                    mood=arguments["mood"],
                    budget=arguments.get("budget"),
                    location=arguments.get("location")
                )
                
                result = []
                for r in restaurants:
                    result.append({
                        "id": r.id,
                        "name": r.name,
                        "location": r.location,
                        "cuisine_type": r.cuisine_type,
                        "avg_price": r.avg_price,
                        "rating": float(r.rating) if r.rating else 0,
                        "description": r.description
                    })
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Rekomendasi untuk mood {arguments['mood']}"
                }
            
            elif function_name == "update_user_preferences":
                user = db_ops.update_user_preferences(
                    user_id=arguments["user_id"],
                    budget=arguments.get("default_budget"),
                    location=arguments.get("default_location")
                )
                
                return {
                    "success": True,
                    "message": "Preferensi berhasil diupdate!"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown function: {function_name}"
                }
        
    except Exception as e:
        logger.error(f"Error executing tool {function_name}: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }