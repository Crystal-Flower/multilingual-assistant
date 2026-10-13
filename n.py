import requests
import os


def generate_osm_map_with_route(
        filename="osm_map_route.png",
        width=640,
        height=440,
        map_center="13.2384, 79.9142",
        zoom=16
):
    """
    Generates a map image using a free, OpenStreetMap-based static map service.
    The coordinates are for the Amrita Vishwa Vidyapeetham, Chennai Campus.

    Args:
        filename (str): The name of the output PNG file.
        width (int): The width of the image in pixels.
        height (int): The height of the image in pixels.
        map_center (str): The latitude and longitude of the map's center.
        zoom (int): The zoom level of the map.
    """
    # Define some sample locations for buildings at Amrita Chennai campus
    buildings = {
        "Main Entrance": (13.2393, 79.9140),
        "Admin Block": (13.2386, 79.9148),
        "Academic Block": (13.2380, 79.9135),
        "Boys Hostel": (13.2375, 79.9150),
        "Girls Hostel": (13.2390, 79.9155)
    }

    # Define start and end points for the route
    start_point_name = "Boys Hostel"
    end_point_name = "Academic Block"
    start_point_coords = buildings[start_point_name]
    end_point_coords = buildings[end_point_name]

    # Create a list of markers for all buildings
    # The API documentation specifies a format for point markers.
    markers = []
    for name, coords in buildings.items():
        # Set a different color for the start and end markers using hex codes
        # Yandex Maps API uses the format `lon,lat,marker_style`
        marker_style = "pm2rdl" if name in [start_point_name, end_point_name] else "pm2bl"
        markers.append(f"{coords[1]},{coords[0]},{marker_style}")

    # Create a path string for the route in the format: lon1,lat1,lon2,lat2
    # The path will be a straight line between the two points.
    path_string = f"{start_point_coords[1]},{start_point_coords[0]},{end_point_coords[1]},{end_point_coords[0]}"

    # The chosen service's URL structure (Yandex Maps)
    base_url = "https://static-maps.yandex.ru/1.x/"

    # Extract lon,lat for map center as a tuple
    center_coords_lon_lat = tuple(map(float, map_center.split(',')[::-1]))

    params = {
        "l": "map",  # Map layer: "map" for scheme, "sat" for satellite
        "size": f"{width},{height}",
        "ll": f"{center_coords_lon_lat[0]},{center_coords_lon_lat[1]}",
        "z": zoom,
        "pt": "~".join(markers),
        "pl": f"c:ff0000,w:5,{path_string}"
    }

    print("Fetching map from free static map service...")

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        if 'image' in response.headers.get('Content-Type', ''):
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Map with route saved to '{os.path.abspath(filename)}'")
        else:
            print("Failed to download map image. Check the URL and parameters.")
            print(f"Response content: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    generate_osm_map_with_route()
