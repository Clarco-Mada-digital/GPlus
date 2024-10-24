-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: localhost    Database: gplus
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `personnel_employee`
--

DROP TABLE IF EXISTS `personnel_employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_employee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `numero_telephone` varchar(15) NOT NULL,
  `date_naissance` date NOT NULL,
  `sexe` varchar(10) NOT NULL,
  `ville` varchar(100) NOT NULL,
  `adresse` varchar(100) NOT NULL,
  `statut_matrimonial` varchar(11) NOT NULL,
  `nationalite` varchar(100) NOT NULL,
  `pays` varchar(100) NOT NULL,
  `code_postal` varchar(10) NOT NULL,
  `date_embauche` date NOT NULL,
  `type_salarie` varchar(20) NOT NULL,
  `statut` varchar(10) NOT NULL,
  `type_contrat` varchar(10) DEFAULT NULL,
  `lettre_motivation` varchar(100) DEFAULT NULL,
  `lettre_introduction` varchar(100) DEFAULT NULL,
  `bulletin_salaire` varchar(100) DEFAULT NULL,
  `curriculum_vitae` varchar(100) DEFAULT NULL,
  `id_facebook` varchar(150) DEFAULT NULL,
  `id_skype` varchar(150) DEFAULT NULL,
  `id_github` varchar(150) DEFAULT NULL,
  `id_linkedln` varchar(150) DEFAULT NULL,
  `jours_conge_annuels` int unsigned NOT NULL,
  `jours_conge_formation` int unsigned NOT NULL,
  `jours_conge_maternite` int unsigned NOT NULL,
  `jours_conge_paternite` int unsigned NOT NULL,
  `jours_conge_exceptionnel` int unsigned NOT NULL,
  `jours_conge_obligatoire` int unsigned NOT NULL,
  `competence_id` bigint DEFAULT NULL,
  `departement_id` bigint DEFAULT NULL,
  `groupe_id` int DEFAULT NULL,
  `user_id` bigint DEFAULT NULL,
  `poste_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `personnel_employee_competence_id_ace86362` (`competence_id`),
  KEY `personnel_employee_departement_id_2a7662bc` (`departement_id`),
  KEY `personnel_employee_groupe_id_888dd46d` (`groupe_id`),
  KEY `personnel_employee_poste_id_47683504` (`poste_id`),
  CONSTRAINT `personnel_employee_chk_1` CHECK ((`jours_conge_annuels` >= 0)),
  CONSTRAINT `personnel_employee_chk_2` CHECK ((`jours_conge_formation` >= 0)),
  CONSTRAINT `personnel_employee_chk_3` CHECK ((`jours_conge_maternite` >= 0)),
  CONSTRAINT `personnel_employee_chk_4` CHECK ((`jours_conge_paternite` >= 0)),
  CONSTRAINT `personnel_employee_chk_5` CHECK ((`jours_conge_exceptionnel` >= 0)),
  CONSTRAINT `personnel_employee_chk_6` CHECK ((`jours_conge_obligatoire` >= 0))
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_employee`
--

LOCK TABLES `personnel_employee` WRITE;
/*!40000 ALTER TABLE `personnel_employee` DISABLE KEYS */;
INSERT INTO `personnel_employee` VALUES (1,'ZOUBERY','Jaotiana Donaldo','photos/default.png','dzoubery@gmail.com','0325005174','2000-08-24','Masculin','Antsiranana','CHU Place Kabary','Célibataire','Malagasy','Madagascar','201','2024-10-10','salarie','T','CDI','fichier/payrolls_2_07KrW64.pdf','fichier/fiche_de_paie_de_ZOUBERY_Jaotiana_Donaldo_Jannvier-_3.pdf','fichier/Cahier_de_charge.docx_3.pdf','fichier/payrolls_2_3ZksNlO.pdf','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/',15,12,105,3,10,15,1,1,1,2,1),(2,'BEZARA','Kemuel Kelub','photos/WhatsApp_Image_2024-09-27_at_10.54.50.jpeg','kemuelebezara205@gmail.com','0325005173','2002-10-14','Masculin','Antsiranana','CHU Place Kabary','Célibataire','Malagasy','Madagascar','201','2024-10-14','direction','T','CDI','fichier/payrolls.pdf','fichier/fiche_de_paie_de_ZOUBERY_Jaotiana_Donaldo_Jannvier.pdf','','','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/',15,12,105,3,10,15,1,1,2,3,1),(3,'ZANDRY','Zepelin','photos/defaut.png','Zepelin19@gmail.com','0325005174','2002-10-17','Masculin','Antsiranana','CHU Place Kabary','Célibataire','Malagasy','Madagascar','201','2024-10-17','direction','C','Aucun','','','','','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/',15,12,105,3,10,15,1,3,2,4,2),(4,'MARC','Odilon','photos/defaut.png','ODddaaaaaaaaaaaa@gmail.com','0325005174','2000-08-24','Masculin','Antsiranana','CHU Place Kabary','Célibataire','Malagasy','Madagascar','201','2024-10-17','salarie','T','CDD','fichier/MCD.xlsx','','','','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/','https://chatgpt.com/',15,12,105,3,10,15,1,1,1,5,3),(5,'PATRON','Clarko','photos/defaut.png','','','2002-11-30','Masculin','','','Célibataire','','','','2024-10-22','','T','CDI','','','','',NULL,NULL,NULL,NULL,15,12,105,3,10,15,NULL,1,NULL,NULL,1);
/*!40000 ALTER TABLE `personnel_employee` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-10-23 10:58:24
