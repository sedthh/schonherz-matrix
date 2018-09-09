# QPY animáció szerkesztő
A **QPY** egy LED fal animáció szerkesztő Python3 alkalmazás, amely a [Schönherz QPA](https://hu.wikipedia.org/wiki/Sch%C3%B6nherz_Qpa) Mátrix eseményére lett létrehozva. Az eseményről a www.oriaskijelzo.hu oldalon olvashatsz. 

# Tartalom

1. [Installálás](#installálás)
2. [Szerkesztés](#szerkesztés)
3. [Exportálás](#exportálás)
4. [Várható funkciók](#várható-funkciók)
	
## Installálás
A futtatáshoz szükség van [Python3.6+](https://www.python.org/downloads/) környezetre (Windows, MacOs X és Linux alatt is elérhető). Ezen felül az alábbi csomagok telepítésére van még szükség:
```python
pip install asynchio
pip install pygame
pip install tkinter
```
A szükséges könyvtárak telepítése után a szerkesztő python (\*.py vagy \*.pyw) fájljai futtathatóvá vállnak, dupla kattintással, vagy parancssorból:
```python
> python editor.pyw
```

## Szerkesztés
Az eszköztár eszközeinek segítségével a színpadra és az előnézeti ablakra is lehet rajzolni. A rajzok a kijelölt réteg, kijelölt képkockáján belül jelennek meg. Rajzolni az egér bal gombjával, törölni a jobb gombjával lehet. 

A szerkesztés megkönnyítésére elérhetőek billentyűparancsok a legtöbb funkcióhoz. 

## Exportálás
A szerkesztő fájljai (\*.qpy) eltérnek az eddig használt *AnimEditor2012* fájljaitól (\*.qp4). A QPA FTP-re való feltöltéshez először exportálni kell a kész animációt, a formátumok közötti átkonvertáláshoz. Az exportálás után létrejövő fájl már megnyitható a régi szerkesztőben is és feltölthető a QPA FTP-re. 

## Várható funkciók
A QPY animáció szerkesztő jelenleg csak **alfa teszt sátdiumban van** a legtöbb funkciója így még nem elérhető. Az újabb funkciókat folyamatosan adjuk hozzá az alkalmazáshoz. Ajánlott a gyakori mentés. 

Minden visszajelzést és segítséget szívesen fogadunk az alkalmazással kapcsolatban!
