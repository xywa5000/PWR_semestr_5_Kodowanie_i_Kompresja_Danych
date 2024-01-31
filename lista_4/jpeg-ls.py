import sys
from math import log2
from typing import List

TGA_IMAGE_FOOTER: int = 26

class ColorPixel:
    def __init__(self, red: int, green: int, blue: int):
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self):
        return f"(red {self.red}, green {self.green}, blue {self.blue})"

class ImageAnalysis:
    def __init__(self, width: int, height: int):
        self.width = width
        self.pixel_matrix = [[ColorPixel(0, 0, 0) for _ in range(height)] for _ in range(width)]
        self.rgb_matrix = [[0] * 256 for _ in range(3)]
        self.rgb_counts = [0] * 3
        self.significant_counts = [0] * 256
        self.index_x = 0
        self.index_y = 0

    def clear_data(self):
        self.rgb_matrix = [[0] * 256 for _ in range(3)]
        self.rgb_counts = [0] * 3
        self.significant_counts = [0] * 256

    def add_pixel(self, red: int, green: int, blue: int):
        x = self.index_x % self.width
        self.pixel_matrix[x][self.index_y] = ColorPixel(red, green, blue)
        if self.index_x == self.width - 1:
            self.index_y += 1
        self.index_x = x + 1

    def get_adjacent_pixel(self, i: int, j: int):
        return self.pixel_matrix[i][j] if 0 <= i < len(self.pixel_matrix) and 0 <= j < len(self.pixel_matrix[0]) else ColorPixel(0, 0, 0)

    def increase_rgb_counts(self, red: int, green: int, blue: int):
        self.rgb_counts[0] += 1
        self.rgb_matrix[0][red] += 1
        self.rgb_counts[1] += 1
        self.rgb_matrix[1][green] += 1
        self.rgb_counts[2] += 1
        self.rgb_matrix[2][blue] += 1

    def increase_significant_counts(self, red: int, green: int, blue: int):
        self.significant_counts[red] += 1
        self.significant_counts[green] += 1
        self.significant_counts[blue] += 1

    def get_total_significant_counts(self) -> int:
        return sum(self.rgb_counts)

class DataCollector:
    def __init__(self, byte_array):
        self.byte_array = byte_array
        self.offset = 0

    def read_byte(self) -> int:
        data = self.byte_array[self.offset]
        self.offset += 1
        return data

def read_bytes_from_file(filename: str):
    with open(filename, "rb") as file:
        return bytearray(file.read())

def compute_entropy(frequency, size):
    return -sum((v / size) * (log2(v) - log2(size)) for v in frequency if v > 0)

def create_predicates():
    return [
        lambda x, y, z: x,
        lambda x, y, z: y,
        lambda x, y, z: z,
        lambda x, y, z: x + y - z,
        lambda x, y, z: x + (y - z) / 2,
        lambda x, y, z: y + (x - z) / 2,
        lambda x, y, z: (x + y) / 2,
        lambda x, y, z: new_standard(x, y, z)
    ]

def new_standard(x, y, z):
    maximum = max(y, z)
    return maximum if x > maximum else min(y, z) if x <= min(y, z) else z + y - x

def mod_256(x: int):
    value: int = x % 256
    return value & 0xFF if value < 0 else value

def analyze_image(image_analysis: ImageAnalysis):
    predicates = create_predicates()
    best_entropy = [sys.maxsize] * 4
    best_func = [sys.maxsize] * 4

    for i, predicate in enumerate(predicates):
        image_analysis.clear_data()
        for j, row in enumerate(image_analysis.pixel_matrix):
            for k, pixel in enumerate(row):
                current_pixel = pixel
                adjacent_pixel_a = image_analysis.get_adjacent_pixel(j, k - 1)
                adjacent_pixel_b = image_analysis.get_adjacent_pixel(j - 1, k)
                adjacent_pixel_c = image_analysis.get_adjacent_pixel(j - 1, k - 1)

                predicted_red = mod_256(current_pixel.red - int(predicate(adjacent_pixel_c.red, adjacent_pixel_b.red, adjacent_pixel_a.red)))
                predicted_green = mod_256(current_pixel.green - int(predicate(adjacent_pixel_c.green, adjacent_pixel_b.green, adjacent_pixel_a.green)))
                predicted_blue = mod_256(current_pixel.blue - int(predicate(adjacent_pixel_c.blue, adjacent_pixel_b.blue, adjacent_pixel_a.blue)))

                image_analysis.increase_rgb_counts(predicted_red, predicted_green, predicted_blue)
                image_analysis.increase_significant_counts(predicted_red, predicted_green, predicted_blue)

        current_entropy = [
            compute_entropy(image_analysis.rgb_matrix[0], image_analysis.rgb_counts[0]),  # Red
            compute_entropy(image_analysis.rgb_matrix[1], image_analysis.rgb_counts[1]),  # Green
            compute_entropy(image_analysis.rgb_matrix[2], image_analysis.rgb_counts[2]),  # Blue
            compute_entropy(image_analysis.significant_counts, image_analysis.get_total_significant_counts())
        ]

        print(f"{i}: total: {current_entropy[3]}")
        print(f"{i}: red  : {current_entropy[0]}")
        print(f"{i}: green: {current_entropy[1]}")
        print(f"{i}: blue : {current_entropy[2]}")

        for j in range(len(best_entropy)):
            if current_entropy[j] < best_entropy[j]:
                best_entropy[j] = current_entropy[j]
                best_func[j] = i
    print("")

    print_final_results(best_entropy, best_func)

def update_best_results(func_idx: int, current_entropy: List, best_entropy: List, best_func):
    for i in range(len(best_entropy)):
        if current_entropy[i] < best_entropy[i]:
            best_entropy[i] = current_entropy[i]
            best_func[i] = func_idx

def show_data_analysis(image_analysis: ImageAnalysis):
    print("File stats:")
    print("File entropy : ", compute_entropy(image_analysis.significant_counts, image_analysis.get_total_significant_counts()))
    print("Red entropy : ", compute_entropy(image_analysis.rgb_matrix[0], image_analysis.rgb_counts[0]))
    print("Green entropy : ", compute_entropy(image_analysis.rgb_matrix[1], image_analysis.rgb_counts[1]))
    print("Blue entropy : ", compute_entropy(image_analysis.rgb_matrix[2], image_analysis.rgb_counts[2]))
    print("")

def print_final_results(best_results: List, best_func: List):
    print("Function numbering is as follows:")
    print("0. A\n1. B\n2. C\n3. A+B-C\n4. A+(B-C)/2\n5. B+(A-C)/2\n6. (A+B)/2\n7. New standard\n")
    print("Best file  [", best_func[3], "] : ", best_results[3])
    print("Best red   [", best_func[0], "] : ", best_results[0])
    print("Best green [", best_func[1], "] : ", best_results[1])
    print("Best blue  [", best_func[2], "] : ", best_results[2])

def main_function(file_name: str):
    data_collector = DataCollector(read_bytes_from_file(file_name))
    for _ in range(12):
        data_collector.read_byte()

    width = data_collector.read_byte() + (data_collector.read_byte() << 8)
    height = data_collector.read_byte() + (data_collector.read_byte() << 8)
    data_collector.read_byte()
    data_collector.read_byte()

    image_analysis = ImageAnalysis(width, height)
    image_size: int = width * height - TGA_IMAGE_FOOTER
    if image_size < 0:
        raise ValueError('Error: image_size < 0!')

    is_uncompressed = data_collector.byte_array[2] == 0x02
    if is_uncompressed and data_collector.byte_array[16] == 0x20:
        raise ValueError('Error: RGBA not RGB!')
    elif is_uncompressed and data_collector.byte_array[16] == 0x18:
        for _ in range(image_size):
            blue = int(data_collector.read_byte())
            green = int(data_collector.read_byte())
            red = int(data_collector.read_byte())
            image_analysis.add_pixel(red, green, blue)
            image_analysis.increase_rgb_counts(red, green, blue)
            image_analysis.increase_significant_counts(red, green, blue)
    else:
        raise ValueError('Error: already compressed!')

    show_data_analysis(image_analysis)
    analyze_image(image_analysis)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Error: wrong args! Usage: python jpeg-ls.py <tga_file>")
        sys.exit(1)
    main_function(sys.argv[1])
