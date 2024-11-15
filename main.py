import json
import requests
import folium
import os
from dotenv import load_dotenv
from flask import Flask
from geopy import distance


def load_coffee_data(filename="coffee.json"):
    with open(filename, "r", encoding="CP1251") as file:
        file_content = file.read()
    coffee_data = json.loads(file_content)
    return coffee_data


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_user_location(apikey):
    address = input('Где вы находитесь?: ')
    return fetch_coordinates(apikey, address)


def calculate_distances(coffee_data, user_location):
    nearby_coffee_shops = []
    for coffee_shop in coffee_data:
        coordinates = coffee_shop['geoData']['coordinates']
        coffee_info = {
            'name': coffee_shop['Name'],
            'latitude': coordinates[1],
            'longitude': coordinates[0],
            'distance': distance.distance(user_location, (coordinates[0], coordinates[1])).km
        }
        nearby_coffee_shops.append(coffee_info)
    return nearby_coffee_shops


def get_distance(coffee_shop):
    return coffee_shop['distance']


def find_nearest_coffee_shops(coffee_shops, count=5):
    return sorted(coffee_shops, key=get_distance)[:count]


def create_coffee_map(nearest_coffee_shops, user_location, map_filename="index.html"):
    latitude, longitude = user_location
    m = folium.Map(location=[longitude, latitude], zoom_start=15)
    # Метка пользователя
    folium.Marker(
        location=[longitude, latitude],
        tooltip='Вы здесь',
        popup=f'{latitude} {longitude}',
        icon=folium.Icon(color="red"),
    ).add_to(m)
    # Метки кафе
    for coffee_shop in nearest_coffee_shops:
        folium.Marker(
            location=[coffee_shop['latitude'], coffee_shop['longitude']],
            tooltip=coffee_shop['name'],
            popup=f"{coffee_shop['name']} — {round(coffee_shop['distance'], 2)} км",
            icon=folium.Icon(color="blue"),
        ).add_to(m)
    m.save(map_filename)


def start_flask_service():
    app = Flask(__name__)

    @app.route('/')
    def display_coffee_map():
        with open('index.html', encoding='utf-8') as file:
            return file.read()

    app.run('0.0.0.0')


def main():
    load_dotenv()
    apikey = os.getenv("API_KEY")
    coffee_data = load_coffee_data()
    user_location = get_user_location(apikey)
    coffee_shops_with_distances = calculate_distances(coffee_data, user_location)
    nearest_coffee_shops = find_nearest_coffee_shops(coffee_shops_with_distances)
    create_coffee_map(nearest_coffee_shops, user_location)
    start_flask_service()


if __name__ == '__main__':
    main()
