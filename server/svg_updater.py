import re
import textwrap
from lxml import etree

from io import BytesIO
from eink_image import Image_transform


class SVGFile:
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    def __init__(self, template_svg_filepath : str, output_filename: str):
        self.tree = etree.parse(template_svg_filepath)
        self.root = self.tree.getroot()
        self.output_filename = output_filename


    def update_svg(self, current_weather_dict, forecast_1_period_dict, forecast_period_2_dict, grocery_dict, calendar_dict):
        # Update the SVG file's text fields with new data
       
        all_supplied_dicts = [current_weather_dict, forecast_1_period_dict, forecast_period_2_dict, grocery_dict, calendar_dict]
        
        # print(all_supplied_dicts)

        actions_dict = {
            "grocery_list": self.handle_grocery,
            "calendar_events": self.handle_calendar,
            "forecast": self.handle_forecast,
            "uv_index": self.handle_uv_index,
            "temp_type": self.handle_temp_type,
            "weather_icon": self.handle_icon_code,
            "default_replace_text" : self.handle_text_element
        }
                
        # Iterate through every dictionary in our concatenated list of dictionaries
        for index, every_dict in enumerate(all_supplied_dicts) : 
            # In each dict, iterate through every key in the dictionary (these are items we want to replace)
            for key, value in every_dict.items():
                # If there is a special SVG replacement logic for the key value, look it up in our dictionary of actions
                trimmed_key = re.sub(r'(period0_|period1_|period2_)', '', key) # trim any prefix in the key
                action = actions_dict.get(trimmed_key, actions_dict["default_replace_text"])
                action(index, key, value) # run action on original key

        # Compile the new SVG file and output it
        self.tree.write(self.output_filename, encoding='utf-8', pretty_print=True)


    def send_to_pi(self):

        # initialize bytes output stream
        output_stream = BytesIO()

        transformed_svg = Image_transform(path_or_image=self.output_filename)
        transformed_svg.save(output_path_or_stream = output_stream)

        # display the image (don't cache it)
        # output.seek resets the pointer to the beginning of the file 
        output_stream.seek(0)

        return output_stream

    def find_svg_element_by_id(self, key):
        """
        Find an SVG text element by its ID attribute.

        Parameters:
        - key (str): The ID attribute of the desired text element.

        Returns:
        - Element: The found SVG text element. None if not found.
        """
        try:
            return self.root.find(f".//svg:text[@id='{key}']", namespaces=SVGFile.ns)
        except Exception as e:
            print(f"Error finding text element with key '{key}': {str(e)}")
            return None

    def find_single_shape(self, id: str):
        return self.root.find(f".//svg:*[@id='{id}']", namespaces=SVGFile.ns)

    def find_group_of_shapes(self, group_name):
        group = self.root.find(f".//svg:*[@id='{group_name}']", namespaces=SVGFile.ns)
        if group is not None:
            return [subgroup for subgroup in group.findall(".//svg:g", namespaces=SVGFile.ns)]
        return []

    def replace_text_with_proper_width(self, text_element, new_text, max_width, line_height_for_spacing, max_lines=5):
        # Split the new text into lines based on max_width
        splits = self.format_text_length(new_text, max_width, max_lines = max_lines)
        
        # Extract the transform attribute values
        matrix_values = text_element.attrib['transform'].split(' ')
        original_x = float(matrix_values[-2])
        start_y = float(matrix_values[-1].replace(')', ''))
        
        # Set spaces between lines
        line_height = line_height_for_spacing
        
        # Create new text elements for each line of text
        for index, line in enumerate(splits):
            new_text_element = etree.SubElement(self.root, "{http://www.w3.org/2000/svg}text")
            new_text_element.text = line
            new_y = start_y + (line_height * index)
            new_text_element.set('transform', f"matrix(1 0 0 1 {original_x} {new_y})")
            for attr, val in text_element.attrib.items():
                if attr != 'transform':
                    new_text_element.set(attr, val)
        
        # Remove the original text element from the SVG after creating the new ones
        text_element.getparent().remove(text_element)
    
    def convert_to_clean_bullet_points(self, text : list) -> str:
        # We are adding a non-breaking space to prevent lines splitting after the bullet point
        return "\n".join([f"•\u00A0{item.capitalize()}" for item in text])

    def extract_event_strings(self, events : list) -> str:
        return "\n".join([str(event) for event in events])

    
    def handle_text_element(self, index, key, value, convert_func = None, max_width = None, line_height_for_spacing = None, max_lines = None):
        # Find text element we want to replace in our SVG file
        text_element = self.find_svg_element_by_id(key)
        if text_element is not None:

            if convert_func == None:
                 text_element.text = str(value)
            else:
                new_text = convert_func(value)
                self.replace_text_with_proper_width(text_element = text_element, new_text = new_text, max_width = max_width, line_height_for_spacing = line_height_for_spacing, max_lines = max_lines)

    def handle_grocery(self, index, key, value):
        self.handle_text_element(index, key, value, self.convert_to_clean_bullet_points, max_width = 16, line_height_for_spacing = 25, max_lines = 12)

    def handle_calendar(self, index, key, value):
        self.handle_text_element(index, key, value, self.extract_event_strings,  max_width = 17, line_height_for_spacing = 25, max_lines = 12)

    def handle_forecast(self, index, key, value):
        self.handle_text_element(index, key, value, lambda x: x,  max_width = 26, line_height_for_spacing = 17, max_lines = 5)

    def handle_uv_index(self, index, key, value):
        # Find text element we want to replace in our SVG file
        text_element = self.find_svg_element_by_id(key)
        if text_element is not None:
            value = int(value)
            if value <=2 : 
                added_text = "(bas)"
            elif value <=5 :
                added_text = "(modéré)"
            elif value <=7 :
                added_text = "(élevé)"
            elif value <=10 :
                added_text = "(très élevé)"
            value = str(value)+" " + added_text
            text_element.text = str(value)


    def handle_temp_type(self, index, key, value):
        polygon_id_up, polygon_id_down = f"up_arrow_period{index}", f"down_arrow_period{index}"
        polygon_up = self.find_single_shape(polygon_id_up)
        polygon_down = self.find_single_shape(polygon_id_down)

        if value in ['high', 'low']:
            class_value_up, class_value_down = ("revealed", "hidden") if value == 'high' else ("hidden", "revealed")

            if polygon_up is not None:
                polygon_up.set('class', class_value_up)

            if polygon_down is not None:
                polygon_down.set('class', class_value_down)


    def handle_icon_code(self, index, key, value):
        icon_to_reveal = self.get_icon_name(value)
        id_of_icon = icon_to_reveal + str(index) if index > 0 else icon_to_reveal #main weather icons ids in the svg file have no suffix (no '..._1' or '..._2')
        list_of_shapes = self.find_group_of_shapes(group_name=key)
        for shape in list_of_shapes: 
            shape_id = shape.attrib.get("id")
            if shape_id == id_of_icon:
                shape.set('class', 'revealed')
            else:
                shape.set('class', 'hidden')
    
    def format_text_length(self, text_to_split, max_width, max_lines):
        return textwrap.fill(
            text=text_to_split,
            width=max_width,
            break_long_words=False,
            replace_whitespace=False,
            max_lines=max_lines,
            placeholder='...'
        ).split('\n')

    def get_icon_name(self, input_key: int) -> str:
        # Dictionary of equivalencies to convert Weather Canada's icon code to our custom icon set
        equivalency_dict = {
            0: "wi-day-sunny",
            1: "wi-day-sunny-overcast",
            2: "wi-day-cloudy",
            3: "wi-cloud",
            4: "wi-cloudy",
            5: "wi-day-cloudy-windy",
            6: "wi-day-showers",
            7: "wi-day-sprinkle",
            8: "wi-day-snow",
            9: "wi-day-thunderstorm",
            10: "wi-cloudy",
            11: "wi-rain-wind",
            12: "wi-showers",
            13: "wi-rain",
            14: "wi-raindrops",
            15: "wi-rain-mix",
            16: "wi-snow",
            17: "wi-snow-wind",
            18: "wi-sandstorm",
            19: "wi-storm-showers",
            22: "wi-day-cloudy",
            23: "wi-smog",
            24: "wi-fog",
            25: "wi-sandstorm",
            26: "wi-snowflake-cold",
            27: "wi-dust",
            28: "wi-rain-mix",
            30: "wi-night-clear",
            31: "wi-night-alt-cloudy",
            32: "wi-night-alt-cloudy",
            33: "wi-night-cloudy",
            34: "wi-night-alt-cloudy-windy",
            35: "wi-night-cloudy-windy",
            36: "wi-night-alt-showers",
            37: "wi-night-alt-rain-mix",
            38: "wi-night-snow-wind",
            39: "wi-night-alt-thunderstorm",
            40: "wi-night-snow-wind",
            41: "wi-sprinkle",
            42: "wi-tornado",
            43: "wi-strong-wind",
            44: "wi-smoke",
            45: "wi-sandstorm",
            46: "wi-storm-showers",
            47: "wi-lightning",
            48: "wi-raindrops"
        }

        return equivalency_dict.get(input_key)