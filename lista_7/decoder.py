from sys import argv

# Macierz generatora kodu Hamminga
G = [
    "00000000",
    "11010010",
    "01010101",
    "10000111",
    "10011001",
    "01001011",
    "11001100",
    "00011110",
    "11100001",
    "00110011",
    "10110100",
    "01100110",
    "01111000",
    "10101010",
    "00101101",
    "11111111",
]

def from_hamming(bits, errors):
    """
    Funkcja dekodująca ciąg bitowy zakodowany za pomocą kodu Hamminga.
    """
    for code in G:
        hamm1 = [int(k) for k in bits]
        hamm2 = [int(k) for k in code]

        diff = []

        i = 0
        while i < 8:
            if hamm1[i] != hamm2[i]:
                diff.append(i + 1)
            i += 1

        if len(diff) == 0:
            return bits[2] + bits[4] + bits[5] + bits[6], errors

        if len(diff) == 1:
            return code[2] + code[4] + code[5] + code[6], errors

        if len(diff) == 2:
            errors += 1
            return None, errors

    return None, errors

def decode(bitstring):
    """
    Funkcja dekodująca cały ciąg bitowy zakodowany za pomocą kodu Hamminga.
    """
    decoded = ""
    errors = 0

    while len(bitstring) >= 8:
        nibble = bitstring[0:8]
        nibble, errors = from_hamming(nibble, errors)

        if nibble != None:
            decoded += nibble
        else:
            decoded += "0000"  # Wstawienie zera, gdy wykryto więcej niż 2 błędy

        bitstring = bitstring[8:]

    print(f"W {errors} blokach napotkano 2 błędy")

    return decoded

def main():
    """
    Główna funkcja programu, która przetwarza plik wejściowy i generuje plik wyjściowy.
    """
    if len(argv) == 3:
        with open(argv[1], "rb") as f, open(argv[2], "wb") as output:
            payload = f.read()

            hexstring = payload.hex()

            # Konwersja ciągu szesnastkowego na ciąg bitowy
            bitstring = "".join(
                [
                    "{0:08b}".format(int(hexstring[x : x + 2], base=16))
                    for x in range(0, len(hexstring), 2)
                ]
            )

            # Dekodowanie ciągu bitowego zakodowanego za pomocą kodu Hamminga
            result = decode(bitstring)

            # Konwersja zakodowanego ciągu bitowego z powrotem na dane binarne i zapis do pliku wyjściowego
            b = bytes(int(result[i : i + 8], 2) for i in range(0, len(result), 8))
            output.write(b)
    else:
        print("Error! Usage: python decoder.py <input_file> <output_file>")

if __name__ == "__main__":
    main()
