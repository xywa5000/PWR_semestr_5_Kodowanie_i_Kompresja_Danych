from sys import argv

def count_bit_differences(byte1, byte2):
    """Counts the number of differing bits between two bytes."""
    count = 0
    for i in range(8):
        if (byte1 >> i) & 1 != (byte2 >> i) & 1:
            count += 1
    return count

def check(in1, in2):
    """Compares two input files byte by byte and prints the number of differing bits."""
    hex1 = in1.read().hex()
    hex2 = in2.read().hex()

    if len(hex1) != len(hex2):
        print("Pliki są różnej długości")
        return

    diff_bits = 0
    total_bits = 0
    diffs = 0
    diffs_1_bit = 0
    diffs_2_bits = 0
    diffs_3_bits = 0
    diffs_4_bits = 0

    for byte1, byte2 in zip(hex1, hex2):
        byte_diffs = count_bit_differences(int(byte1, 16), int(byte2, 16))
        diff_bits += byte_diffs
        total_bits += 4
        if byte_diffs != 0:
            diffs += 1
        if byte_diffs == 1:
            diffs_1_bit += 1
        elif byte_diffs == 2:
            diffs_2_bits += 1
        elif byte_diffs == 3:
            diffs_3_bits += 1
        elif byte_diffs == 4:
            diffs_4_bits += 1

    print(f"Liczba różnych bloków: {diffs}")
    print(f"Liczba bloków różniących się 1 bitem:  {diffs_1_bit}")
    print(f"Liczba bloków różniących się 2 bitami: {diffs_2_bits}")
    print(f"Liczba bloków różniących się 3 bitami: {diffs_3_bits}")
    print(f"Liczba bloków różniących się 4 bitami: {diffs_4_bits}")
    print(f"Liczba bitów: {total_bits}")
    print(f"Liczba zmienionych bitów: {diff_bits}")
    print(f"Procent zmienionych bitów: {diff_bits / total_bits}")

def main():
    if len(argv) == 3:
        in1 = argv[1]
        in2 = argv[2]

        with open(in1, "rb") as f1, open(in2, "rb") as f2:
            check(f1, f2)
    else:
        print("Error! Usage: python comparator.py <file_1> <file_2>")

if __name__ == "__main__":
    main()
