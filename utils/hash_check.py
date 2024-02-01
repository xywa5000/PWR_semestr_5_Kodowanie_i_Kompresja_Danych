import hashlib
import sys

def calculate_hash(file_path):
    hash_object = hashlib.sha256()
    with open(file_path, "rb") as file:
        while True:
            data = file.read(65536)  # Chunk size: 64KB
            if not data:
                break
            hash_object.update(data)
    return hash_object.hexdigest()

def main():
    if len(sys.argv) != 3:
        print("Użycie: python hash_files.py <ścieżka_do_pliku_1> <ścieżka_do_pliku_2>")
        return

    file_path_1 = sys.argv[1]
    file_path_2 = sys.argv[2]

    try:
        hash_1 = calculate_hash(file_path_1)
        hash_2 = calculate_hash(file_path_2)
        print("Hash pliku 1:", hash_1)
        print("Hash pliku 2:", hash_2)
        if hash_1 == hash_2:
            print("\033[92mPliki są identyczne\033[0m")
        else:
            print("\033[91mPliki są różne\033[0m")
    except FileNotFoundError:
        print("Nie można odnaleźć pliku.")
    except PermissionError:
        print("Brak uprawnień do odczytu pliku.")
    except Exception as e:
        print("Wystąpił błąd:", e)

if __name__ == "__main__":
    main()
