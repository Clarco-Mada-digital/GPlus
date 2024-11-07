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
-- Table structure for table `personnel_paie`
--

DROP TABLE IF EXISTS `personnel_paie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_paie` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `salaire_base` decimal(10,2) NOT NULL,
  `primes` decimal(10,2) NOT NULL,
  `indemnites` decimal(10,2) NOT NULL,
  `indice_anciennete` decimal(5,2) NOT NULL,
  `cotisations_salariales` decimal(10,2) NOT NULL,
  `cotisations_patronales` decimal(10,2) NOT NULL,
  `net_imposable` decimal(10,2) NOT NULL,
  `net_a_payer` decimal(10,2) NOT NULL,
  `date_paie` date NOT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `lot` date NOT NULL,
  `date_creation` datetime(6) NOT NULL,
  `exercice` varchar(50) NOT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_paie_employee_id_de02341f` (`employee_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_paie`
--

LOCK TABLES `personnel_paie` WRITE;
/*!40000 ALTER TABLE `personnel_paie` DISABLE KEYS */;
INSERT INTO `personnel_paie` VALUES (1,1000000.00,500000.00,0.00,1.00,30000.00,270000.00,1470000.00,1470000.00,'2024-10-24','En attente','2024-10-24','2024-10-24','2024-10-24','2024-10-24 08:37:39.445758','24 October - 24 October',1);
/*!40000 ALTER TABLE `personnel_paie` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-10-25 21:14:44
