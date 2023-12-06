import sys
import math

def fib_sequence(n):
    sequence = []
    a, b = 0, 1

    while a <= n:
        sequence.append(a)
        a, b = b, a + b

    return sequence[1:]

def fib_encode(n):
    sequence = fib_sequence(n)
    result = ["0" for _ in sequence]

    while n > 0:
        i, x = [(i, x) for i, x in enumerate(sequence) if x <= n][-1]
        result[i] = "1"
        n %= x

    result.append("1")
    return "".join(result)

def omega(number):
    code = "0"
    k = number

    while k > 1:
        binary_k = bin(k)[2:]
        code = binary_k + code
        k = len(binary_k) - 1

    return code

def gamma(number):
    code = bin(number)[2:]
    return "0" * (len(code) - 1) + code

def delta(number):
    code = bin(number)[3:]
    return gamma(len(code) + 1) + code

def encode(input_file, output_file, func=omega):
    with open(input_file, "rb") as inp, open(output_file, "wb") as output:
        dictionary = {chr(i): i for i in range(256)}
        input_bytes = inp.read()
        bitstring_output = ""

        P = chr(int.from_bytes([input_bytes[0]], "big"))

        for byte in input_bytes[1:]:
            C = chr(int.from_bytes([byte], "big"))

            if P + C in dictionary:
                P = P + C
            else:
                bitstring_output += func(dictionary[P] + 1)
                dictionary[P + C] = len(dictionary)
                P = C

        bitstring_output += func(dictionary[P] + 1)

        if func.__name__ in ["gamma", "delta"]:
            bitstring_output = bitstring_output.ljust((len(bitstring_output) + 7) // 8 * 8, "0")
        else:
            pad_len = (8 - (len(bitstring_output) + 3) % 8) % 8
            bitstring_output = bin(pad_len)[2:].zfill(3) + bitstring_output + "0" * pad_len

        b = bytes(int(bitstring_output[i:i + 8], 2) for i in range(0, len(bitstring_output), 8))
        output.write(b)
        return b

def entropy(freq, num_of_symbols):
    H = sum(freq[i] / num_of_symbols * -math.log(freq[i] / num_of_symbols, 2) for i in freq)
    return H

def get_freq(sth):
    freq = {}

    for symbol in sth:
        if not symbol:
            break

        freq[symbol] = freq.get(symbol, 0) + 1

    return freq

def stats(input_file, output):
    with open(input_file, "rb") as f:
        inp = f.read()
        input_len = len(inp)
        input_freq = get_freq(inp)

    output_len = len(output)
    output_freq = get_freq(output)

    print("\nInput:")
    print("   entropy:", entropy(input_freq, input_len))
    print("   size:", input_len)
    print("Output:")
    print("   entropy:", entropy(output_freq, output_len))
    print("   size:", output_len)
    print("Compression ratio:", output_len / input_len, "\n")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        res = encode(sys.argv[1], sys.argv[2])
        stats(sys.argv[1], res)
    elif len(sys.argv) == 4:
        encoding_functions = {"--delta": delta, "--gamma": gamma, "--omega": omega, "--fib": fib_encode}
        encoding_function = encoding_functions.get(sys.argv[3], omega)

        res = encode(sys.argv[1], sys.argv[2], encoding_function)
        stats(sys.argv[1], res)
    else:
        print("\ncorrect parameters: <input_file> <output_file> <type_of_coding>\ntype of coding options: --delta --gamma --omega --fib\n")
