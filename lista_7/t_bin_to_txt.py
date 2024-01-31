"""
Program konwertujący plik *.bin na *.txt
Użycie: t_bin_to_txt.py <bin_file> <txt_file>
"""

from sys import argv


def binary_to_text(input_file, output_file):
    try:
        with open(input_file, 'rb') as f_in:
            binary_data = f_in.read()
            # Konwertowanie każdego bajtu na ciąg zer i jedynek
            text_data = ''.join(format(byte, '08b') for byte in binary_data)

        with open(output_file, 'w') as f_out:
            f_out.write(text_data)

        print("Konwersja zakończona sukcesem!")

    except Exception as e:
        print("Wystąpił błąd podczas konwersji:", str(e))


if __name__ == "__main__":
    input_file = argv[1]
    output_file = argv[2]
    binary_to_text(input_file, output_file)
