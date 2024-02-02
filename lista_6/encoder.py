import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import argparse


def sub_band_encode_channel(channel):
    """
    Rozdziela kanał na składowe wysokoprzepustową (y) i niskoprzepustową (z).
    :param channel: 2D numpy array, pojedynczy kanał obrazu
    :return: y, z - składowe wysokoprzepustowa i niskoprzepustowa
    """
    rows, cols = channel.shape

    if rows % 2 != 0:
        channel = np.pad(channel, ((0, 1), (0, 0)), mode='edge')
    if cols % 2 != 0:
        channel = np.pad(channel, ((0, 0), (0, 1)), mode='edge')

    rows, cols = channel.shape
    
    # Konwersja do float32 na potrzebę obliczeń (unikanie Overflow)
    channel = channel.astype(np.float32)

    y = np.empty((rows // 2, cols // 2), dtype=np.float32)
    z = np.empty((rows // 2, cols // 2), dtype=np.float32)

    i = 0
    prev = 0
    curr = 0

    for row in range(0, rows):
        for col in range(0, cols):
            if i % 2 == 0:
                prev = channel[row][col] # x_{2n-1}
            else:
                curr = channel[row][col] # x_{2n} licząc elementy od 1
                # srdnia y_{2n} = (x_{2n} + x_{2n-1}) /2 
                y[row//2, col//2] = (curr + prev)/2 
                # odchylenie z_{2n} = (x_{2n} - x_{2n-1}) /2 
                z[row//2, col//2] = (curr - prev)/2
            i += 1

    return y, z


def sub_band_encode(image_array):
    """
    Koduje obraz za pomocą podpasmowego kodowania.
    :param image_array: 3D numpy array, obraz
    :return: Lista zawierająca składowe wysokoprzepustowe i niskoprzepustowe dla każdego koloru
    """
    return [sub_band_encode_channel(image_array[:, :, c]) for c in range(3)]


def uniform_quantizer(channel, k):
    """
    Tworzy równomierny kwantyzator.
    :param channel: 2D numpy array, pojedynczy kanał obrazu
    :param k: int, liczba bitów kwantyzacji
    :return: Lista zawierająca wartości kwantyzatora
    """
    min_val = np.min(channel)
    max_val = np.max(channel)
    
    # Wyliczanie równomiernych przedziałów kwantyzatora
    quantizer_values = np.linspace(min_val, max_val, num=2**k)

    return quantizer_values



def quantize(channel, k):
    """
    Kwantyzuje kanał obrazu.
    :param channel: 2D numpy array, pojedynczy kanał obrazu
    :param k: int, liczba bitów kwantyzacji
    :return: Kanał po zastosowaniu kwantyzacji
    """
    quantizer_values = uniform_quantizer(channel, k)
    quantized_channel = np.vectorize(lambda x: min(quantizer_values, key=lambda c: abs(x - c)))(channel)
    return quantized_channel


def differential_coding(x, k):
    """
    Koduje różnicowo wartości pikseli obrazu.
    :param x: 2D numpy array, pojedynczy kanał obrazu
    :param k: int, liczba bitów kwantyzacji
    :return: Zdekodowany kanał obrazu
    """

    #kodowanie różnicowe
    flat_x = x.astype(np.float32).flatten() # podobno splaszcza
    d = np.zeros_like(flat_x, dtype=np.float32) 
    d[0] = flat_x[0]
    for i in range(1, len(flat_x)):
        d[i] = flat_x[i] - flat_x[i-1] 
    
    d_2D = d.reshape(x.shape)

    quantizer_values = uniform_quantizer(d_2D, k)

    flat_x = x.astype(np.float32).flatten() # podobno splaszcza
    
    d = np.zeros_like(flat_x, dtype=np.float32)  # Różnice
    q = np.zeros_like(flat_x, dtype=np.float32)  # Skwantyzowane wartości
    q_error = np.zeros_like(flat_x, dtype=np.float32)  # Błędy kwantyzacji

    d[0] = flat_x[0]
    q[0] = min(quantizer_values, key=lambda q_val: abs(d[0] - q_val))
    q_error[0] = q[0] - d[0]
    
    for i in range(1, len(flat_x)):
        d[i] = flat_x[i] - (flat_x[i-1] + q_error[i-1]) 
        q[i] = min(quantizer_values, key=lambda q_val: abs(d[i] - q_val))
        q_error[i] = q[i] - d[i]
    
    q_2D = q.reshape(x.shape)
    return q_2D


def save_array(array, path):
    """
    Zapisuje tablicę numpy do pliku.
    :param array: Numpy array
    :param path: Ścieżka do pliku
    """
    np.save(path, array)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Encode image with sub-band coding')
    parser.add_argument('input_file_name', type=str, help='Input image file name.')
    parser.add_argument('output_file_name', type=str, help='Numpy arrays name. y_filename, z_filename')
    parser.add_argument('k', type=int, help='Number of bits for quantization.')

    args = parser.parse_args()

    image_path = args.input_file_name
    image = Image.open(image_path)
    image_array = np.array(image)

    # Kodowanie dla każdego koloru
    encoded_channels = [sub_band_encode_channel(image_array[:, :, c]) for c in range(3)]

    low_band_components = [y for y, _ in encoded_channels]
    high_band_components = [z for _, z in encoded_channels]

    # Kwantyzacja high-pass
    k_means_quantized_high_band_components = [quantize(z, args.k) for z in high_band_components]

    # Kodowanie różnicowe + kwantyzacja low-pass
    differential_low_band_components = [differential_coding(y, args.k) for y in low_band_components]

    y_combined = np.stack(differential_low_band_components, axis=-1).astype(np.float16)
    z_combined = np.stack(k_means_quantized_high_band_components, axis=-1).astype(np.int8)
    save_array(y_combined, f'y_{args.output_file_name}.npy')
    save_array(z_combined, f'z_{args.output_file_name}.npy')
