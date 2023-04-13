# Projet CL02

L'objectif de ce projet est d'optimiser un système de tri vertical. L'optimisation se fait avec deux méthodes, une méthode exacte (modèle linéaire), et une métaheuristique (optimisation par essaims particulaires ou PSO).

Auteurs : Simon BAYLE, Hugo BERSON, Dorian BOCK, Lisa GINISTY, Adrien TOURNIER.

Date : Automne 2022

## Préparation

* Installer python (64 bits) ici : https://www.python.org/downloads/
* Lancer install.bat pour créer l'environnement virtuel avec pipenv et installer les dépendances.
* Ce projet requiert que CPLEX soit installé sur le PC.

## Version exacte

L'algorithme lui-même est contenu dans le fichier `exacte.py`.

Pour le lancer :
* Avec pipenv en double cliquant sur le script `exacte.bat`
* En construisant un exécutable en double cliquant sur le script `exacte_build_exe.bat`. Cela créera un dossier `exacte_exe` avec un exécutable à l'intérieur. Ce dossier peut être déplacé n'importe où sur toute machine Windows 64 bits, il suffit ensuite de lancer le fichier `exacte.exe` contenu à l'intérieur.


## Version PSO

L'algorithme lui-même est contenu dans le fichier `pso.py`.

Pour le lancer :
* Avec pipenv en double cliquant sur le script `pso.bat`
* En construisant un exécutable en double cliquant sur le script `pso_build_exe.bat`. Cela créera un dossier `pso_exe` avec un exécutable à l'intérieur. Ce dossier peut être déplacé n'importe où sur toute machine Windows 64 bits, il suffit ensuite de lancer le fichier `exacte.exe` contenu à l'intérieur.

# CPLEX

Les modèles CPLEX (pour la méthode exacte et pso) sont présents dans le dossier `CPLEX`. Ce dossier peut être directement ouvert dans CPLEX (des configurations d'exécutions sont déjà créées).