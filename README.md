# QPY animáció szerkesztő
A **QPY** egy LED fal animáció szerkesztő Python3 alkalmazás, amely a [Schönherz QPA](https://hu.wikipedia.org/wiki/Sch%C3%B6nherz_Qpa) Mátrix eseményére lett létrehozva. Az eseményről a www.oriaskijelzo.hu oldalon olvashatsz. 

[![Schönherz Mátrix 2017 | Drónfelvétel [4K]](http://img.youtube.com/vi/1sqLbh-WmbM/maxresdefault.jpg)](https://www.youtube.com/watch?v=1sqLbh-WmbM "Schönherz Mátrix 2017 | Drónfelvétel [4K]")

# Tartalom

1. [Installálás](#installálás)
2. [Szerkesztés](#szerkesztés)
3. [Exportálás](#exportálás)
4. [Várható funkciók](#várható-funkciók)
	
## Installálás
A fájlok között nincs futtatható **exe** csak egy *editor.pyw* fájl. A futtatáshoz szükség van [Python3.6+](https://www.python.org/downloads/) környezetre (Windows, MacOs X és Linux alatt is elérhető). Ezen felül az alábbi csomagok telepítésére van még szükség (Windows alatt írd be ezeket a parancssorban. MacOs X és Linux alatt lehet, hogy elé kell írnod, hogy "sudo"):
```python
pip3 install asynchio
pip3 install tkinter
pip3 install pygame
```
A szükséges könyvtárak telepítése után a szerkesztő python (\*.py vagy \*.pyw) fájljai futtathatóvá vállnak, dupla kattintással, vagy szintén parancssorból:
```python
> python editor.pyw
```

## Szerkesztés
Az eszköztár eszközeinek segítségével a színpadra és az előnézeti ablakra is lehet rajzolni. A rajzok a kijelölt réteg, kijelölt képkockáján belül jelennek meg. Rajzolni az egér bal gombjával, törölni a jobb gombjával lehet. 

![pencil tool](images/pencil.png) ceruza eszköz: bal egérgombbal rajzolni, jobbal törölni tudsz

![line tool](images/line.png) vonal eszköz: bal egérgombbal vonalat rajzolni, jobbal vonal alakban törölni lehet felengedés után

![rectangle tool](images/rectangle.png) négyszög eszköz: bal egérgombbal négyszöget rajzolni, jobbal négyszög alakban törölni lehet felengedés után

![fill tool](images/fill.png) festékesvödör eszköz: bal egérgombbal azonos színű területet átszínezni, jobbal azonos színű területet törölni lehet

![picker tool](images/picker.png) színválasztó eszköz: bal egérgombbal adott terület színét lehet felvenni a kijelölt szín helyére (az előnézeti képen minden szintet figyelembe vesz, a szerkesztő felületen csak az aktuális réteg pixeleit)

![zoom tool](images/zoom.png) nagyító eszköz: bal egérgombbal a szerkesztő felülletet nagyítani, jobbal kicsinyíteni lehet (előnézeti képen nincs hatása)

Mozgatni rajzot a nyilakkal és a transzformációs menü mozgatási parancsaival lehet. A transzformációk között elérhető tükrözés és forgatás is. A szerkesztés megkönnyítésére a legtöbb funkcióhoz elérhetők billentyűparancsok is. 

Ha esetleg idén is tetriszt, snake-et, nyan catet vagy scrollozó csapatnevet akarnál rakni az animációdba, kérd meg egy másik csapattársadat, hogy készítsen helyetted animációt.

## Exportálás
A szerkesztő fájljai (\*.qpy) eltérnek az eddig használt *AnimEditor2012* fájljaitól (\*.qp4). A QPA FTP-re való feltöltéshez először exportálni kell a kész animációt, a formátumok közötti átkonvertáláshoz. Az exportálás után létrejövő fájl már megnyitható a régi szerkesztőben is és feltölthető a QPA FTP-re. 

## Várható funkciók
A QPY animáció szerkesztő jelenleg csak **alfa teszt sátdiumban van** a legtöbb funkciója így még nem elérhető. Az újabb funkciókat folyamatosan adjuk hozzá az alkalmazáshoz. 

Mivel csak házon bleül tudtuk tesztelni, előfordulhatnak nem várt hibák. Ajánlott a gyakori mentés! Amennyiben valamiért túlságosan lassúvá válik az alkalmazás és csak rövidebb animációkat tudsz vele létrehozni a gépeden, exportáld ki a rövidebb animációkat és vágd össze őket egy \*.qp4 LUA kóddá az *AniimEditor2012* szerkesztőhöz. 

*Minden visszajelzést és segítséget szívesen fogadunk az alkalmazással kapcsolatban!*