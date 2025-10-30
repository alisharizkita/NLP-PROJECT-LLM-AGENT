from typing import Dict, List, Any
import requests
from src.config import Config
import logging
import os
import json

logger = logging.getLogger(__name__)

def get_tools_definition() -> List[Dict]:
    """
    Get tool definitions for function calling
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Dapatkan informasi cuaca saat ini untuk lokasi tertentu. Gunakan ini untuk memberikan rekomendasi makanan yang sesuai dengan cuaca.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Nama kota (contoh: Jakarta, Bandung, Surabaya)"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_calories",
                "description": "Hitung estimasi kalori untuk makanan tertentu",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "food_name": {
                            "type": "string",
                            "description": "Nama makanan (contoh: nasi goreng, ayam bakar)"
                        },
                        "portion": {
                            "type": "string",
                            "description": "Ukuran porsi (small/medium/large)",
                            "enum": ["small", "medium", "large"]
                        }
                    },
                    "required": ["food_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_meal_time_recommendation",
                "description": "Dapatkan rekomendasi makanan berdasarkan waktu (pagi/siang/malam)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_of_day": {
                            "type": "string",
                            "description": "Waktu makan",
                            "enum": ["breakfast", "lunch", "dinner", "snack"]
                        },
                        "mood": {
                            "type": "string",
                            "description": "Mood user (opsional)",
                            "enum": ["happy", "sad", "stressed", "energetic", "relaxed", "hungry"]
                        }
                    },
                    "required": ["time_of_day"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_nearby_restaurants",
                "description": "Mencari restoran valid di sekitar lokasi menggunakan Google Maps Places API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Nama kota atau daerah untuk pencarian restoran."
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Radius pencarian dalam meter (default 3000)."
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Kata kunci spesifik seperti 'sushi', 'cafe', dll (opsional)."
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    return tools


def execute_tool(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tool/function and return result
    """
    try:
        logger.info(f"Executing tool: {function_name} with args: {arguments}")
        
        if function_name == "get_weather":
            return get_weather(arguments.get("location", Config.DEFAULT_LOCATION))
        
        elif function_name == "calculate_calories":
            return calculate_calories(
                arguments.get("food_name"),
                arguments.get("portion", "medium")
            )
        
        elif function_name == "get_meal_time_recommendation":
            return get_meal_time_recommendation(
                arguments.get("time_of_day"),
                arguments.get("mood")
            )

        elif function_name == "search_nearby_restaurants":
            return search_nearby_restaurants(
                arguments.get("location"),
                arguments.get("radius", 3000),
                arguments.get("keyword")
            )
        
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


def get_weather(location: str) -> Dict[str, Any]:
    """
    Get weather information from OpenWeatherMap API
    """
    api_key = Config.WEATHER_API_KEY or os.getenv("OPENWEATHER_API_KEY")
    api_url = Config.WEATHER_API_URL or "https://api.openweathermap.org/data/2.5/weather"

    if not api_key:
        logger.error("Weather API key not found.")
        return {
            "success": False,
            "message": "Weather API key tidak ditemukan. Cek konfigurasi environment variable."
        }
    
    try:
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric",
            "lang": "id"
        }

        logger.info(f"Fetching weather data for {location}...")
        response = requests.get(api_url, params=params, timeout=8)

        if response.status_code != 200:
            logger.warning(f"Weather API response {response.status_code}: {response.text}")
            return {
                "success": False,
                "message": f"Gagal mengambil data cuaca untuk {location}. Status: {response.status_code}"
            }

        data = response.json()
        if "weather" not in data or "main" not in data:
            return {
                "success": False,
                "message": "Respons dari API tidak lengkap."
            }

        weather_info = {
            "success": True,
            "location": data.get("name", location),
            "temperature": round(data["main"].get("temp", 0)),
            "feels_like": round(data["main"].get("feels_like", 0)),
            "humidity": data["main"].get("humidity", 0),
            "description": data["weather"][0].get("description", "tidak diketahui"),
            "main": data["weather"][0].get("main", "").lower(),
            "icon": data["weather"][0].get("icon", "")
        }

        # Food context
        condition = weather_info["main"]
        temp = weather_info["temperature"]

        if "rain" in condition or "drizzle" in condition:
            weather_info["food_context"] = "hujan - cocok untuk makanan hangat berkuah"
        elif temp > 30:
            weather_info["food_context"] = "panas - cocok untuk makanan segar dan dingin"
        elif temp < 20:
            weather_info["food_context"] = "dingin - cocok untuk makanan hangat"
        else:
            weather_info["food_context"] = "cuaca nyaman - bebas pilih makanan apapun"

        logger.info(f"Weather fetched: {weather_info['description']} ({temp}°C)")
        return weather_info

    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        return {
            "success": False,
            "message": f"Gagal mengambil data cuaca untuk {location}: {str(e)}"
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_weather: {e}")
        return {
            "success": False,
            "message": f"Terjadi kesalahan internal saat memproses cuaca untuk {location}"
        }



def calculate_calories(food_name: str, portion: str = "medium") -> Dict[str, Any]:
    """
    Calculate estimated calories for food (mock data)
    """
    try:
        calorie_database = {
            "nasi goreng": 450,
            "nasi putih": 200,
            "mie goreng": 400,
            "ayam goreng": 300,
            "ayam bakar": 250,
            "sate ayam": 200,
            "bakso": 350,
            "soto": 300,
            "gado-gado": 280,
            "rendang": 400,
            "pizza": 600,
            "burger": 550,
            "sushi": 300,
            "ramen": 450,
            "pasta": 500,
            "salad": 150,
        }
        
        multipliers = {"small": 0.7, "medium": 1.0, "large": 1.4}
        
        if not food_name:
            return {"success": False, "message": "Nama makanan tidak boleh kosong"}
        
        if portion not in multipliers:
            portion = "medium"
        
        food_lower = str(food_name).lower()
        base_calories, matched_food = None, None
        
        for food, cal in calorie_database.items():
            if food in food_lower or food_lower in food:
                base_calories, matched_food = cal, food
                break
        
        if base_calories is None:
            if any(word in food_lower for word in ["nasi", "rice"]):
                base_calories = 400
                matched_food = food_name
            elif any(word in food_lower for word in ["mie", "noodle", "pasta"]):
                base_calories = 450
                matched_food = food_name
            elif any(word in food_lower for word in ["ayam", "chicken"]):
                base_calories = 280
                matched_food = food_name
            else:
                return {"success": False, "message": f"Data kalori '{food_name}' tidak tersedia."}
        
        final_calories = int(base_calories * multipliers.get(portion, 1.0))
        
        return {
            "success": True,
            "food": matched_food,
            "portion": portion,
            "calories": final_calories,
            "protein_estimate": int(final_calories * 0.15 / 4),
            "carbs_estimate": int(final_calories * 0.50 / 4),
            "fat_estimate": int(final_calories * 0.35 / 9)
        }
    except Exception as e:
        logger.error(f"Error in calculate_calories: {e}")
        return {"success": False, "message": f"Error menghitung kalori: {str(e)}"}


def get_meal_time_recommendation(time_of_day: str, mood: str = None) -> Dict[str, Any]:
    """
    Get meal recommendations based on time and mood
    """
    recommendations = {
        "breakfast": {"default": ["Bubur ayam", "Roti bakar", "Nasi goreng"], "energetic": ["Smoothie bowl", "Granola"]},
        "lunch": {"default": ["Nasi padang", "Soto ayam", "Bakso"], "happy": ["Pizza", "Burger"]},
        "dinner": {"default": ["Ayam bakar", "Sate ayam"], "sad": ["Mie kuah", "Soto"]},
        "snack": {"default": ["Pisang goreng", "Martabak mini"], "stressed": ["Coklat hangat", "Ice cream"]}
    }
    
    time_recs = recommendations.get(time_of_day, recommendations["lunch"])
    foods = time_recs.get(mood, time_recs["default"])
    
    return {"success": True, "time_of_day": time_of_day, "mood": mood or "default", "recommendations": foods}


def search_nearby_restaurants(location: str, radius: int = 3000, keyword: str = None):
    """
    Cari restoran terdekat berdasarkan lokasi menggunakan Google Maps Places API.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "API key Google Maps tidak ditemukan."}

    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
    geo_resp = requests.get(geocode_url)
    if geo_resp.status_code != 200:
        return {"error": "Gagal mendapatkan koordinat lokasi."}
    geo_data = geo_resp.json()

    if not geo_data["results"]:
        return {"error": f"Lokasi '{location}' tidak ditemukan di Google Maps."}

    lat = geo_data["results"][0]["geometry"]["location"]["lat"]
    lng = geo_data["results"][0]["geometry"]["location"]["lng"]

    places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}&type=restaurant&key={api_key}"
    )
    if keyword:
        places_url += f"&keyword={keyword}"

    resp = requests.get(places_url)
    if resp.status_code != 200:
        return {"error": "Gagal mengambil data restoran dari Google Maps."}

    places_data = resp.json()
    if not places_data.get("results"):
        return {"error": f"Tidak ada restoran ditemukan di sekitar {location}."}

    results = []
    for r in places_data["results"][:3]:
        place = {
            "name": r.get("name"),
            "address": r.get("vicinity"),
            "rating": r.get("rating", "N/A"),
            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{r.get('place_id')}"
        }
        results.append(place)

    return {"location": location, "total_found": len(places_data["results"]), "top_recommendations": results}
