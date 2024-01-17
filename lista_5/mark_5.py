import sys
import math
from typing import List

TGA_IMAGE_HEADER_SIZE = 18
TGA_IMAGE_FOOTER_SIZE = 25

class Pixel:
    def __init__(self, blue: float, green: float, red: float):
        self.blue = blue
        self.green = green
        self.red = red

    @staticmethod
    def create_pixel_array(size: int, buffer: bytes) -> List:
        # Tworzy tablicę obiektów Pixel z surowego bufora bajtów obrazu TGA
        return [Pixel(buffer[i * 3], buffer[i * 3 + 1], buffer[i * 3 + 2]) for i in range(size)]

    def distance_to(self, other: 'Pixel') -> float:
        # Oblicza kwadrat odległości euklidesowej pomiędzy dwoma pikselami
        return math.pow(self.blue - other.blue, 2) + math.pow(self.green - other.green, 2) + math.pow(
            self.red - other.red, 2)

    def scaled_vector(self, epsilon: float) -> 'Pixel':
        # Zwraca nowy piksel, w którym każda składowa jest przeskalowana o wartość epsilon
        return Pixel(self.blue * epsilon, self.green * epsilon, self.red * epsilon)

    def floor_values(self) -> 'Pixel':
        # Zaokrągla wartości składowych piksela do najbliższej mniejszej liczby całkowitej
        self.blue = math.floor(self.blue)
        self.green = math.floor(self.green)
        self.red = math.floor(self.red)
        return self

    def squared_length(self):
        # Zwraca kwadrat długości wektora reprezentowanego przez piksel
        return math.pow(self.blue, 2) + math.pow(self.green, 2) + math.pow(self.red, 2)

class CodeWord:
    def __init__(self, pixel: Pixel):
        self.members: List[Pixel] = []
        self.word: Pixel = pixel

    def clear_members(self):
        # Czyści listę członków klastra (pikseli przypisanych do kodu koloru)
        self.members = []

    def add_pixel(self, pixel: Pixel):
        # Dodaje nowy piksel do klastra
        self.members.append(pixel)

    def update_word(self, new_state: Pixel):
        # Aktualizuje reprezentanta klastra
        self.word = new_state

    def __str__(self) -> str:
        # Tekstowa reprezentacja obiektu CodeWord
        return f"[({self.word.blue},{self.word.green},{self.word.red})]  -> {len(self.members)}"

class Vectorization:
    def __init__(self):
        self.code_words: List[CodeWord] = []
        self.epsilon: float = 0.00_001
        self.pixels: List[Pixel] = []

    def create_codebook(self, pixels: List, size_codebook: int):
        # Tworzy słownik (codebook) algorytmem LBG i zwraca go
        code_word = CodeWord(self.get_middle_vector(pixels))
        self.code_words.append(code_word)
        self.pixels = pixels
        avg_dist = Vectorization.get_avg_distance(code_word, pixels)

        while len(self.code_words) < size_codebook:
            self.enlarge_collection()
            avg_dist = self.LBG_algorithm(avg_dist)

        return self.code_words

    def enlarge_collection(self):
        # Powiększa słownik poprzez dodanie dwóch nowych kodów koloru dla każdego istniejącego
        new_code_words: List[CodeWord] = []
        for cw in self.code_words:
            word1 = CodeWord(cw.word.scaled_vector(1 + self.epsilon))
            new_code_words.append(word1)
            word2 = CodeWord(cw.word.scaled_vector(1 - self.epsilon))
            new_code_words.append(word2)
        self.code_words = new_code_words

    def LBG_algorithm(self, init_avg_distance: float) -> float:
        # Implementacja algorytmu LBG do optymalizacji słownika
        avg_distance = 0.0
        err = 1.0 + self.epsilon

        while err > self.epsilon:
            for cw in self.code_words: cw.clear_members()
            self.clusterization()
            self.generate_centroid()
            before_distance = avg_distance if avg_distance > 0 else init_avg_distance
            avg_distance = self.quantization_error()
            err = (before_distance - avg_distance) / before_distance
        return avg_distance

    def clusterization(self):
        # Przypisuje każdy piksel do najbliższego klastra (kodu koloru) w słowniku
        reset = math.pow(2, 24)
        for pixel in self.pixels:
            shortest = reset
            idx = 0
            for i, cw in enumerate(self.code_words):
                distance = pixel.distance_to(cw.word)
                if distance < shortest:
                    shortest = distance
                    idx = i
            self.code_words[idx].add_pixel(pixel)

    def generate_centroid(self):
        # Aktualizuje reprezentantów klastrów (kodów koloru) na podstawie przypisanych do nich pikseli
        for cw in self.code_words:
            if len(cw.members) > 0:
                new_word = self.get_middle_vector(cw.members)
                cw.update_word(new_word)

    @staticmethod
    def get_middle_vector(pixels: List[Pixel]) -> Pixel:
        # Oblicza wektor średni z zestawu pikseli
        size = len(pixels)
        colors = [sum(p.blue for p in pixels), sum(p.green for p in pixels), sum(p.red for p in pixels)]
        return Pixel(colors[0] / size, colors[1] / size, colors[2] / size)

    @staticmethod
    def get_avg_distance(code_word: CodeWord, pixels: List[Pixel]) -> float:
        # Oblicza średnią odległość od reprezentanta klastra do pikseli w zbiorze
        total_distance = sum(p.distance_to(code_word.word) for p in pixels)
        return total_distance / len(pixels)

    def quantization_error(self) -> float:
        # Oblicza błąd kwantyzacji na podstawie odległości między pikselami a ich reprezentantami klastrów
        total_error = sum(sum(cw.word.distance_to(pixel) for pixel in cw.members) / len(self.pixels) for cw in self.code_words)
        return total_error

def quantize(pixel_arr: List[Pixel], code_words: List[CodeWord]) -> List[Pixel]:
    # Kwadruje wartości składowych piksela dla każdego reprezentanta klastra
    new_bitmap = [cw.word.floor_values() for cw in code_words]

    for pixel in pixel_arr:
        distances = [pixel.distance_to(cw.word) for cw in code_words]
        new_bitmap.append(code_words[distances.index(min(distances))].word)

    return new_bitmap

def pixels_to_bytes(pixel_arr: List[Pixel]):
    # Konwertuje listę pikseli na sekwencję bajtów (TGA)
    payload = [int(p.blue) for p in pixel_arr] + [int(p.green) for p in pixel_arr] + [int(p.red) for p in pixel_arr]
    return bytes(payload)

def mse_rate(pixel_arr: List[Pixel], new_arr: List[Pixel]) -> float:
    # Oblicza błąd średniokwadratowy (MSE) między dwoma zestawami pikseli
    return (1 / len(pixel_arr)) * sum((pixel_arr[i].distance_to(new_arr[i])) ** 2 for i in range(len(pixel_arr)))

def snr_rate(pixel_arr: List[Pixel], ms_rate: float) -> float:
    # Oblicza stosunek sygnał-szum (SNR) na podstawie oryginalnych pikseli i błędu średniokwadratowego
    return (1 / len(pixel_arr)) * sum(pixel_arr[i].squared_length() for i in range(len(pixel_arr))) / ms_rate

def get_tga_image_width(buffer: bytes) -> int:
    # Odczytuje szerokość obrazu TGA z nagłówka
    return buffer[12] + (buffer[13] << 8)

def get_tga_image_height(buffer: bytes) -> int:
    # Odczytuje wysokość obrazu TGA z nagłówka
    return buffer[14] + (buffer[15] << 8)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise ValueError('Args Error! Usage: python lista5.py <input.tga> <output.tga> <num>')
    with open(sys.argv[1], 'rb') as f:
        tga_buffer_image: bytes = f.read()
        tga_header = tga_buffer_image[:TGA_IMAGE_HEADER_SIZE]
        tga_footer = tga_buffer_image[-TGA_IMAGE_FOOTER_SIZE:]
        tga_width: int = get_tga_image_width(tga_buffer_image)
        tga_height: int = get_tga_image_height(tga_buffer_image)

        pixel_arr = Pixel.create_pixel_array(tga_width * tga_height,
                                             tga_buffer_image[TGA_IMAGE_HEADER_SIZE:len(tga_buffer_image) - TGA_IMAGE_FOOTER_SIZE])

        code_words: List[CodeWord] = Vectorization().create_codebook(pixel_arr, 2 ** int(sys.argv[3]))
        new_pixel_arr = quantize(pixel_arr, code_words)
        pixels_as_byte = pixels_to_bytes(new_pixel_arr)

        mse = mse_rate(pixel_arr, new_pixel_arr)
        snratio = snr_rate(pixel_arr, mse)
        print("MSE:", mse)
        print("SNR:", snratio)

        with open(sys.argv[2], "wb") as output:
            quantized = tga_header + pixels_as_byte + tga_footer
            output.write(quantized)
