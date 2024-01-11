import sys
from math import sqrt, log10

def read_tga_header(file_path):
    with open(file_path, "rb") as file:
        header = file.read(18)
    return header

def read_tga_image(file_path, width, height):
    with open(file_path, "rb") as file:
        file.seek(18)
        image_data = file.read(width * height * 3)
    return image_data

def quantize(value, num_bits):
    step_size = 256 / (2 ** num_bits)
    quantized_value = int(value / step_size) * step_size
    return quantized_value

def perform_uniform_quantization(image_data, red_bits, green_bits, blue_bits):
    width = int(sqrt(len(image_data) / 3))
    height = width
    quantized_image = bytearray()

    mse_total = 0.0
    mse_red = 0.0
    mse_green = 0.0
    mse_blue = 0.0

    for i in range(0, len(image_data), 3):
        red = quantize(image_data[i], red_bits)
        green = quantize(image_data[i + 1], green_bits)
        blue = quantize(image_data[i + 2], blue_bits)

        mse_total += (red - image_data[i]) ** 2 + (green - image_data[i + 1]) ** 2 + (blue - image_data[i + 2]) ** 2
        mse_red += (red - image_data[i]) ** 2
        mse_green += (green - image_data[i + 1]) ** 2
        mse_blue += (blue - image_data[i + 2]) ** 2

        quantized_image.extend([int(red), int(green), int(blue)])

    mse_total /= (width * height)
    mse_red /= (width * height)
    mse_green /= (width * height)
    mse_blue /= (width * height)

    snr_total = 255 ** 2 / mse_total
    if mse_red == 0.0:
        snr_red = float('inf')
    else:
        snr_red = 255 ** 2 / mse_red
    if mse_green == 0.0:
        snr_green = float('inf')
    else:
        snr_green = 255 ** 2 / mse_green
    if mse_blue == 0.0:
        snr_blue = float('inf')
    else:
        snr_blue = 255 ** 2 / mse_blue

    print(f"mse = {mse_total:.6f}")
    print(f"mse(r) = {mse_red:.6f}")
    print(f"mse(g) = {mse_green:.6f}")
    print(f"mse(b) = {mse_blue:.6f}")

    print(f"SNR = {snr_total:.6f} ({10 * log10(snr_total):.6f}dB)")
    print(f"SNR(r) = {snr_red:.6f} ({10 * log10(snr_red):.6f}dB)")
    print(f"SNR(g) = {snr_green:.6f} ({10 * log10(snr_green):.6f}dB)")
    print(f"SNR(b) = {snr_blue:.6f} ({10 * log10(snr_blue):.6f}dB)")

    return quantized_image

def save_quantized_image(file_path, header, quantized_data):
    with open(file_path, "wb") as file:
        file.write(header)
        file.write(quantized_data)

def main():
    if len(sys.argv) != 6:
        print("Usage: python mark_3.py input.tga output.tga red_bits green_bits blue_bits")
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    red_bits = int(sys.argv[3])
    green_bits = int(sys.argv[4])
    blue_bits = int(sys.argv[5])

    header = read_tga_header(input_file_path)
    width = int.from_bytes(header[12:14], byteorder="little")
    height = int.from_bytes(header[14:16], byteorder="little")

    original_image_data = read_tga_image(input_file_path, width, height)
    quantized_image_data = perform_uniform_quantization(original_image_data, red_bits, green_bits, blue_bits)

    save_quantized_image(output_file_path, header, quantized_image_data)
    print(f"Quantized image saved to {output_file_path}")

if __name__ == "__main__":
    main()
