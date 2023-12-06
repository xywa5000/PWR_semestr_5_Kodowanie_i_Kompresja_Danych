#include <iostream>
#include <fstream>
#include <map>
#include <cmath>

// Funkcja obliczająca entropię
double entropy(std::map<unsigned char, int>& freq, int num_of_symbols) {
    double H = 0;
    for (const auto& pair : freq) {
        double probability = static_cast<double>(pair.second) / num_of_symbols;
        H += probability * (-log2(probability));
    }
    return H;
}

// Funkcja obliczająca warunkową entropię
double cond_entropy(std::map<unsigned char, std::map<unsigned char, int>>& cond_freq, std::map<unsigned char, int>& freq, int num_of_symbols) {
    double H = 0;
    for (const auto& i : freq) {
        double symbol_entropy = 0;
        for (const auto& j : cond_freq[i.first]) {
            double probability = static_cast<double>(j.second) / i.second;
            symbol_entropy += probability * (-log2(probability));
        }
        H += (static_cast<double>(i.second) / num_of_symbols) * symbol_entropy;
    }
    return H;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <filename>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Failed to open the file." << std::endl;
        return 1;
    }

    std::map<unsigned char, int> symbols_frequency;  // Mapa przechowująca częstości poszczególnych symboli
    std::map<unsigned char, std::map<unsigned char, int>> cond_freq;  // Mapa przechowująca warunkowe częstości symboli
    int num_of_symbols = 0;  // Liczba wszystkich symboli w pliku
    unsigned char prev_symbol = 0;  // Poprzedni symbol dla obliczenia warunkowych częstości
    cond_freq[prev_symbol] = {};  // Inicjalizacja mapy warunkowych częstości dla poprzedniego symbolu

    while (true) {
        unsigned char symbol;
        if (!file.read(reinterpret_cast<char*>(&symbol), 1)) {
            break;
        }

        num_of_symbols++;

        // Aktualizacja mapy warunkowych częstości
        if (cond_freq.find(prev_symbol) == cond_freq.end()) {
            cond_freq[prev_symbol] = {};
        }

        if (cond_freq[prev_symbol].find(symbol) != cond_freq[prev_symbol].end()) {
            cond_freq[prev_symbol][symbol]++;
        } else {
            cond_freq[prev_symbol][symbol] = 1;
        }

        prev_symbol = symbol;

        // Aktualizacja mapy częstości symboli
        if (symbols_frequency.find(symbol) != symbols_frequency.end()) {
            symbols_frequency[symbol]++;
        } else {
            symbols_frequency[symbol] = 1;
        }
    }

    // Obliczenie entropii i warunkowej entropii
    double ent = entropy(symbols_frequency, num_of_symbols);
    double cond_ent = cond_entropy(cond_freq, symbols_frequency, num_of_symbols);

    // Wyświetlenie wyników
    std::cout << "Entropy: " << ent << std::endl;
    std::cout << "Conditional Entropy: " << cond_ent << std::endl;
    std::cout << "Absolute Difference: " << fabs(cond_ent - ent) << std::endl;

    file.close();

    return 0;
}
