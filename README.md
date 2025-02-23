# Implementare-Switch

Cerintele rezolvate: 1, 2, 3

Cerinta1:
La prima cerinta la cea cu procesul de comutare am facut exact ceea ce ati descris voi pe ocw in pseudocul de cod. Am verificat daca adresa mac destinatara este diferita de adresa de brodcast. Daca adresa dst_mac este diferita de cea de  broadcast am vericat daca
adresa dst_mac se afla in tabela de comutare cu MAC_TABLE daca da trimiteam pachetul direct, daca nu trimiteam pachetul la celelate interfete, mai putin la adresa src. In cazul in care adresa dst_mac este adresa de broadcast, atunci trimitem pachetul la celelalte interfete mai putin adresa src_mac.

Cerinta2:
La cerinta nr 2, am vericat ca daca pe portul de unde primim informatia este de tip access si noi vrem sa trimitem pe un port de tip trunk atunci va trebui sa adaugam headerul 802.1Q, daca vrem trimitem pe un trimitem pe un port de tip access atunci nu trebuie sa adaugam campul 802.1Q. Daca portul de unde primim informatia este tip trunk si vrem sa trimitem pe unul de tip access, atunci vom trimitem fara campul 802.1Q, iar vrem sa trimitem pe un port de tip trunk atunci vom trimitem si cu campul 802.1Q. De asemenea ca sa fac deosebire dintee porturi m-am folosit de cele 3 fisiere puse la dispozitie si creat un vector unde sa retin vlan_id. Daca interfata era acccess, atunci bagam in vector valorea intreaga a vlan-id. Daca interfata era trunk, atunci in bagam in vector string-ul "TRUNK".

Cerinta3:
La cerinta3, pentru stp am implementat pseudocoruile alea cu initialize, sending_bdpu, receive_bdpu. Am verificat daca verificat daca primeam un pachet de tip bpdu sau ethernet, dupa dest_mac. Si m-am folosit de cerintele 1 si 2. Adica cand trimiteam pachetul pentru dest_mac sau pentru celelalte interfete inafara de src_mac, vericam tabela de vlan-uri si de asemenea, daca portul interfetei pe care vrem sa trimitem este de tip listening. 
