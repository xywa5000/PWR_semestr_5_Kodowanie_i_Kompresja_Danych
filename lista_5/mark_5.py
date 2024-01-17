import sys
import math

# Wczytuje plik TGA i zwraca nagłówek, stopkę, listę pikseli, szerokość i wysokość obrazu.
def read_TGA(filename):
    with open(filename, "rb") as f:
        byte = f.read()
        data = [int(x) for x in byte]
        image_width = data[13] * 256 + data[12]
        image_height = data[15] * 256 + data[14]
        header = byte[:18]
        source = data[18:18 + (3 * image_height * image_width)]
        footer = byte[18 + (3 * image_height * image_width):]
        source.reverse()  # Własność tych plików, bez reverse byłoby B G R
        pixels_list = []
        for i in range(image_height):
            for j in range(image_width):
                index = (image_width * i + j) * 3
                pixels_list.append((source[index], source[index + 1], source[index + 2]))
        return header, footer, pixels_list, image_width, image_height

# Zapisuje plik TGA z podanym nagłówkiem, stopką, danymi pikseli i nazwą pliku.
def write_TGA(header, source_to_bytes, footer, filename):
    with open(filename, "wb") as out:
        out.write(header)
        out.write(source_to_bytes)
        out.write(footer)

# Oblicza średnią wartość dla zestawu pikseli.
def avg(pixels):
    size = len(pixels)
    average = [0, 0, 0]
    for item in pixels:
        for i in range(3):
            average[i] += item[i] / size
    return average

# Oblicza odległość Manhattan pomiędzy dwoma wektorami.
def distance_manhattan(source, variable):
    return sum(abs(sourceElement - variableElement) for sourceElement, variableElement in zip(source, variable))

# Oblicza odległość euklidesową pomiędzy dwoma wektorami.
def distance_euclid(source, variable):
    return sum((sourceElement - variableElement) ** 2 for sourceElement, variableElement in zip(source, variable))

# Oblicza pierwszą miarę dystorsji dla podanego punktu i zestawu pikseli.
def first_distortion(pixels, point, size):
    distance = 0
    for lst in pixels:
        distance = (distance + distance_euclid(lst, point)) / size
    return distance

# Ocena dystorsji dla punktu i zestawu pikseli.
def evaluate_distortion(pixels, point, size):
    distance = 0
    for i, lst in enumerate(pixels):
        for element in lst:
            distance = (distance + distance_euclid(point[i], element)) / size
    return distance

# Zwraca nowy wektor po perturbacji wartości.
def new_vector(vector, perturbation):
    for i in range(3):
        vector[i] = vector[i] + perturbation
        if vector[i] > 255:
            vector[i] = 255
        if vector[i] < 0:
            vector[i] = 0
    return vector

# Podział kodów na dwie części z perturbacją.
def divide(pixels, codebook, distortion, size):
    divided_codebook = []

    for element in codebook:
        c1 = new_vector(element[:], 0.001)
        divided_codebook.append(c1)
        c2 = new_vector(element[:], -0.001)
        divided_codebook.append(c2)

    codebook = divided_codebook
    iter_count = 0
    while iter_count < 10:
        centers = [[] for _ in range(len(codebook))]
        for i, vertex in enumerate(pixels):
            min_distance = None
            min_point = 0
            for j, point in enumerate(codebook):
                distance = distance_manhattan(point, vertex)
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_point = j
                centers[min_point].append(vertex)

        tmp_distortion = evaluate_distortion(centers, codebook, size)
        for i in range(len(centers)):
            if len(centers[i]) == 0:
                continue
            centers[i] = avg(centers[i])
            new_center = round_centers(centers[i])
            if new_center in codebook:
                continue
            codebook[i] = centers[i]

        iter_count += 1

    return codebook, distortion

# Algorytm LBG do kwantyzacji wektorów pikseli.
def LBG(pixels, iterations, eps):
    size = len(pixels)
    codebook = []
    codebook.append(avg(pixels))
    distortion = first_distortion(pixels, codebook[0], size)
    print("   iterations : codebook")
    while len(codebook) < iterations:
        codebook, distortion = divide(pixels, codebook, distortion, size)
        print(f"   {iterations} : {len(codebook)}")
    return codebook

# Zaokrągla wartości w centrach kodów.
def round_centers(centers):
    for i in range(3):
        centers[i] = round(centers[i])
    return centers

# Zaokrągla wartości w rezultacie algorytmu.
def round_result(result):
    for lst in result:
        for i in range(len(lst)):
            lst[i] = round(lst[i])
    return result

# Przypisuje każdemu pikselowi wartość najbliższego kodu z wyniku algorytmu.
def convert(pixels, result):
    source = []
    for pixel in pixels:
        distances = [distance_manhattan(item, pixel) for item in result]
        source.append(result[min(range(len(distances)), key=distances.__getitem__)])
    return source

# Konwertuje listę pikseli na bajty.
def pixels_to_bytes(pixels):
    pixels.reverse()
    pixels_bytes = []
    for pixel in pixels:
        for color in reversed(pixel):
            pixels_bytes.append(color)

    return bytes(pixels_bytes)

# Oblicza błąd średniokwadratowy (MSE) między oryginalnymi a przetworzonymi pikselami.
def mse(original, new):
    return (1 / len(original)) * sum([distance_euclid(original[i], new[i]) for i in range(len(original))])

# Oblicza stosunek sygnał-szum (SNR) na podstawie oryginalnych pikseli i błędu średniokwadratowego.
def snr(x, mserr):
    current_sum = 0
    for element in x:
        for pixel in element:
            current_sum += pixel
    snr_val = current_sum * current_sum
    snr_val = snr_val / (3 * len(x))
    snr_val = snr_val / mserr
    return 10 * math.log10(snr_val)

# Główna funkcja programu, wczytuje argumenty wiersza poleceń i uruchamia algorytm LBG.
if __name__ == '__main__':
    print("parsing args...")
    if len(sys.argv) != 4:
        print("Usage: jpegls.py <plik_wejsciowy> <plik_wyjsciowy> <liczba_kolorow>")
        sys.exit()
    file = sys.argv[1]
    out = sys.argv[2]
    iterations = int(sys.argv[3])
    eps = 0.001
    print(f"reading {file}...")
    header, footer, pixels, image_width, image_height = read_TGA(file)
    print("LBG alogithm...")
    result = LBG(pixels, 2 ** iterations, eps)
    print("round results...")
    result = round_result(result)
    print("converting...")
    source = convert(pixels, result)
    print("computing mse and snr...")
    mserr = mse(pixels, source)
    snratio = snr(pixels, mserr)
    print("   MSE:", mserr)
    print("   SNR:", snratio)
    source_to_bytes = pixels_to_bytes(source)
    print(f"saving {out}...")
    write_TGA(header, source_to_bytes, footer, out)
