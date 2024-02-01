from sys import argv
import subprocess

def run_scripts(input_file, output_file, p):
    encoder_args = [input_file, "tmp_e.bin"]
    noisemaker_args = [p, "tmp_e.bin", "tmp_n.bin"]
    decoder_args = ["tmp_n.bin", output_file]
    comparator_args = [input_file, output_file]

    print(f"Start: encoder.py")
    result = subprocess.run(["python", "encoder.py"] + list(encoder_args), capture_output=True, text=True)
    print("\n" + result.stdout)
    if result.returncode != 0:
        print(f"Błąd: encoder.py zakończył się kodem błędu {result.returncode}")
    print(f"End: encoder.py")

    print(f"Start: noisemaker.py")
    result = subprocess.run(["python", "noisemaker.py"] + list(noisemaker_args), capture_output=True, text=True)
    print("\n" + result.stdout)
    if result.returncode != 0:
        print(f"Błąd: noisemaker.py zakończył się kodem błędu {result.returncode}")
    print(f"End: noisemaker.py")

    print(f"Start: decoder.py")
    result = subprocess.run(["python", "decoder.py"] + list(decoder_args), capture_output=True, text=True)
    print("\n" + result.stdout)
    if result.returncode != 0:
        print(f"Błąd: decoder.py zakończył się kodem błędu {result.returncode}")
    print(f"End: decoder.py")

    print(f"Start: comparator.py")
    result = subprocess.run(["python", "comparator.py"] + list(comparator_args), capture_output=True, text=True)
    print("\n" + result.stdout)
    if result.returncode != 0:
        print(f"Błąd: comparator.py zakończył się kodem błędu {result.returncode}")
    print(f"End: comparator.py")


def main():

    if len(argv) == 4:
        p = argv[3] # Prawdopodobieństwo szumu
        input_file = argv[1] # Nazwa pliku wejściowego
        output_file = argv[2] # Nazwa pliku wyjściowego

        run_scripts(input_file, output_file, p)
    else:
        print("Error! Usage: python pipeline.py <input_file> <output_file> <probability>")

if __name__ == "__main__":
    main()