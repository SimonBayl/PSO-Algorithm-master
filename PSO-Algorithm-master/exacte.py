import os
import random
import subprocess
import numpy as np
import codecs
import time

random.seed()

# Saisie des parametres par l'utilisateur
parcels_count = int(input("Entrez le nombre de cartons (S) : "))
stations_count = int(input("Entrez le nombre de picking stations (N) : "))
AGVs_count = int(input("Entrez le nombre d'AGV (R) : "))
destinations_count = int(input("Entrez le nombre de destinations (D) : "))

# Creation des listes relatives a nos parametres
parcels = list(range(1, parcels_count+1))
stations = list(range(1, stations_count+1))
AGVs = list(range(1, AGVs_count+1))
destinations = list(range(1, destinations_count+1))

# Generation des parametres fixes du fichier de donnees CPLEX
base_parameters = f"nbparcel = {parcels_count};\nnbstation = {stations_count};\nnbAGV = {AGVs_count};\nnbdest = {destinations_count};"

# Generation du parametre a
destination_par_colis = {}
for colis in parcels:
    destination_par_colis[colis] = random.choice(destinations)
colis_est_juste_avant = {}
stra = "["
for colis_avant in parcels:
    colis_est_juste_avant[colis_avant] = {}
    stra += "["
    for colis_apres in parcels:
        destination_colis_avant = destination_par_colis[colis_avant]
        colis_est_juste_avant[colis_avant][colis_apres] = int(
            destination_colis_avant == destination_par_colis[colis_apres] and
            colis_apres == colis_avant + 1
        )
    stra += ", ".join(map(str, colis_est_juste_avant[colis_avant].values())) + "],"
stra = stra[:-1] + "]"

# Generation des autres parametres
donnees_fixes = f"""{base_parameters}
b = [{", ".join(map(str, destination_par_colis.values()))}]; // Destinations des colis
M = 5000000;
t = 5; // Durée necessaire au bras mécanique
c1 = [[{"], [".join([", ".join([str(round(random.uniform(90, 120), 2)) for i in range(stations_count)]) for j in range(AGVs_count)])}]]; // Temps de trajet de l'AGV jusqu'à la picking station
c2 = [[{"], [".join([", ".join([str(round(random.uniform(60, 90), 2)) for i in range(parcels_count)]) for j in range(stations_count)])}]]; // Temps necessaire à l'AGV pour acheminer le colis à la remorque
c3 = [{", ".join([str(round(random.uniform(30, 60), 2)) for i in range(stations_count)])}]; // Temps necessaire au convoyeur pour acheminer le colis à la picking station
g = [{", ".join([str(round((8 / 27) * i, 2)) for i in range(1, parcels_count + 1)])}]; // Moment d'arrivée du colis dans le système
a = {stra}; // Binaire activé si le colis s' est arrive juste après dans le système et qu'ils ont la même destination
"""

# Chemin d'accès à la solution et au fichier de données
data_path = "CPLEX/Exacte.dat"
solution_path = "CPLEX/solution.dat"

# On efface les fichiers précédents s'ils existent
if os.path.isfile(data_path):
    os.remove(data_path)
if os.path.isfile(solution_path):
    os.remove(solution_path)
# On ouvre le fichier de données et on écrit les données dedans
with codecs.open(data_path, "w", "utf-8") as fichierDonnees:
    fichierDonnees.write(donnees_fixes)

print("\n\nFichier de données écrit")
print("Lancement de CPLEX")
# Calcule et affiche la date de départ
start_time = time.time()
print(f"Début le {time.strftime('%d/%m/%Y à %H:%M:%S', time.gmtime(start_time))} UTC")
# Lancement de CPLEX
subprocess.run(["oplrun", "CPLEX/Exacte.mod", data_path], stdout=subprocess.PIPE)

# Récuperation de la valeur objectif
with open(solution_path) as solution_file:
    result_score = float(solution_file.read())

# Affiche le résultat (score et valeurs de alpha, beta, epsilon),
# affiche la date de fin et calcule la durée d'execution
print("\n\n=== RESULTAT ===")
end_time = time.time()
print(f"Fin le {time.strftime('%d/%m/%Y à %H:%M:%S', time.gmtime(end_time))} UTC")
duration = end_time - start_time
print(f"Durée d'exécution de l'algorithme: {duration} secondes")
print(f"Durée maximale mise par un AGV pour traiter tous ses colis : {result_score} secondes")
input("\nAppuyez sur entrée pour terminer...")
