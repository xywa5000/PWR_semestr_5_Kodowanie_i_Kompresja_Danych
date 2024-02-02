import numpy as np
from PIL import Image
import argparse


def sub_band_decode_channel(y, z):
    """
    Rekonstruuje pojedynczy kanał obrazu z podpasmowych składowych y i z.
    :param y: 2D numpy array, składowa wysokoprzepustowa
    :param z: 2D numpy array, składowa niskoprzepustowa
    :return: 2D numpy array, zrekonstruowany kanał obrazu
    """
    rows, cols = y.shape
    reconstructed_channel = np.empty((rows * 2, cols * 2), dtype=np.float32)
    i = 0
    # ważna kolejnośc pasm
    for row in range(rows*2):
        for col in range(cols*2):
            y_value = y[row//2, col//2]
            z_value = z[row//2, col//2]
            if i % 2 == 0:
                # x_{2n-1} = y_{2n} - z_{2n}
                reconstructed_channel[row, col] = y_value - z_value
            else:
                # x_{2n} = y_{2n} + z_{2n}
                reconstructed_channel[row, col] = y_value + z_value
            i+=1

    reconstructed_channel = np.clip(reconstructed_channel, 0, 255).astype(np.uint8)
    return reconstructed_channel


def sub_band_decode(encoded_channels):
    """
    Dekoduje obraz z podpasmowych składowych.
    :param encoded_channels: Lista zawierająca parę składowych y i z dla każdego koloru
    :return: 3D numpy array, zrekonstruowany obraz
    """
    channels = [sub_band_decode_channel(y, z) for y, z in encoded_channels]
    return np.stack(channels, axis=-1).astype(np.uint8)


def reverse_differential_coding(d):
    """
    Odwraca kodowanie różnicowe.
    :param d: 2D numpy array, składowa różnicowa
    :return: 2D numpy array, zrekonstruowana składowa oryginalna
    """
    flat_d = d.flatten()
    reconstructed = np.zeros_like(flat_d, dtype=np.float32)

    reconstructed[0] = flat_d[0] # Pierwszy element

    for i in range(1, len(flat_d)):
        reconstructed[i] = reconstructed[i-1] + flat_d[i]

    reconstructed_2D = reconstructed.reshape(d.shape)

    return reconstructed_2D


def load_array(path):
    """
    Wczytuje tablicę numpy z pliku.
    :param path: Ścieżka do pliku
    :return: Numpy array
    """
    return np.load(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decode image encoded with encode.py')
    parser.add_argument('input_file_name', type=str, help='Numpy arrays name: y_filename.npy, z_filename.npy')
    parser.add_argument('output_file_name', type=str, help='Output image file name.')

    args = parser.parse_args()

    y_combined_reloaded = load_array(f'y_{args.input_file_name}.npy')
    z_combined_reloaded = load_array(f'z_{args.input_file_name}.npy')

    restored_low_band_components = [reverse_differential_coding(y_combined_reloaded[:, :, i]) for i in range(3)]
    
    reloaded_encoded_channels = [(restored_low_band_components[i], z_combined_reloaded[:, :, i]) for i in range(3)]
    
    reconstructed_array = sub_band_decode(reloaded_encoded_channels)

    output_image_path = args.output_file_name
    reconstructed_image = Image.fromarray(reconstructed_array)
    reconstructed_image.save(output_image_path)
