from sys import argv

def parity(bitstring, indices):
    """
    Funkcja obliczająca parzystość dla określonych indeksów w ciągu bitów.
    """
    sub = ""
    for i in indices:
        sub += bitstring[i]
    return str(str.count(sub, "1") % 2)

def to_hamming(bits):
    """
    Funkcja kodująca ciąg bitowy za pomocą kodu Hamminga.
    """
    p1 = parity(bits, [0, 1, 3])
    p2 = parity(bits, [0, 2, 3])
    p3 = parity(bits, [1, 2, 3])
    p = parity(p1 + p2 + bits[0] + p3 + bits[1:], range(7))
    return p1 + p2 + bits[0] + p3 + bits[1:] + p

def encode(bitstring):
    """
    Funkcja kodująca cały ciąg bitowy za pomocą kodu Hamminga.
    """
    encoded = ""
    while len(bitstring) >= 4:
        nibble = bitstring[0:4]
        encoded += to_hamming(nibble)
        bitstring = bitstring[4:]
    return encoded

def main():
    """
    Główna funkcja programu, która przetwarza plik wejściowy i generuje plik wyjściowy.
    """
    if len(argv) == 3:
        with open(argv[1], "rb") as f, open(argv[2], "wb") as output:
            payload = f.read()

            # Konwersja danych binarnych na ciąg szesnastkowy
            hexstring = payload.hex()

            # Konwersja ciągu szesnastkowego na ciąg bitowy
            bitstring = "".join(
                [
                    "{0:08b}".format(int(hexstring[x : x + 2], base=16))
                    for x in range(0, len(hexstring), 2)
                ]
            )

            # Kodowanie ciągu bitowego za pomocą kodu Hamminga
            result = encode(bitstring)

            # Konwersja zakodowanego ciągu bitowego z powrotem na dane binarne i zapis do pliku wyjściowego
            b = bytes(int(result[i : i + 8], 2) for i in range(0, len(result), 8))
            output.write(b)
            print("Encoded.")
    else:
        print("Error! Usage: python encoder.py <input_file> <output_file>")

if __name__ == "__main__":
    main()
