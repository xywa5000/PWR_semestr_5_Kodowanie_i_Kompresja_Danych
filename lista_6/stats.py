import numpy as np
from PIL import Image
import argparse
import math


def calculate_mean_squared_error(original, reconstructed):
    mse = np.mean((original - reconstructed) ** 2)
    return mse

def calculate_signal_to_noise_ratio(original, mse):
    signal_power = np.var(original)
    if mse != 0:
        snr = 10 * np.log10(signal_power / mse)
        return snr
    else:
        return math.inf

def calculate_metrics_per_channel(original, reconstructed):
    metrics = {}
    for i in range(3): 
        original_channel = original[:, :, i]
        reconstructed_channel = reconstructed[:, :, i]
        mse = calculate_mean_squared_error(original_channel, reconstructed_channel)
        snr = calculate_signal_to_noise_ratio(original_channel, mse)
        metrics[f"Channel {i}"] = {"MSE": mse, "SNR": snr}
    return metrics

def trim_reconstructed_to_original_size(original, reconstructed):
    original_rows, original_cols = original.shape[:2]
    return reconstructed[:original_rows, :original_cols]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate image metrics.')
    parser.add_argument('original_image', type=str, help='Path to the original image file.')
    parser.add_argument('reconstructed_image', type=str, help='Path to the reconstructed image file.')

    args = parser.parse_args()

    original_image_path = args.original_image
    original_image = Image.open(original_image_path)
    original_image_array = np.array(original_image)

    reconstructed_image_path = args.reconstructed_image
    reconstructed_image = Image.open(reconstructed_image_path)
    
    reconstructed_image_array = np.array(reconstructed_image)
    reconstructed_image_array = trim_reconstructed_to_original_size(original_image_array, reconstructed_image_array)

    # Metrics
    overall_mse = calculate_mean_squared_error(original_image_array, reconstructed_image_array)
    overall_snr = calculate_signal_to_noise_ratio(original_image_array, overall_mse)

    channel_metrics = calculate_metrics_per_channel(original_image_array, reconstructed_image_array)

    print(f"Overall Mean Squared Error: {overall_mse}")
    print(f"Overall Signal-to-Noise Ratio: {overall_snr}")
    print("Per Channel Metrics:")
    for channel, metrics in channel_metrics.items():
        print(f"Channel {channel}: MSE = {metrics['MSE']}, SNR = {metrics['SNR']}")
