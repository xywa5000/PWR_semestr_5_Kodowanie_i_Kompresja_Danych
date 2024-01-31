"""
Program konwertujący plik *.txt na *.bin
Użycie: t_txt_to_bin.py <txt_file> <bin_file>
Uwaga: w pliku *.txt powinien zawierać tylko znaki '0' i '1'
Uwaga: liczba znaków w pliku *.txt powinna być podzielna przez 8
"""

from sys import argv


def text_to_binary(input_file, output_file):
    try:
        with open(input_file, 'r') as f_in:
            text_data = f_in.read().strip()  # Usuń ewentualne białe znaki

            # Podziel ciąg zer i jedynek na grupy po 8 i konwertuj je na bajty
            binary_data = bytearray([int(text_data[i:i+8], 2) for i in range(0, len(text_data), 8)])

        with open(output_file, 'wb') as f_out:
            f_out.write(binary_data)

        print("Konwersja zakończona sukcesem!")

    except Exception as e:
        print("Wystąpił błąd podczas konwersji:", str(e))


if __name__ == "__main__":
    input_file = argv[1]
    output_file = argv[2]
    text_to_binary(input_file, output_file)
