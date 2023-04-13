/*********************************************
 * OPL 22.1.0.0 Model
 * Author: doria
 * Creation Date: 27 sept. 2022 at 16:17:18
 *********************************************/

//Indices
 int nbparcel=...;
 range S=1..nbparcel;
 range S1=S;
 
 int nbstation=...;
 range N=1..nbstation;
 int nbAGV=...;
 range R=1..nbAGV;
 int nbdest=...;
 range D=1..nbdest;

 
 range S0=1..nbparcel+1;
 range Sbar=1..nbparcel+1;
 int M=...;
 
 
 
 //Parametres
 int a[S][S]=...;
 int b[S]=...;
 float c1[R][N]=...;
 float c2[N][S]=...;
 float c3[N]=...;
 float g[S]=...;
 float t=...; 
 
 
 //Variables
 dvar boolean alph[N][D];
 dvar boolean beta[S0][Sbar][R];
 dvar boolean epsi[S][R];
 dvar float+ gamm[S][R];
 dvar float+ delt[S][R];
 dvar float+ omeg[R];
 
 //Fonction objectif - minimisation du plus grand temps de fonction des AGV parmi la flotte disponible
 minimize 
 	max(r in R) omeg[r];
 	
 //Contraintes
 subject to{
 //(2) - assignement des destinations aux stations 
 	forall(d in D)
   	{
     sum (n in N) alph[n][d]==1;
   	}
   	
 //(3) - assignement des stations aux destinations 
 	forall(n in N)
 	  {
 	    sum (d in D)alph[n][d]<=1;
 	  }
 	  
 //(4) - contrainte de précédence pour le traitement des colis
 	forall (sprim in S)
 	  {
 	    forall(r in R)
 	      {
 	       	sum (s in S0) beta[s][sprim][r]==epsi[sprim][r];
 	       	sum (s in Sbar) beta[sprim][s][r]==epsi[sprim][r];
 	      }
 	  }
  
 //(5) - contrainte sur l'entree et la sortie des AGV du parking
 		forall(r in R)
 	    {
 	       sum (s in S) beta[nbparcel+1][s][r]== 1;
 	       sum (s in S) beta[s][nbparcel+1][r]==1;
 	     }
 
 
 //(6) - contraintes pour sous-tours
 	forall (s1 in S1: 2<=card(S1)<=card(S)-1)
 	  {
 	    forall(r in R)
 	      {
 	    	sum (s in S1: 2<=card(S1)<=card(S)-1)sum(sprim in S1: 2<=card(S1)<=card(S)-1)beta[s][sprim][r]<=card(S1);
          } 	    
  } 
  	  
 
 //(7) - contrainte d'unicite de traitement des colis
 		forall(sprim in S)
         {
              	sum(r in R) sum(s in S0) beta[s][sprim][r]==1;
        		sum(r in R) sum(s in Sbar) beta[sprim][s][r]==1;
         }
           
 //8 - contrainte de temps sur l'arrivee de l'AGV pour le traitement du colis
        forall (s in S)
         {
           forall(r in R)
             {
               gamm[s][r] >= sum(n in N) c1[r][n]*alph[n][b[s]] + M*(beta[nbparcel+1][s][r]-1);
             }
         }
      
 //9  - contrainte de temps sur l'arrivee de l'AGV pour le traitement du colis
       forall (s, sprim in S)
         {
           forall(r in R)
             {
               gamm[sprim][r] <= delt[s][r] + t + sum(n in N)(c2[n][s]*alph[n][b[s]]) + sum(n in N)(c2[n][s]*alph[n][b[sprim]]) + M*(1-beta[s][sprim][r]);
             }
         }
  
  //10 - contrainte de temps sur l'arrivee de l'AGV pour le traitement du colis
       forall (s, sprim in S)
         {
           forall(r in R)
             {
               gamm[sprim][r] >= delt[s][r] + t + sum(n in N) c2[n][s]*alph[n][b[s]] + sum(n in N) c2[n][s]*alph[n][b[sprim]] - M*(1-beta[s][sprim][r]);
             }
         }        
       
        
 //11 - contrainte de precedence sur la manipulation des colis par l'AGV
       forall (s, sprim in S : s!=sprim)
         {
           forall(r, rprim in R )
             {
               delt[sprim][rprim] >= delt[s][r] + t - M*(3-a[s][sprim]- sum(s1 in S0)beta[s1][s][r] - sum(s1 in Sbar) beta[sprim][s1][rprim]);
             }
         }

 //12 - contrainte de temps pour la prise en main du colis par l'AGV
       forall (s in S)
         {
           forall(r in R)
             {
               gamm[s][r] <= delt[s][r];
             }
         }
  
  //13 - contrainte de temps sur l'arrivee de l'AGV a la station de prelevement
       forall (s in S)
         {
           forall(r in R)
             {
               delt[s][r] <= M*epsi[s][r];
             }
         }
    
  //14 - contrainte de disponibilite de colis
       forall (s in S)
         {
           forall(r in R)
             {
               delt[s][r] >= g[s] + sum(n in N) c3[n]*alph[n][b[s]] + M*(epsi[s][r]-1);
             }
         }
  //15 - contrainte de calcul de l'instant de fin de travail de l'AGV
       forall (s in S)
         {
           forall(r in R)
             {
               omeg[r] >= delt[s][r] + t + sum(n in N) c2[n][s]*alph[n][b[s]];
             }
         }
  //16 - declaration des variables booléeenes : inutile ici car deja declarees
      
  //17 - declaration des variables positives
       forall (s in S)
         {
           forall(r in R)
             {
              gamm[s][r] >= 0;
              delt[s][r] >= 0;
              }
         }
 
 
}

//ecriture de la fonction objectif pour l'executable

execute write {
 var f2 = new IloOplOutputFile("solution.dat", false);
 var maximum = 0.0;
 for(var r in R) {
   if(omeg[r] > maximum) {
     maximum = omeg[r];
   }
 }
 f2.writeln(maximum);
 f2.close();
}