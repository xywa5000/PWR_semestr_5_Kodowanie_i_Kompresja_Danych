import math
import argparse

KOD_NYT = 'NYT'

class Wezel:
    def __init__(self, rodzic, waga=0, lewy=None, prawy=None, znak=''):
        self._rodzic = rodzic
        self._waga = waga
        self._lewy = lewy
        self._prawy = prawy
        self._znak = znak

    @property
    def rodzic(self):
        return self._rodzic
    
    @rodzic.setter
    def rodzic(self, nowy_rodzic):
        self._rodzic = nowy_rodzic

    @property
    def waga(self):
        return self._waga
    
    @waga.setter
    def waga(self, nowa_waga):
        self._waga = nowa_waga

    @property
    def lewy(self):
        return self._lewy
    
    @lewy.setter
    def lewy(self, nowy_lewy):
        self._lewy = nowy_lewy

    @property
    def prawy(self):
        return self._prawy
    
    @prawy.setter
    def prawy(self, nowy_prawy):
        self._prawy = nowy_prawy

    @property
    def znak(self):
        return self._znak
    
    @znak.setter
    def znak(self, nowy_znak):
        self._znak = nowy_znak

    def czy_lisc(self):
        return self._lewy is None and self._prawy is None


class KodowanieHuffmana:
    def __init__(self):
        self._NYT = Wezel(None, 0, znak=KOD_NYT)
        self._korzen = self._NYT
        self._wszystkie_znaki = [None] * 256
        self._posortowane_wezly = []

    def _czy_juz_dodany(self, znak):
        if ord(znak) > 255:
            raise Exception('Znak poza zakresem')

        return self._wszystkie_znaki[ord(znak)] is not None

    def _zarejestruj_znak(self, znak):
        obecny = self._wszystkie_znaki[ord(znak)]

        if obecny is None:
            nyt = self._NYT
            stary_rodzic_nyt = nyt.rodzic

            nowy_rodzic = None

            if stary_rodzic_nyt is None:
                self._korzen = Wezel(None, lewy=nyt, prawy=None)
                nyt.rodzic = self._korzen
                nowy_rodzic = self._korzen
            else:
                nowy_rodzic = Wezel(stary_rodzic_nyt, waga=1, lewy=nyt, prawy=None)
                stary_rodzic_nyt.lewy = nowy_rodzic
                nyt.rodzic = nowy_rodzic

            nowy_wezel = Wezel(nowy_rodzic, waga=1, znak=znak)
            nowy_rodzic.prawy = nowy_wezel

            self._posortowane_wezly.extend([nowy_wezel, nowy_rodzic])
            self._wszystkie_znaki[ord(znak)] = nowy_wezel

            obecny = nowy_rodzic.rodzic

        while obecny is not None:
            do_zamiany = next(w for w in self._posortowane_wezly if w.waga == obecny.waga)
            if obecny is not do_zamiany and obecny is not do_zamiany.rodzic and do_zamiany is not obecny.rodzic:
                self._zamien_wezly(obecny, do_zamiany)

            obecny.waga += 1
            obecny = obecny.rodzic

    def _zamien_wezly(self, jeden, dwa):
        indeks_jeden = self._posortowane_wezly.index(jeden)
        indeks_dwa = self._posortowane_wezly.index(dwa)

        self._posortowane_wezly[indeks_jeden], self._posortowane_wezly[indeks_dwa] = \
            self._posortowane_wezly[indeks_dwa], self._posortowane_wezly[indeks_jeden]

        rodzic = jeden.rodzic
        jeden.rodzic = dwa.rodzic
        dwa.rodzic = rodzic

        if jeden.rodzic.lewy is dwa:
            jeden.rodzic.lewy = jeden
        else:
            jeden.rodzic.prawy = jeden

        if dwa.rodzic.lewy is jeden:
            dwa.rodzic.lewy = dwa
        else:
            dwa.rodzic.prawy = dwa

    def _generuj_kod_wezla(self, _wezel):
        kod = ''
        wezel = _wezel
        while wezel.rodzic is not None:
            rodzic = wezel.rodzic
            kod += '0' if rodzic.lewy is wezel else '1'
            wezel = rodzic
        return kod[::-1]

    def _generuj_kod(self, znak):
        if self._czy_juz_dodany(znak):
            wezel = self._wszystkie_znaki[ord(znak)]
            return self._generuj_kod_wezla(wezel)
        else:
            return self._generuj_kod_wezla(self._NYT) + bin(ord(znak))[2:].zfill(8)

    def koduj_pojedynczy_znak(self, znak):
        kod = self._generuj_kod(znak)
        self._zarejestruj_znak(znak)
        return kod

    def dekoduj(self, zakodowane):
        wynik = []
        pierwszy_znak = chr(int(zakodowane[:8], 2))
        wynik.append(ord(pierwszy_znak))
        self._zarejestruj_znak(pierwszy_znak)

        wezel = self._korzen
        i = 8
        while i < len(zakodowane):
            obecny_bit = zakodowane[i]

            if obecny_bit == '0':
                wezel = wezel.lewy
            elif obecny_bit == '1':
                wezel = wezel.prawy
            else:
                raise Exception("Nieprawidłowy kod Huffmana (nie jest to 0 ani 1)")

            znak = wezel.znak

            if znak:
                if znak == KOD_NYT:
                    znak = chr(int(zakodowane[i+1:i+9], 2))
                    i += 8
                wynik.append(ord(znak))
                self._zarejestruj_znak(znak)
                wezel = self._korzen

            i += 1

        return wynik

    def srednia_dlugosc_kodu(self):
        dlugosci = []
        liczba_znakow = 0

        for znak in self._wszystkie_znaki:
            if znak is None:
                continue
            dlugosci.append(len(self._generuj_kod_wezla(znak)))
            liczba_znakow += 1

        return sum(dlugosci) / liczba_znakow

    def entropia(self):
        wynik = 0

        for znak in self._wszystkie_znaki:
            if znak is None:
                continue
            wynik += znak.waga * (-math.log2(znak.waga))

        wynik /= self._korzen.waga

        return wynik + math.log2(self._korzen.waga)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kodowanie Huffmana')
    parser.add_argument('tryb', choices=['koduj', 'dekoduj'], help='Tryb: koduj lub dekoduj')
    parser.add_argument('plik_wejsciowy', help='Ścieżka do pliku wejściowego')
    parser.add_argument('plik_wyjsciowy', help='Ścieżka do pliku wyjściowego')
    args = parser.parse_args()

    huffman = KodowanieHuffmana()

    if args.tryb == "dekoduj":
        with open(args.plik_wyjsciowy, "wb+") as fo:
            with open(args.plik_wejsciowy, "rb") as fi:
                bity_wejsciowe = ""
                tmp = fi.read(1)
                padding_uzyty = ord(tmp)

                tmp = fi.read(1)
                while tmp:
                    tmp = ord(tmp)
                    for i in range(0, 8):
                        bity_wejsciowe += '1' if (tmp >> (7-i)) & 0b1 else '0'
                    tmp = fi.read(1)

                bity_wejsciowe = bity_wejsciowe[:-padding_uzyty]

                bajty = huffman.dekoduj(bity_wejsciowe)
                for b in bajty:
                    fo.write(b.to_bytes(1, byteorder="big"))

    else:  # args.tryb == "koduj"
        with open(args.plik_wyjsciowy, "wb+") as fo:
            with open(args.plik_wejsciowy, "rb") as fi:
                wyjscie = ""
                bajt = fi.read(1)
                liczba_znakow = 1
                while bajt:
                    wyjscie += huffman.koduj_pojedynczy_znak(bajt)
                    bajt = fi.read(1)
                    liczba_znakow += 1

                wyjscie_bajty = []
                padding_uzyty = 0
                for i in range(0, math.ceil(len(wyjscie)/8)):
                    tmp = wyjscie[(i*8):((i+1)*8)]
                    if len(tmp) != 8:
                        padding_uzyty = 8-len(tmp)
                        tmp += "0" * padding_uzyty
                    tmp = int(tmp, 2)
                    wyjscie_bajty.append(tmp)

                wyjscie_bajty = [padding_uzyty] + wyjscie_bajty

                for b in wyjscie_bajty:
                    fo.write(b.to_bytes(1, byteorder='big'))

                print("Średnia długość kodu:", huffman.srednia_dlugosc_kodu())
                print("Współczynnik kompresji:", liczba_znakow/len(wyjscie_bajty))
                print("Entropia:", huffman.entropia())
