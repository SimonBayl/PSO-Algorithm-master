import os
import random
import subprocess
import numpy as np
import codecs
import time
import statistics
from matplotlib import pyplot as plt

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

# Coefficients d'accélération
c1 = 0.638
c2 = 0.638

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


def get_closest_value(values, target):
    """
    Permet de recuperer la valeur la plus proche fournie en parametre dans un tableau de valeurs

    exemple : get_closest_value([1, 2, 3], 2.4) renvoie 2

    :param values: tableau de valeurs
    :param target: valeur cible
    :return: la valeur dans le tableau values la plus proche de target
    """
    # Initialisation de la valeur la plus proche
    closest = float("inf")
    closest_value = None

    # Parcours des valeurs de la liste
    for value in values:
        # Calcul de la différence entre la valeur courante et la valeur cible
        diff = abs(target - value)

        # Si la différence est plus petite que la différence la plus proche actuelle,
        # on met à jour la valeur la plus proche et la différence la plus proche
        if diff < closest:
            closest = diff
            closest_value = value

    # Retour de la valeur la plus proche
    return closest_value


def get_alpha_beta_epsilon(position):
    """
    A partir d'une position, retourne les valeurs CPLEX de alpha, beta et epsilon

    :param position: position sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination
     et comme valeur les tableaux correspondants
    :return: tuple de tableaux numpy (alpha, beta, epsilon)
    """

    # Calcul de beta
    beta = np.zeros((parcels_count + 1, parcels_count + 1, AGVs_count), dtype=int)
    for AGV in AGVs:
        parcels_for_current_AGV = [parcel for parcel in parcels if position["AGV_for_parcel"][parcel - 1] == AGV]
        parcels_for_current_AGV.sort()
        if len(parcels_for_current_AGV) == 0:
            beta[parcels_count + 1 - 1][parcels_count + 1 - 1][AGV - 1] = True
        else:
            beta[parcels_count + 1 - 1][parcels_for_current_AGV[0] - 1][AGV - 1] = True
            beta[parcels_for_current_AGV[len(parcels_for_current_AGV) - 1] - 1][parcels_count + 1 - 1][AGV - 1] = True
            i = 1
            while i < len(parcels_for_current_AGV):
                beta[parcels_for_current_AGV[i - 1] - 1][parcels_for_current_AGV[i] - 1][AGV - 1] = True
                i += 1

    # Calcul de alpha
    alph = np.zeros((stations_count, destinations_count), dtype=int)
    for n in stations:
        for d in destinations:
            alph[n - 1, d - 1] = int(position["station_for_destination"][d - 1] == n)

    # Calcul d'epsilon
    epsi = np.zeros((parcels_count, AGVs_count), dtype=int)
    for s in parcels:
        for r in AGVs:
            epsi[s - 1, r - 1] = int(position["AGV_for_parcel"][s - 1] == r)

    return alph, beta, epsi


def objective_function(position):
    """
    A partir d'une position, renvoie la valeur de la fonction objectif

    :param position: position sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination
     et comme valeur les tableaux correspondants
    :return: La valeur de la fonction objectif (fitness) pour la position fournie
    """

    # Chemin d'accès à la solution et au fichier de données
    data_path = "CPLEX/PSO.dat"
    solution_path = "CPLEX/solution.dat"

    # On efface les fichiers précédents s'ils existent
    if os.path.isfile(data_path):
        os.remove(data_path)
    if os.path.isfile(solution_path):
        os.remove(solution_path)
    # On ouvre le fichier de données et on écrit les données dedans
    with codecs.open(data_path, "w", "utf-8") as fichierDonnees:
        fichierDonnees.write(donnees_fixes)
        alph, beta, epsi = get_alpha_beta_epsilon(position)
        newline = '\n'
        fichierDonnees.write(
            f"alph = {np.array2string(alph, separator=',', threshold=np.inf).replace(newline,'')};\nepsi = {np.array2string(epsi, separator=',', threshold=np.inf).replace(newline,'')};\nbeta = {np.array2string(beta, separator=',', threshold=np.inf).replace(newline,'')};")

    # Lancement de CPLEX
    subprocess.run(["oplrun", "CPLEX/PSO.mod", data_path], stdout=subprocess.PIPE)

    # Récuperation de la valeur objectif
    with open(solution_path) as solution_file:
        return float(solution_file.read())


def generate_position():
    """
    Permet de générer aléatoirement une position

    :return: position sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination et
     comme valeur les tableaux correspondants
    """

    # Initalisation du dictionnaire
    position = {
        "station_for_destination": np.zeros(destinations_count),
        "AGV_for_parcel": np.zeros(parcels_count)
    }
    # Génération des valeurs pour station_for_destination
    remaining_stations = stations.copy()
    for destination in destinations:
        station = random.choice(remaining_stations)
        position["station_for_destination"][destination - 1] = station
        remaining_stations.remove(station)
    # Génération des valeurs pour AGV_for_parcel
    for parcel in parcels:
        position["AGV_for_parcel"][parcel - 1] = random.choice(AGVs)

    return position


def generate_velocity():
    """
    Permet de générer aléatoirement une vélocité

    :return: vélocité sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination et
     comme valeur les tableaux correspondants
    """
    return {"station_for_destination": np.random.rand() * len(stations), "AGV_for_parcel": np.random.rand() * len(AGVs)}


def update_velocity(velocity, position, pbest_position, gbest_position):
    """
    Calcule une nouvelle vélocité pour une position

    :param velocity: vélocité actuelle
    :param position: position actuelle
    :param pbest_position: Meilleure position pour la position fournie
    :param gbest_position: Meilleure position globale
    :return: vélocité actualisée sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et
     station_for_destination et comme valeur les tableaux correspondants
    """
    r1 = np.random.rand()  # float entre 0 et 1
    r2 = np.random.rand()  # float entre 0 et 1
    new_velocity = {"AGV_for_parcel": 0, "station_for_destination": 0}
    for key in ["AGV_for_parcel", "station_for_destination"]:
        new_velocity[key] = velocity[key] + c1 * r1 * (pbest_position[key] - position[key]) + c2 * r2 * (
                gbest_position[key] - position[key])
    return new_velocity


def update_position(position, velocity):
    """
    Calcule la nouvelle position

    :param position: position sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination
     et comme valeur les tableaux correspondants
    :param velocity: vélocité sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et station_for_destination
     et comme valeur les tableaux correspondants
    :return: position actualisée sous la forme d'un dictionnaire ayant pour clefs AGV_for_parcel et
     station_for_destination et comme valeur les tableaux correspondants
    """
    # Initialisation du dictionnaire de la nouvelle position et mise à jour des valeurs pour AGV_for_parcel
    new_position = {
        "station_for_destination": np.zeros(destinations_count),
        "AGV_for_parcel": np.around(position["AGV_for_parcel"] + velocity["AGV_for_parcel"])
    }
    # Mise à jour des valeurs de station_for_destination
    remaining_stations = stations.copy()
    for destination in destinations:
        station = get_closest_value(remaining_stations, position["station_for_destination"][destination - 1] +
                                    velocity["station_for_destination"][destination - 1])
        new_position["station_for_destination"][destination - 1] = station
        remaining_stations.remove(station)

    # Vérification des limites d'AGV_for_parcel
    for parcel in parcels:
        if new_position["AGV_for_parcel"][parcel - 1] < 1:
            new_position["AGV_for_parcel"][parcel - 1] = 1
        elif new_position["AGV_for_parcel"][parcel - 1] > len(AGVs):
            new_position["AGV_for_parcel"][parcel - 1] = len(AGVs)

    return new_position


# Définition de la fonction d'optimisation par essaim de particules
def pso(num_particles, generations_count):
    """
    Réalise l'optimisation par essaims particulaires, et affiche deux graphiques (évolution du meilleur score, et du
    score moyen par génération)

    :param num_particles: nombre de particules
    :param generations_count: nombre de génération
    :return: Un tuple (result_position, result_score) comprenant la meilleure position et le score associé pour toutes
     les générations
    """

    # Initialisation des tableaux communs à toutes les générations
    gbest_scores = []
    best_scores_per_generation = []
    mean_scores_per_generation = []

    print(f"PSO pour {generations_count} générations de {num_particles} particules/positions\n")

    # Génération aléatoire des positions initiales des particules
    print("Initialisation...")
    positions = []
    for i in range(num_particles):
        positions.append(generate_position())

    # Génération aléatoire des vitesses initiales des particules
    velocities = []
    for i in range(num_particles):
        velocities.append(generate_velocity())

    # Définition initiale des meilleures positions individuelles, stockage de valeurs pour les graphiques et l'affichage
    pbest_position = positions.copy()
    pbest_score = np.zeros(num_particles)
    scores_for_current_generation = []
    for i in range(num_particles):
        pbest_score[i] = objective_function(pbest_position[i])
        scores_for_current_generation.append(pbest_score[i])
    mean_score_for_current_generation = statistics.mean(scores_for_current_generation)
    mean_scores_per_generation.append(mean_score_for_current_generation)

    # Recherche de la meilleure position globale, stockage de valeurs pour les graphiques et l'affichage
    gbest_position = positions[0]
    gbest_score = float("inf")
    for i in range(num_particles):
        if pbest_score[i] < gbest_score:
            gbest_score = pbest_score[i]
            gbest_position = pbest_position[i]
    gbest_scores.append(gbest_score)
    best_scores_per_generation.append(gbest_score)
    best_score_for_current_generation = gbest_score

    # Boucle principale de l'algorithme
    for i in range(generations_count):
        # Affichage des statistiques (score moyen, meilleure score, meilleur score global) pour la génération précédente
        print(f"Meilleur score : {best_score_for_current_generation}")
        print(f"Score moyen : {mean_score_for_current_generation}")
        print(f"Meilleur score jusqu'à présent : {gbest_score}")

        # On affiche le numéro de la génération en cours
        print(f"\nGénération {i+1}")
        # Initialisation des valeurs spécifiques par génération
        best_score_for_current_generation = float("inf")
        scores_for_current_generation = []
        # On itére sur les particules/positions
        for j in range(num_particles):
            # Mise à jour de la vitesse des particules/positions
            velocities[j] = update_velocity(velocities[j], positions[j], pbest_position[j], gbest_position)

            # Mise à jour de la position des particules/positions
            positions[j] = update_position(positions[j], velocities[j])

            # Mise à jour des meilleures positions (individuelles et globale)
            score = objective_function(positions[j])
            scores_for_current_generation.append(score)
            if score < pbest_score[j]:
                pbest_score[j] = score
                pbest_position[j] = positions[j]
            if score < best_score_for_current_generation:
                best_score_for_current_generation = score
            # Mise à jour de la meilleure position globale
            if pbest_score[j] < gbest_score:
                gbest_score = pbest_score[j]
                gbest_position = pbest_position[j]
        # Stockage pour les graphiques et l'affichage
        gbest_scores.append(gbest_score)
        mean_score_for_current_generation = statistics.mean(scores_for_current_generation)
        mean_scores_per_generation.append(mean_score_for_current_generation)
        best_scores_per_generation.append(best_score_for_current_generation)

    # Affichage des statistiques (score moyen, meilleure score, meilleur score global) pour la dernière génération
    print(f"Meilleur score : {best_score_for_current_generation}")
    print(f"Score moyen : {mean_score_for_current_generation}")
    print(f"Meilleur score jusqu'à présent : {gbest_score}")

    # Génération des graphiques (une figure avec deux graphiques)
    fig, axs = plt.subplots(2)
    (best_score_plot, mean_score_plot) = axs
    fig.suptitle('Evolution des scores au cours des générations')
    # Insertion des données
    best_score_plot.plot(gbest_scores, label="Meilleur score jusqu'à présent")
    best_score_plot.plot(best_scores_per_generation, label="Meilleur score pour la génération")
    mean_score_plot.plot(mean_scores_per_generation, label="Score moyen de la génération")
    # Légendes
    mean_score_plot.set(xlabel="Génération")
    for ax in axs.flat:
        ax.set(ylabel="Score (secondes)")
        ax.grid(True)
        ax.legend()
    fig.show()  # Affichage du graphique
    return gbest_position, gbest_score  # Renvoi de la meilleure position trouvée et son score


def main():
    """
    Code principal, demande la saisie du nombre de particules et de générations, lance le PSO, calcule le temps d'exécution,
    affiche le résultat
    """

    # Saisie du nombre de particules/positions et du nombre de générations
    num_particules = int(input("Indiquez le nombre de particules/positions souhaitées par générations : "))
    generations_count = int(input("Indiquez le nombre de générations souhaitées : "))

    # Calcule et affiche la date de départ
    start_time = time.time()
    print(f"Début le {time.strftime('%d/%m/%Y à %H:%M:%S', time.gmtime(start_time))} UTC")

    # Lance le PSO
    result, result_score = pso(num_particules, generations_count)

    # Affiche le résultat (score et valeurs de alpha, beta, epsilon),
    # affiche la date de fin et calcule la durée d'execution
    print("\n\n=== RESULTAT ===")
    end_time = time.time()
    print(f"Fin le {time.strftime('%d/%m/%Y à %H:%M:%S', time.gmtime(end_time))} UTC")
    duration = end_time - start_time
    print(f"Durée d'exécution de l'algorithme: {duration} secondes")
    print(f"Durée maximale mise par un AGV pour traiter tous ses colis : {result_score}")
    print("\n== alpha, beta, epsilon pour la meilleure position ==")
    alph, beta, epsi = get_alpha_beta_epsilon(result)
    newline = '\n'
    print(f"alph = {np.array2string(alph, separator=',', threshold=np.inf).replace(newline,'')};\nepsi = {np.array2string(epsi, separator=',', threshold=np.inf).replace(newline,'')};\nbeta = {np.array2string(beta, separator=',', threshold=np.inf).replace(newline,'')};")
    input("Appuyez sur entrée pour terminer...")


if __name__ == "__main__":
    main()
