from random import random
from sys import argv

def swap(bit):
    """
    Funkcja zamieniająca 0 na 1 i 1 na 0.
    """
    return "1" if bit == "0" else "0"

def make_some_noise(input_file, output_file, p):
    """
    Funkcja dodająca losowy szum do danych binarnych.
    """
    with open(input_file, "rb") as f, open(output_file, "wb") as out:
        payload = f.read()

        hexstring = payload.hex()

        # Konwersja ciągu szesnastkowego na ciąg bitowy
        bitstring = "".join(
            [
                "{0:08b}".format(int(hexstring[x : x + 2], base=16))
                for x in range(0, len(hexstring), 2)
            ]
        )

        new_bitstring = ""
        for bit in bitstring:
            # Losowa decyzja czy zaszumiać bit
            if p > random():
                new_bitstring += swap(bit)
            else:
                new_bitstring += bit

        # Konwersja ciągu bitowego z powrotem na dane binarne i zapis do pliku wyjściowego
        b = bytes(
            int(new_bitstring[i : i + 8], 2) for i in range(0, len(new_bitstring), 8)
        )
        out.write(b)

def main():
    """
    Główna funkcja programu, która przetwarza plik wejściowy i generuje plik wyjściowy.
    """
    if len(argv) == 4:
        p = float(argv[1]) # Prawdopodobieństwo szumu
        input_file = argv[2] # Nazwa pliku wejściowego
        output_file = argv[3] # Nazwa pliku wyjściowego

        make_some_noise(input_file, output_file, p)
    else:
        print("Error! Usage: python comparator.py <probability - (0.0; 1.0)> <input_file> <output_file>")

if __name__ == "__main__":
    main()
