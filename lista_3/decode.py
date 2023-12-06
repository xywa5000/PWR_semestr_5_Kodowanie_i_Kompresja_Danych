import sys
import math

def fib_sequence(n):
    sequence = []
    a, b = 0, 1

    sequence = [a]
    for _ in range(n + 1):
        sequence.append(b)
        a, b = b, a + b

    return sequence[1:]

def fib_decode(code):
    codes = [x + "1" for x in code.split("11")][:-1]
    seq = fib_sequence(max(len(x) for x in codes))
    return [
        sum(seq[i] if x == "1" else 0 for i, x in enumerate(code))
        for code in codes
    ]

def gamma(code):
    codes = []
    counter = 0
    idx = 0
    while idx < len(code):
        if code[idx] == "0":
            counter += 1
            idx += 1
        else:
            codes.append(int(code[idx : idx + counter + 1], base=2))
            idx += counter + 1
            counter = 0
    return codes

def delta(code):
    codes = []
    L = 0
    idx = 0
    while idx < len(code):
        if code[idx] == "0":
            L += 1
            idx += 1
        else:
            n = int(code[idx : idx + L + 1], base=2) - 1
            idx += L + 1
            codes.append(int("1" + code[idx : idx + n], base=2))
            idx += n
            L = 0
    return codes

def omega(code):
    codes = []
    i = 0
    n = 1
    while i < len(code):
        if code[i] == "0":
            codes.append(n)
            n = 1
            i += 1
        elif code[i] == "1":
            s = code[i : i + n + 1]
            i += n + 1
            n = int(s, base=2)
    return codes

def decode(input_file, output_file, func=omega):
    with open(input_file, "rb") as inp, open(output_file, "wb") as output:
        dictionary = [bytes([i]) for i in range(256)]
        hexstring = inp.read().hex()
        bitstring = "".join(["{0:08b}".format(int(hexstring[x : x + 2], base=16)) for x in range(0, len(hexstring), 2)])

        # padding?
        if func.__name__ not in ["gamma", "delta"]:
            num = bitstring[:3]
            bitstring = bitstring[3:len(bitstring)-(int(num, base=2))]

        codes = list(map(lambda x: x - 1, func(bitstring)))

        idx = 0
        OLD = codes[idx]
        S = dictionary[OLD]
        C = dictionary[OLD][:1]
        result = S
        idx += 1

        while idx < len(codes):
            NEW = codes[idx]
            if NEW >= len(dictionary):
                S = dictionary[OLD]
                S = S + C
            else:
                S = dictionary[NEW]
            result += S
            C = S[:1]
            dictionary.append(dictionary[OLD] + C)
            OLD = NEW
            idx += 1

        output.write(result)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        decode(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        encoding_functions = {"--delta": delta, "--gamma": gamma, "--omega": omega, "--fib": fib_decode}
        encoding_function = encoding_functions.get(sys.argv[3], omega)

        decode(sys.argv[1], sys.argv[2], encoding_function)
    else:
        print("\ncorrect parameters: <input_file> <output_file> <type_of_coding>\ntype of coding options: --delta --gamma --omega --fib\n")
