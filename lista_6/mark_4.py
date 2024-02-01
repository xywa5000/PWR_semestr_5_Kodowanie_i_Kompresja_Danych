import sys

class Pixel:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str((self.r, self.g, self.b))

def read_tga(filename):
    # Odczyt nagłówka pliku TGA
    with open(filename, "br") as f:
        header = list(map(int, f.read(18)))
        width = header[13] * 256 + header[12]
        height = header[15] * 256 + header[14]
        
        # Inicjalizacja tablicy obrazu Pixelami
        image_array = [[Pixel(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        # Odczyt pikseli z pliku
        for row in range(height):
            for col in range(width):
                image_array[row][col] = Pixel(*(list(map(int, f.read(3)))))
        
        return image_array, header

# Funkcje do pobierania składowych koloru z obrazu
def get_r(bitmap):
    return [[pixl.r for pixl in row] for row in bitmap]

def get_g(bitmap):
    return [[pixl.g for pixl in row] for row in bitmap]

def get_b(bitmap):
    return [[pixl.b for pixl in row] for row in bitmap]


# Filtr dolnoprzepustowy i górnoprzepustowy
def highpass_filter(bm, i, j):
    x = (bm[i][j] - bm[i][j-1]) // 2
    if x < 0:
        return 0
    elif x > 255:
        return 255
    else:
        return x

def lowpass_filter(bm, i, j):
    x = (bm[i][j] + bm[i][j-1]) // 2
    if x < 0:
        return 0
    elif x > 255:
        return 255
    else:
        return x


# Funkcja transformująca obraz za pomocą zadanego filtra
def transform(bm, filter):
    rs, gs, bs = get_r(bm), get_g(bm), get_b(bm)
    
    output = [[None for pixl in row[1:-1]] for row in bm[1:-1]]

    for i, row in enumerate(bm[1:-1], 1):
        for j, _ in enumerate(row[1:-1], 1):
            output[i - 1][j - 1] = Pixel(
                filter(rs, i, j),
                filter(gs, i, j),
                filter(bs, i, j)
            )
    
    return output

# Funkcje do konwersji obrazu na bitstream i z powrotem
def bitmap_to_bytes(bitmap):
    payload = []
    for i, row in enumerate(bitmap):
        for j, e in enumerate(row):
            payload.extend([e.r, e.g, e.b])
    return bytes(payload)

def quants(bits, min):
    # Funkcja do generowania wartości i słownika kwantyzacji
    delta = 255 - min
    n = 2**bits
    values = []
    
    for i in range(n):
        values.append(int(min + delta / n * (i + 1)))
    
    quant_dict = {}
    k = 0
    for i in range(min, 256):
        if k + 1 < n and abs(values[k + 1] - i) <= abs(values[k] - i):
            k += 1
        quant_dict[i] = k

    return values, quant_dict

def differences_sequence(sequence):
    # Funkcja generująca sekwencję różnicową
    a = sequence[0]
    result = [a]
    for p in range(len(sequence)-1):
        a = sequence[p+1] - sequence[p]
        result.append(a)
    return result

def reconstruct_from_differences(diffs):
    # Funkcja odtwarzająca sekwencję z różnic
    a = diffs[0]
    result = [a]
    for q in range(len(diffs)-1):
        a = diffs[q+1] + result[q]
        if a > 255:
            result.append(255)
        elif a < 0:
            result.append(0)
        else:
            result.append(a)

    return result

def differential_encoding(bitmap, k):
    # Funkcja kodująca różnice pikseli
    rs = []
    gs = []
    bs = []
    for _, row in enumerate(bitmap):
        for _, pixel in enumerate(row):
            rs.append(pixel.r)
            gs.append(pixel.g)
            bs.append(pixel.b)

    subs_r = differences_sequence(rs)
    subs_g = differences_sequence(gs)
    subs_b = differences_sequence(bs)

    q_r = differential_quantizer(subs_r, k)
    q_g = differential_quantizer(subs_g, k)
    q_b = differential_quantizer(subs_b, k)

    bin_r = ['1' + bin(abs(el))[2:].zfill(8) if el < 0 else '0' + bin(abs(el))[2:].zfill(8) for el in q_r]
    bin_g = ['1' + bin(abs(el))[2:].zfill(8) if el < 0 else '0' + bin(abs(el))[2:].zfill(8) for el in q_g]
    bin_b = ['1' + bin(abs(el))[2:].zfill(8) if el < 0 else '0' + bin(abs(el))[2:].zfill(8) for el in q_b]

    bins = bin_r + bin_g + bin_b
    return ''.join(bins)

def differential_quantizer(diffs, k):
    # Oblicza maksymalną wartość różnicy
    max_diff = max(map(abs, diffs))

    # Oblicza wartość, którą należy dodać lub odjąć, aby uzyskać k kolorów
    step = max_diff // (2**k)
    if step == 0:
        step = 1

    # Kwantyzuje wartości różnicowe
    quantized_diffs = []
    for diff in diffs[1:]:
        if diff >= 0:
            quantized_diffs.append(int(diff // step) * step)
        else:
            quantized_diffs.append(-int(abs(diff) // step) * step)

    return quantized_diffs

def differential_encoding_v2(bitmap):
    # Funkcja kodująca różnice pikseli
    encoded_bitmap = []
    for row in bitmap:
        encoded_row = []
        for pixel in row:
            encoded_pixel = Pixel(
                encode_difference(pixel.r),
                encode_difference(pixel.g),
                encode_difference(pixel.b)
            )
            encoded_row.append(encoded_pixel)
        encoded_bitmap.append(encoded_row)
    return encoded_bitmap


def encode_difference(value):
    # Ograniczenie wartości do zakresu 0-255
    value = max(0, min(value, 255))
    binary_value = bin(abs(value))[2:].zfill(8)
    if value < 0:
        return '1' + binary_value
    else:
        return '0' + binary_value


def differential_decoding(file):
    # Funkcja dekodująca różnice pikseli
    bitstring, header = read_encoded(file)
    all_colors = [int(el[1:], 2) if el[0] == '0' else -int(el[1:], 2) for el in [bitstring[i:i + 9] for i in range(0, len(bitstring), 9)]]
    r_list = [el for el in all_colors[0: len(all_colors) // 3]]
    g_list = [el for el in all_colors[len(all_colors) // 3: 2 * len(all_colors) // 3]]
    b_list = [el for el in all_colors[2 * len(all_colors) // 3:]]
    
    rs = reconstruct_from_differences(r_list)
    gs = reconstruct_from_differences(g_list)
    bs = reconstruct_from_differences(b_list)
    print(len(all_colors))
    print(len(r_list))
    print(len(gs))
    print(len(bs))

    rgbs = []
    for i in range(len(rs)):
        rgbs.extend([rs[i], gs[i], bs[i]]) 

    return rgbs, header


def simple_quantizer_encoding(bitmap, bits):
    # Funkcja kodująca obraz za pomocą prostego kwantyzatora
    rs = []
    gs = []
    bs = []
    for _, row in enumerate(bitmap):
        for _, pixel in enumerate(row):
            rs.append(pixel.r)
            gs.append(pixel.g)
            bs.append(pixel.b)
    
    r_vals, quant_dict_r, _ = nonuniform_quantizer(rs, bits, 0, 255)
    g_vals, quant_dict_g, _ = nonuniform_quantizer(gs, bits, 0, 255)
    b_vals, quant_dict_b, _ = nonuniform_quantizer(bs, bits, 0, 255)

    c_r = [quant_dict_r[el] for el in rs]
    c_g = [quant_dict_g[el] for el in gs]
    c_b = [quant_dict_b[el] for el in bs]
    coded = c_r + c_g + c_b

    return ''.join([num_to_bits(el, bits) for el in coded]), r_vals, g_vals, b_vals

def simple_quantizer_decoding(file, bits):
    # Funkcja dekodująca obraz zakodowany prostym kwantyzatorem
    bitstring, header, rs, gs, bs = read_encoded2(file)
    all_colors = [int(bitstring[i:i + bits], 2) for i in range(0, len(bitstring), bits)]
    r_list = [rs[el] for el in all_colors[0: len(all_colors) // 3]]
    g_list = [gs[el] for el in all_colors[len(all_colors) // 3: 2 * len(all_colors) // 3]]
    b_list = [bs[el] for el in all_colors[2 * len(all_colors) // 3:]]
    rgbs = []
    for i in range(len(r_list)):
        rgbs.extend([r_list[i], g_list[i], b_list[i]])
    return rgbs, header

def read_encoded(file_in):
    # Funkcja do odczytu zakodowanego pliku
    with open(file_in, "br") as f:
        header = list(map(int, f.read(18)))
        n = int.from_bytes((f.read(1)), byteorder='big')
        result = ''.join([bin(c)[2:].zfill(8) for c in f.read()])
        result = result[:len(result) - n]
    return result, header

def read_encoded2(file_in):
    # Funkcja do odczytu zakodowanego pliku z dodatkowymi danymi
    with open(file_in, "br") as f:
        header = list(map(int, f.read(18)))
        rs = list(map(int, (f.readline()).decode('utf-8').split()))
        gs = list(map(int, (f.readline()).decode('utf-8').split()))
        bs = list(map(int, (f.readline()).decode('utf-8').split()))
        n = int.from_bytes((f.read(1)), byteorder='big')
        result = ''.join([bin(c)[2:].zfill(8) for c in f.read()])
        result = result[:len(result) - n]
    return result, header, rs, gs, bs

def bitstring_to_file(bitstring, header, file_out):
    # Funkcja zapisująca bitstream jako plik
    padding = 8 - len(bitstring) % 8
    bitstring = bitstring + padding * '0'
    bytes_list = bytes([padding]) + bytes([int(bitstring[i:i + 8], 2) for i in range(0, len(bitstring), 8)])
    with open(file_out, "bw") as f:
        f.write(bytes(header) + bytes_list)

def bitstring_to_file_with_vals(bitstring, header, file_out, rs, gs, bs):
    # Funkcja zapisująca bitstream z dodatkowymi danymi jako plik
    padding = 8 - len(bitstring) % 8
    bitstring = bitstring + padding * '0'
    bytes_list = bytes([padding]) + bytes([int(bitstring[i:i + 8], 2) for i in range(0, len(bitstring), 8)])
    with open(file_out, "bw") as f:
        f.write(bytes(header))
        f.write(bytes(" ".join(list(map(str, rs))), 'utf-8'))
        f.write(bytes('\n', 'utf-8'))
        f.write(bytes(" ".join(list(map(str, gs))), 'utf-8'))
        f.write(bytes('\n', 'utf-8'))
        f.write(bytes(" ".join(list(map(str, bs))), 'utf-8'))
        f.write(bytes('\n', 'utf-8'))
        f.write(bytes_list)

def nonuniform_quantizer(pixels, bits, min, max):
    # Prosta kwantyzacja nieliniowa
    n = 2**bits
    d = {i: 0 for i in range(min, max + 1)}
    for p in pixels:
        d[p] += 1
    intervals = {(i, i + 1): d[i] + d[i + 1] for i in d if i % 2 == 0} 

    while len(intervals) > n:
        min_interval = sorted(intervals, key=intervals.get)[0]
        dict_list = list(intervals)
        k = dict_list.index(min_interval)

        if k == 0:
            to_join = dict_list[1]
        elif k == len(dict_list) - 1:
            to_join = dict_list[-2]
        else:
            if intervals[dict_list[k - 1]] < intervals[dict_list[k + 1]]:
                to_join = dict_list[k - 1]
            else:
                to_join = dict_list[k + 1]
        if to_join[0] > min_interval[0]:
            new_interval = (min_interval[0], to_join[1])
        else:
            new_interval = (to_join[0], min_interval[1])
        new_interval_value = intervals[min_interval] + intervals[to_join]
        intervals[new_interval] = new_interval_value
        del intervals[min_interval]
        del intervals[to_join]
        intervals = dict(sorted(intervals.items()))

    values = [(el[0] + el[1]) // 2 for el in intervals]
    quant_dict = {}
    j = 0
    for i in range(min, max + 1):
        if j + 1 < n and abs(values[j + 1] - i) <= abs(values[j] - i):
            j += 1
        quant_dict[i] = j

    return values, quant_dict, intervals
        

def num_to_bits(x, n):
    return bin(x)[2:].zfill(n)

def smaller_header(h):
    if h[12] == 0:
        h[12] = 254
        h[13] -= 1
    else:
        h[12] -= 2
    if h[14] == 0:
        h[14] = 254
        h[15] -= 1
    else:
        h[14] -= 2  
    return h


def main():

    if len(sys.argv) != 6:
        print("Error! Usage:")
        print("python coders.py -e k in_file out_file1 out_file2")
        print("python coders.py -d k -H/-L in_file out_file ")
    else:
        if sys.argv[1] == '-e':
            bm, h = read_tga(sys.argv[3])
            h2 = smaller_header(h.copy())

            x1 = transform(bm, highpass_filter)
            x2 = transform(bm, lowpass_filter)

            bitstring1, rs1, gs1, bs1 = simple_quantizer_encoding(x1, int(sys.argv[2]))
            bitstring_to_file_with_vals(bitstring1, h2, sys.argv[4], rs1, gs1, bs1)

            bitstring2 = differential_encoding(x2, int(sys.argv[2]))
            bitstring_to_file(bitstring2, h2, sys.argv[5])

        elif sys.argv[1] == '-d':
            if sys.argv[3] == '-L':
                rgbs, header = differential_decoding(sys.argv[4])
                with open(sys.argv[5], "wb") as f:
                    f.write(bytes(header) + bytes(rgbs))
            elif sys.argv[3] == '-H':
                rgbs, header = simple_quantizer_decoding(sys.argv[4], int(sys.argv[2]))
                with open(sys.argv[5], "wb") as f:
                    f.write(bytes(header) + bytes(rgbs))

    
if __name__ == "__main__":
    main()