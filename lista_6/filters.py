import sys
import math

class Gamma:
    def encode(self, number):
        # Unary encoding
        code = bin(number)[2:]
        code = "0" * (len(code) - 1) + code
        return code

    def decode(self, code):
        # Unary decoding
        codes = []
        counter = 0
        idx = 0
        while idx < len(code):
            if code[idx] == "0":
                counter += 1
                idx += 1
            else:
                codes.append(int(code[idx: idx + counter + 1], base=2))
                idx += counter + 1
                counter = 0
        return codes


class Pixel:
    def __init__(self, red, green, blue):
        # Pixel class to represent RGB values
        self.red = red
        self.green = green
        self.blue = blue

    def __add__(self, other):
        # Addition of pixels
        return Pixel(self.red + other.red, self.green + other.green, self.blue + other.blue)

    def __sub__(self, other):
        # Subtraction of pixels
        return Pixel(self.red - other.red, self.green - other.green, self.blue - other.blue)

    def __mul__(self, number):
        # Multiplication of pixel by a scalar
        return Pixel(self.red * number, self.green * number, self.blue * number)

    def __truediv__(self, number):
        # True division of pixel by a scalar
        return Pixel(self.red / number, self.green / number, self.blue / number)

    def __floordiv__(self, number):
        # Floor division of pixel by a scalar
        return Pixel(self.red // number, self.green // number, self.blue // number)

    def __mod__(self, number):
        # Modulo operation for pixel values
        return Pixel(self.red % number, self.green % number, self.blue % number)

    def uniform_quantization(self, step):
        # Uniform quantization of pixel values
        r = int(self.red // step * step)
        g = int(self.green // step * step)
        b = int(self.blue // step * step)
        return Pixel(r, g, b)


class Bitmap:
    def __init__(self, bitmap, width, height):
        # Bitmap class to represent an image
        self.width = width
        self.height = height

        result = []
        row = []
        for i in range(width * height):
            row.append(
                Pixel(
                    blue=bitmap[i * 3],
                    green=bitmap[i * 3 + 1],
                    red=bitmap[i * 3 + 2]
                )
            )

            if width == len(row):
                result.insert(0, row)
                row = []
        self.bitmap = result

    def __getitem__(self, pos):
        # Get item from bitmap with boundary checking
        x, y = pos
        ret_x, ret_y = x, y
        if x < 0:
            ret_x = 0
        elif x >= self.width:
            ret_x = self.width - 1

        if y < 0:
            ret_y = 0
        elif y >= self.height:
            ret_y = self.height - 1

        return self.bitmap[ret_y][ret_x]


def parse_bitmap(bitmap, width, height):
    # Parse bitmap data into a 2D array of Pixel objects
    result = []
    row = []
    for i in range(width * height):
        row.append(
            Pixel(
                blue=bitmap[i * 3],
                green=bitmap[i * 3 + 1],
                red=bitmap[i * 3 + 2]
            )
        )

        if width == len(row):
            result.insert(0, row)
            row = []
    return result


def apply_filter(bitmap, x, y, high_pass=False):
    # Apply convolution filter to a pixel in the bitmap
    weights_low_pass = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    weights_high_pass = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]

    weights = weights_high_pass if high_pass else weights_low_pass

    pix = Pixel(0, 0, 0)
    for i in range(-1, 2):
        for j in range(-1, 2):
            pix += bitmap[x + i, y + j] * weights[i + 1][j + 1]

    weights_sum = sum([sum(row) for row in weights])

    if weights_sum <= 0:
        weights_sum = 1

    pix = pix // weights_sum

    # Clip pixel values to the valid range [0, 255]
    pix.red = max(0, min(255, pix.red))
    pix.green = max(0, min(255, pix.green))
    pix.blue = max(0, min(255, pix.blue))

    return pix


def bitmap_to_array(bitmap):
    #Convert bitmap data to an array for TGA file
    payload = []
    for pixel in bitmap:
        payload += [pixel.blue, pixel.green, pixel.red]
    return payload


def bitmap_to_bytes(bitmap):
    # Convert bitmap data to bytes
    payload = []
    for pixel in bitmap:
        payload += [pixel.blue, pixel.green, pixel.red]
    return bytes(payload)


def differential_coding(bitmap):
    # Różnicowe kodowanie pikseli w obrazie
    a = bitmap[0]
    result = [a]
    for pixel in bitmap[1:]:
        a = pixel - a
        result.append(a)
        a = pixel
    return result


def differential_decoding(diffs):
    # Dekodowanie różnicowe pikseli w obrazie
    a = diffs[0]
    result = [a]
    for x in diffs[1:]:
        a = a + x
        result.append(a)
    return result


def quantify_uniform(bitmap, k):
    # Jednorodna kwantyzacja pikseli w obrazie
    step = 256 // (2 ** k)
    return [pixel.uniform_quantization(step) for pixel in bitmap]


def quantify_nonuniform(bitmap, k):
    # Niejednorodna kwantyzacja pikseli w obrazie
    reds = []
    greens = []
    blues = []
    for pixel in bitmap:
        reds.append(pixel.red)
        greens.append(pixel.green)
        blues.append(pixel.blue)

    # Kwantyzacja niejednorodna dla każdego kanału koloru
    red_codebook = nonuniform_quantization(reds, k)
    green_codebook = nonuniform_quantization(greens, k)
    blues_codebook = nonuniform_quantization(blues, k)

    # Zastosowanie nowego kodbooka do każdego kanału koloru
    new_reds = [red_codebook[elem] for elem in reds]
    new_greens = [green_codebook[elem] for elem in greens]
    new_blues = [blues_codebook[elem] for elem in blues]

    quantified_bitmap = []
    for red, green, blue in zip(new_reds, new_greens, new_blues):
        quantified_bitmap.append(Pixel(red, green, blue))

    return quantified_bitmap


def nonuniform_quantization(pixels, k):
    # Niejednorodna kwantyzacja wartości pikseli
    n = 2 ** k
    d = {i: 0 for i in range(256)}
    for p in pixels:
        d[p] += 1
    intervals = {(i, i + 1): d[i] + d[i + 1] for i in d if i % 2 == 0}

    # Redukcja ilości przedziałów do n
    while len(intervals) > n:
        intervals_list = list(intervals)
        min_interval = min(intervals)
        i = intervals_list.index(min_interval)

        if i == 0:
            to_join = intervals_list[1]
        elif k == len(intervals_list) - 1:
            to_join = intervals_list[-2]
        else:
            to_join = (
                intervals_list[k - 1]
                if intervals[intervals_list[k - 1]] < intervals[intervals_list[k + 1]]
                else intervals_list[k + 1]
            )

        new_interval = (
            (min_interval[0], to_join[1])
            if to_join[0] > min_interval[0]
            else (to_join[0], min_interval[1])
        )

        intervals[new_interval] = intervals[min_interval] + intervals[to_join]
        del intervals[min_interval]
        del intervals[to_join]
        intervals = dict(sorted(intervals.items()))

    # Wyznaczenie wartości reprezentatywnych dla każdego przedziału
    values = [(interval[0] + interval[1]) // 2 for interval in intervals]
    codebook = {}
    j = 0
    for i in range(256):
        if j + 1 < n and abs(values[j + 1] - i) <= abs(values[j] - i):
            j += 1
        codebook[i] = values[j]

    return codebook


def encode(bitmap, k):
    # Kodowanie obrazu przy użyciu filtra niskoprzepustowego i wysokoprzepustowego
    filtered_low = [
        apply_filter(bitmap, x, y)
        for y in reversed(range(bitmap.height))
        for x in range(bitmap.width)
    ]
    filtered_high = [
        apply_filter(bitmap, x, y, True)
        for y in reversed(range(bitmap.height))
        for x in range(bitmap.width)
    ]

    # Różnicowe kodowanie obrazu niskoprzepustowego
    low = differential_coding(filtered_low)
    byte_array = bitmap_to_array(low)

    # Mapowanie wartości na liczby dodatnie dla kodowania Eliassa
    byte_array = [2 * x if x > 0 else abs(x) * 2 + 1 for x in byte_array]

    # Kodowanie Gamma
    bitstring = "".join([Gamma().encode(x) for x in byte_array])

    # Uzupełnienie bitstringa zerami
    if len(bitstring) % 8 != 0:
        bitstring += "0" * (8 - (len(bitstring) % 8))

    # Konwersja bitstringa na bajty
    b = bytes(int(bitstring[i: i + 8], 2) for i in range(0, len(bitstring), 8))

    # Kwantyzacja obrazu wysokoprzepustowego
    quantified = quantify_nonuniform(filtered_high, k)
    quantified_bytes = bytes(bitmap_to_array(quantified))

    # Testy jakości obrazu
    bitmap = [
        bitmap[x, y]
        for y in reversed(range(bitmap.height))
        for x in range(bitmap.width)
    ]

    l_mse, l_mse_r, l_mse_g, l_mse_b, l_snr = tests(bitmap, filtered_low)
    h_mse, h_mse_r, h_mse_g, h_mse_b, h_snr = tests(bitmap, quantified)
    
    print("Low:")
    print("    MSE:", l_mse)
    print("    MSE (red):", l_mse_r)
    print("    MSE (green):", l_mse_g)
    print("    MSE (blue):", l_mse_b)
    print("    SNR:", l_snr)
    print("\nHigh:")
    print("    MSE:", h_mse)
    print("    MSE (red):", h_mse_r)
    print("    MSE (green):", h_mse_g)
    print("    MSE (blue):", h_mse_b)
    print("    SNR:", h_snr)

    return filtered_low, b, filtered_high, quantified_bytes



def decode(payload_low):
    # Dekodowanie danych zakodowanych za pomocą kodu Gamma
    hexstring = payload_low.hex()
    bitstring = "".join(
        [
            "{0:08b}".format(int(hexstring[x: x + 2], base=16))
            for x in range(0, len(hexstring), 2)
        ]
    )

    # Dekodowanie za pomocą kodu Gamma
    codes = Gamma().decode(bitstring)
    # Przekształcenie do postaci różnicowej
    diffs = [x // 2 if x % 2 == 0 else -(x // 2) for x in codes]

    # Konstrukcja obrazu z różnicowych danych
    bitmap = [
        Pixel(int(diffs[i + 2]), int(diffs[i + 1]), int(diffs[i]))
        for i in range(0, len(diffs), 3)
    ]
    # Dekodowanie różnicowe
    bitmap = differential_decoding(bitmap)
    # Konwersja obrazu do postaci bajtowej
    bitmap = bitmap_to_array(bitmap)

    return bytes(bitmap)


def d(a, b):
    # Kwadrat różnicy między wartościami a i b
    return (a - b) ** 2


def mse(original, new):
    # Średni błąd kwadratowy między dwoma obrazami
    return (1 / len(original)) * sum([d(a, b) for a, b in zip(original, new)])


def snr(x, mserr):
    # Stosunek sygnału do szumu
    return ((1 / len(x)) * sum([d(i, 0) for i in x])) / mserr


def tests(original, new):
    # Testy jakości obrazu, zwraca MSE i SNR dla każdego kanału koloru
    original_array = []
    for pixel in original:
        original_array += [pixel.blue, pixel.green, pixel.red]

    original_red = [pixel.red for pixel in original]
    original_green = [pixel.green for pixel in original]
    original_blue = [pixel.blue for pixel in original]

    new_array = []
    for pixel in new:
        new_array += [pixel.blue, pixel.green, pixel.red]

    new_red = [pixel.red for pixel in new]
    new_green = [pixel.green for pixel in new]
    new_blue = [pixel.blue for pixel in new]

    # Obliczanie MSE i SNR dla każdego kanału koloru
    mserr = mse(original_array, new_array)
    mserr_red = mse(original_red, new_red)
    mserr_green = mse(original_green, new_green)
    mserr_blue = mse(original_blue, new_blue)
    snratio = snr(original_array, mserr)
    return mserr, mserr_red, mserr_green, mserr_blue, snratio


def main():
    print("\nLow-pass and high-pass filters\n")
    if (len(sys.argv) == 3 and sys.argv[2] == "--decode") or (len(sys.argv) == 4 and sys.argv[2] == "--encode"):
        with open(sys.argv[1], "rb") as f:
            # Wczytanie pliku TGA
            print(f"reading {sys.argv[1]}...\n")
            tga = f.read()
            header = tga[:18]
            width = tga[13] * 256 + tga[12]
            height = tga[15] * 256 + tga[14]
            footer = tga[18 + (3 * height * width):]

        if sys.argv[2] == "--encode":
            # Kodowanie obrazu
            print(f"encoding {sys.argv[1]}...\n")
            bitmap = Bitmap(tga[18: len(tga) - 26], width, height)

            if int(sys.argv[3]) < 1 or int(sys.argv[3]) > 7:
                print("Error: number must be between 0 and 8")
                sys.exit()
                
            k = int(sys.argv[3])
            filtered_low, encoded_low, filtered_high, encoded_high = encode(bitmap, k)
            filtered_low_bytes = bytes(bitmap_to_array(filtered_low))
            filtered_high_bytes = bytes(bitmap_to_array(filtered_high))

            # Zapis do plików wyjściowych
            print(f"\nsaving...\n")
            with open(sys.argv[1] + "_low.tga", "wb") as f:
                f.write(header + filtered_low_bytes + footer)
            with open(sys.argv[1] + "_low_encoded.bin", "wb") as f:
                f.write(header + encoded_low + footer)
            with open(sys.argv[1] + "_high.tga", "wb") as f:
                f.write(header + filtered_high_bytes + footer)
            with open(sys.argv[1] + "_high_encoded.tga", "wb") as f:
                f.write(header + encoded_high + footer)

        if sys.argv[2] == "--decode":
            # Dekodowanie obrazu
            print(f"decoding {sys.argv[1]}...\n")
            payload_low = tga[18:-26]
            decoded_bitmap = decode(payload_low)

            # Zapis do pliku wyjściowego
            print(f"\nsaving...\n")
            with open(sys.argv[1] + "_low_decoded.tga", "wb") as f:
                f.write(header + decoded_bitmap + footer)


    else:
        print("Using:\nfilters.py <input_file> --encode <bits_number>\nfilters.py <input_file> --decode")


if __name__ == "__main__":
    main()
