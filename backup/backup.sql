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
-- Table structure for table `accounts_customuser`
--

DROP TABLE IF EXISTS `accounts_customuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_customuser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `photo` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_customuser`
--

LOCK TABLES `accounts_customuser` WRITE;
/*!40000 ALTER TABLE `accounts_customuser` DISABLE KEYS */;
INSERT INTO `accounts_customuser` VALUES (1,'pbkdf2_sha256$870000$UnmsjY6dgnUrlwLKLWVxoD$0m+zrFx5j/eBD8Be0sXG8k6WWyrz/sKvaj/PBQ4RtLE=','2024-10-22 07:51:55.867288',1,'admin','','','admin@gmail.com',1,1,'2024-10-10 11:42:29.422332','photos/pdp_defaut.png'),(2,'pbkdf2_sha256$870000$arOqi1H5kqgASQE4Hra0o9$xOwBhNE3QxEetUROtLwsw20hHrea6hzLEs7fbHMIeyU=','2024-10-14 09:32:42.809570',0,'dzoubery','','','dzoubery@gmail.com',0,1,'2024-10-10 11:51:06.885170','photos/pdp_defaut.png'),(3,'pbkdf2_sha256$870000$CiIZsViTtTKfCSAISPeIQS$HpZ+DxF2Z9clBaOkfyJDoyaiZA096UnWTI6v+Kk3mQ4=','2024-10-16 19:28:30.221205',0,'kemuelebezara205','','','kemuelebezara205@gmail.com',0,1,'2024-10-14 11:39:24.613304','photos/WhatsApp_Image_2024-09-27_at_10.54.50.jpeg'),(4,'pbkdf2_sha256$870000$PsmblG4tyoAuLFux6iTb12$bfAui3h4S7IqHuMwtwptP/hr3OTKltLjmDQih7ldUD4=','2024-10-22 13:51:26.931565',0,'Zepelin19','','','Zepelin19@gmail.com',0,1,'2024-10-17 07:58:28.113283','photos/defaut.png'),(5,'pbkdf2_sha256$870000$sFVkDE39jm1MF1d0KEgNyl$idWmtXB1OQz/0RhmEI1M3ZjcNBaaYGAis2+FWcU2w0A=','2024-10-17 11:58:30.924356',0,'ODddaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','','','ODdd@gmail.com',0,1,'2024-10-17 11:49:16.000000','photos/defaut.png');
/*!40000 ALTER TABLE `accounts_customuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_customuser_groups`
--

DROP TABLE IF EXISTS `accounts_customuser_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_customuser_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customuser_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_customuser_groups_customuser_id_group_id_c074bdcb_uniq` (`customuser_id`,`group_id`),
  KEY `accounts_customuser_groups_customuser_id_bc55088e` (`customuser_id`),
  KEY `accounts_customuser_groups_group_id_86ba5f9e` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_customuser_groups`
--

LOCK TABLES `accounts_customuser_groups` WRITE;
/*!40000 ALTER TABLE `accounts_customuser_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_customuser_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_customuser_user_permissions`
--

DROP TABLE IF EXISTS `accounts_customuser_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_customuser_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customuser_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_customuser_user_customuser_id_permission_9632a709_uniq` (`customuser_id`,`permission_id`),
  KEY `accounts_customuser_user_permissions_customuser_id_0deaefae` (`customuser_id`),
  KEY `accounts_customuser_user_permissions_permission_id_aea3d0e5` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=181 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_customuser_user_permissions`
--

LOCK TABLES `accounts_customuser_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_customuser_user_permissions` DISABLE KEYS */;
INSERT INTO `accounts_customuser_user_permissions` VALUES (1,2,32),(2,2,64),(3,2,2),(4,2,65),(5,2,66),(6,2,68),(7,2,40),(8,2,72),(9,2,44),(10,2,45),(11,2,46),(12,2,60),(13,2,48),(14,2,49),(15,2,53),(16,2,54),(17,2,56),(18,2,28),(19,3,1),(20,3,2),(21,3,3),(22,3,4),(23,3,5),(24,3,6),(25,3,7),(26,3,8),(27,3,9),(28,3,10),(29,3,11),(30,3,12),(31,3,13),(32,3,14),(33,3,15),(34,3,16),(35,3,17),(36,3,18),(37,3,19),(38,3,20),(39,3,21),(40,3,22),(41,3,23),(42,3,24),(43,3,25),(44,3,26),(45,3,27),(46,3,28),(47,3,29),(48,3,30),(49,3,31),(50,3,32),(51,3,33),(52,3,34),(53,3,35),(54,3,36),(55,3,37),(56,3,38),(57,3,39),(58,3,40),(59,3,41),(60,3,42),(61,3,43),(62,3,44),(63,3,45),(64,3,46),(65,3,47),(66,3,48),(67,3,49),(68,3,50),(69,3,51),(70,3,52),(71,3,53),(72,3,54),(73,3,55),(74,3,56),(75,3,57),(76,3,58),(77,3,59),(78,3,60),(79,3,61),(80,3,62),(81,3,63),(82,3,64),(83,3,65),(84,3,66),(85,3,67),(86,3,68),(87,3,69),(88,3,70),(89,3,71),(90,3,72),(91,4,1),(92,4,2),(93,4,3),(94,4,4),(95,4,5),(96,4,6),(97,4,7),(98,4,8),(99,4,9),(100,4,10),(101,4,11),(102,4,12),(103,4,13),(104,4,14),(105,4,15),(106,4,16),(107,4,17),(108,4,18),(109,4,19),(110,4,20),(111,4,21),(112,4,22),(113,4,23),(114,4,24),(115,4,25),(116,4,26),(117,4,27),(118,4,28),(119,4,29),(120,4,30),(121,4,31),(122,4,32),(123,4,33),(124,4,34),(125,4,35),(126,4,36),(127,4,37),(128,4,38),(129,4,39),(130,4,40),(131,4,41),(132,4,42),(133,4,43),(134,4,44),(135,4,45),(136,4,46),(137,4,47),(138,4,48),(139,4,49),(140,4,50),(141,4,51),(142,4,52),(143,4,53),(144,4,54),(145,4,55),(146,4,56),(147,4,57),(148,4,58),(149,4,59),(150,4,60),(151,4,61),(152,4,62),(153,4,63),(154,4,64),(155,4,65),(156,4,66),(157,4,67),(158,4,68),(159,4,69),(160,4,70),(161,4,71),(162,4,72),(163,5,32),(164,5,64),(165,5,2),(166,5,65),(167,5,66),(168,5,68),(169,5,40),(170,5,72),(171,5,44),(172,5,45),(173,5,46),(174,5,60),(175,5,48),(176,5,49),(177,5,53),(178,5,54),(179,5,56),(180,5,28);
/*!40000 ALTER TABLE `accounts_customuser_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'Salarié'),(2,'Direction'),(3,'Assist_direction'),(4,'Bénévole'),(5,'Stagiaire'),(6,'Freelance');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
  KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`)
) ENGINE=MyISAM AUTO_INCREMENT=151 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
INSERT INTO `auth_group_permissions` VALUES (1,1,2),(2,2,1),(3,2,2),(4,2,3),(5,2,4),(6,2,5),(7,2,6),(8,2,7),(9,2,8),(10,2,9),(11,2,10),(12,2,11),(13,2,12),(14,2,13),(15,2,14),(16,2,15),(17,2,16),(18,2,17),(19,2,18),(20,2,19),(21,2,20),(22,2,21),(23,2,22),(24,2,23),(25,2,24),(26,2,25),(27,2,26),(28,2,27),(29,2,28),(30,2,29),(31,2,30),(32,2,31),(33,2,32),(34,2,33),(35,2,34),(36,2,35),(37,2,36),(38,2,37),(39,2,38),(40,2,39),(41,2,40),(42,2,41),(43,2,42),(44,2,43),(45,2,44),(46,2,45),(47,2,46),(48,2,47),(49,2,48),(50,2,49),(51,2,50),(52,2,51),(53,2,52),(54,2,53),(55,2,54),(56,2,55),(57,2,56),(58,2,57),(59,2,58),(60,2,59),(61,2,60),(62,2,61),(63,2,62),(64,2,63),(65,2,64),(66,2,65),(67,2,66),(68,2,67),(69,2,68),(70,2,69),(71,2,70),(72,2,71),(73,2,72),(74,3,37),(75,3,38),(76,3,39),(77,3,40),(78,3,41),(79,3,42),(80,3,44),(81,3,45),(82,3,46),(83,3,47),(84,3,48),(85,3,49),(86,3,53),(87,3,54),(88,3,56),(89,3,61),(90,3,62),(91,3,63),(92,3,64),(93,3,65),(94,3,66),(95,3,68),(96,3,69),(97,3,70),(98,3,72),(99,4,40),(100,4,64),(122,6,32),(102,6,64),(103,1,32),(104,1,64),(105,1,65),(106,1,66),(107,1,68),(108,1,40),(109,1,72),(110,1,44),(111,1,45),(112,1,46),(113,1,60),(114,1,48),(115,1,49),(116,1,53),(117,1,54),(118,1,56),(119,1,28),(120,3,32),(121,3,60),(123,6,65),(124,6,66),(125,6,68),(126,6,44),(127,6,60),(128,6,49),(129,6,53),(130,6,28),(131,4,65),(132,4,66),(133,4,68),(134,4,44),(135,4,49),(136,4,53),(137,4,54),(138,4,56),(139,5,32),(140,5,64),(141,5,65),(142,5,66),(143,5,68),(144,5,60),(145,5,49),(146,5,53),(147,5,54),(148,5,56),(149,5,28),(150,6,40);
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=73 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add user',6,'add_customuser'),(22,'Can change user',6,'change_customuser'),(23,'Can delete user',6,'delete_customuser'),(24,'Can view user',6,'view_customuser'),(25,'Can add agenda event',7,'add_agendaevent'),(26,'Can change agenda event',7,'change_agendaevent'),(27,'Can delete agenda event',7,'delete_agendaevent'),(28,'Can view agenda event',7,'view_agendaevent'),(29,'Can add competence',8,'add_competence'),(30,'Can change competence',8,'change_competence'),(31,'Can delete competence',8,'delete_competence'),(32,'Can view competence',8,'view_competence'),(33,'Can add departement',9,'add_departement'),(34,'Can change departement',9,'change_departement'),(35,'Can delete departement',9,'delete_departement'),(36,'Can view departement',9,'view_departement'),(37,'Can add employee',10,'add_employee'),(38,'Can change employee',10,'change_employee'),(39,'Can delete employee',10,'delete_employee'),(40,'Can view employee',10,'view_employee'),(41,'Can add conge',11,'add_conge'),(42,'Can change conge',11,'change_conge'),(43,'Can delete conge',11,'delete_conge'),(44,'Can view conge',11,'view_conge'),(45,'Can add historique',12,'add_historique'),(46,'Can change historique',12,'change_historique'),(47,'Can delete historique',12,'delete_historique'),(48,'Can view historique',12,'view_historique'),(49,'Can add notification',13,'add_notification'),(50,'Can change notification',13,'change_notification'),(51,'Can delete notification',13,'delete_notification'),(52,'Can view notification',13,'view_notification'),(53,'Can add paie',14,'add_paie'),(54,'Can change paie',14,'change_paie'),(55,'Can delete paie',14,'delete_paie'),(56,'Can view paie',14,'view_paie'),(57,'Can add poste',15,'add_poste'),(58,'Can change poste',15,'change_poste'),(59,'Can delete poste',15,'delete_poste'),(60,'Can view poste',15,'view_poste'),(61,'Can add schedule',16,'add_schedule'),(62,'Can change schedule',16,'change_schedule'),(63,'Can delete schedule',16,'delete_schedule'),(64,'Can view schedule',16,'view_schedule'),(65,'Can add user notification',17,'add_usernotification'),(66,'Can change user notification',17,'change_usernotification'),(67,'Can delete user notification',17,'delete_usernotification'),(68,'Can view user notification',17,'view_usernotification'),(69,'Can add user settings',18,'add_usersettings'),(70,'Can change user settings',18,'change_usersettings'),(71,'Can delete user settings',18,'delete_usersettings'),(72,'Can view user settings',18,'view_usersettings');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6` (`user_id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=MyISAM AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2024-10-10 11:50:27.228823','1','Dev',1,'[{\"added\": {}}]',9,1),(2,'2024-10-10 11:50:31.679674','1','Python',1,'[{\"added\": {}}]',8,1),(3,'2024-10-10 11:50:39.879029','1','Dev Devellopeur_Fullstack',1,'[{\"added\": {}}]',15,1),(4,'2024-10-10 11:51:08.595818','1','ZOUBERY Jaotiana Donaldo',1,'[{\"added\": {}}]',10,1),(5,'2024-10-14 11:39:27.130900','2','BEZARA Kemuel Kelub',1,'[{\"added\": {}}]',10,1),(6,'2024-10-16 18:58:48.570600','1','Fin stage',1,'[{\"added\": {}}]',7,1),(7,'2024-10-16 18:59:37.460370','2','Daily',1,'[{\"added\": {}}]',7,1),(8,'2024-10-16 18:59:58.138118','3','Manger',1,'[{\"added\": {}}]',7,1),(9,'2024-10-17 07:55:13.602934','2','Direction',1,'[{\"added\": {}}]',9,1),(10,'2024-10-17 07:55:24.763819','2','Direction',1,'[{\"added\": {}}]',15,1),(11,'2024-10-17 07:56:49.054130','2','Manager',2,'[{\"changed\": {\"fields\": [\"Nom\"]}}]',15,1),(12,'2024-10-17 07:57:32.584838','3','Direction',1,'[{\"added\": {}}]',9,1),(13,'2024-10-17 07:58:29.118739','3','ZANDRY Zepelin',1,'[{\"added\": {}}]',10,1),(14,'2024-10-17 11:49:17.692858','4','MARC Odilon',1,'[{\"added\": {}}]',10,1),(15,'2024-10-17 11:56:48.316847','3','Assistant_Direction',1,'[{\"added\": {}}]',15,1),(16,'2024-10-17 11:56:51.099595','4','MARC Odilon',2,'[{\"changed\": {\"fields\": [\"User\", \"Email\", \"Poste\"]}}]',10,1),(17,'2024-10-17 11:57:37.126099','5','ODddaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',2,'[{\"changed\": {\"fields\": [\"Username\"]}}]',6,1),(18,'2024-10-17 11:57:43.950578','4','MARC Odilon',2,'[{\"changed\": {\"fields\": [\"User\"]}}]',10,1),(19,'2024-10-18 12:33:22.994448','1','ZANDRY Zepelin - ANN du 2024-10-18 au 2024-10-19 - en_attente',1,'[{\"added\": {}}]',11,1),(20,'2024-10-22 07:52:09.501162','2','Java',1,'[{\"added\": {}}]',8,1),(21,'2024-10-22 07:52:57.593803','3','Html',1,'[{\"added\": {}}]',8,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(2,'auth','permission'),(3,'auth','group'),(4,'contenttypes','contenttype'),(5,'sessions','session'),(6,'accounts','customuser'),(7,'personnel','agendaevent'),(8,'personnel','competence'),(9,'personnel','departement'),(10,'personnel','employee'),(11,'personnel','conge'),(12,'personnel','historique'),(13,'personnel','notification'),(14,'personnel','paie'),(15,'personnel','poste'),(16,'personnel','schedule'),(17,'personnel','usernotification'),(18,'personnel','usersettings');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-10-10 11:40:07.308348'),(2,'contenttypes','0002_remove_content_type_name','2024-10-10 11:40:07.427154'),(3,'auth','0001_initial','2024-10-10 11:40:07.991310'),(4,'auth','0002_alter_permission_name_max_length','2024-10-10 11:40:08.051095'),(5,'auth','0003_alter_user_email_max_length','2024-10-10 11:40:08.059210'),(6,'auth','0004_alter_user_username_opts','2024-10-10 11:40:08.067155'),(7,'auth','0005_alter_user_last_login_null','2024-10-10 11:40:08.077380'),(8,'auth','0006_require_contenttypes_0002','2024-10-10 11:40:08.079188'),(9,'auth','0007_alter_validators_add_error_messages','2024-10-10 11:40:08.088835'),(10,'auth','0008_alter_user_username_max_length','2024-10-10 11:40:08.098835'),(11,'auth','0009_alter_user_last_name_max_length','2024-10-10 11:40:08.111416'),(12,'auth','0010_alter_group_name_max_length','2024-10-10 11:40:08.163933'),(13,'auth','0011_update_proxy_permissions','2024-10-10 11:40:08.169650'),(14,'auth','0012_alter_user_first_name_max_length','2024-10-10 11:40:08.173647'),(15,'accounts','0001_initial','2024-10-10 11:40:08.781591'),(16,'admin','0001_initial','2024-10-10 11:40:09.201679'),(17,'admin','0002_logentry_remove_auto_add','2024-10-10 11:40:09.208792'),(18,'admin','0003_logentry_add_action_flag_choices','2024-10-10 11:40:09.220795'),(19,'personnel','0001_initial','2024-10-10 11:40:11.967304'),(20,'sessions','0001_initial','2024-10-10 11:40:12.030130'),(21,'personnel','0002_alter_employee_photo_alter_notification_type','2024-10-18 12:47:43.766419');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('i96as07d7dkfpvseo8bdya7j4srt2ocb','.eJxVjMEKwyAQRP_FcxGNothj7_0GWXfXmrYoxOQU-u81kEN7GZh5M7OLCNta4tZ5iTOJq7Di8pslwBfXA9AT6qNJbHVd5iSPijxpl_dG_L6d3b-DAr2MtQoWMU-TR8puiEnkgwadLBinrULgQTITG2WcHzw5QBUcaDVMEJ8vDpY5Cw:1t3FIE:aa-bS_-wCekeWBTi9ouXDCet68AOUsOlFd_VLfKm6xE','2024-11-05 13:51:26.933565');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_agendaevent`
--

DROP TABLE IF EXISTS `personnel_agendaevent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_agendaevent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `start_time` time(6) NOT NULL,
  `start_date` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_agendaevent`
--

LOCK TABLES `personnel_agendaevent` WRITE;
/*!40000 ALTER TABLE `personnel_agendaevent` DISABLE KEYS */;
INSERT INTO `personnel_agendaevent` VALUES (1,'Fin stage','Ist Stagiaire','18:57:51.000000','2024-10-17 18:58:15.000000','2024-10-16 18:58:48.557770'),(2,'Daily','Tout le monde','18:59:25.000000','2024-10-16 18:59:28.000000','2024-10-16 18:59:37.458390'),(3,'Manger','Tout','18:59:50.000000','2024-10-16 18:59:56.000000','2024-10-16 18:59:58.136118');
/*!40000 ALTER TABLE `personnel_agendaevent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_competence`
--

DROP TABLE IF EXISTS `personnel_competence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_competence` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_competence`
--

LOCK TABLES `personnel_competence` WRITE;
/*!40000 ALTER TABLE `personnel_competence` DISABLE KEYS */;
INSERT INTO `personnel_competence` VALUES (1,'Python'),(2,'Java'),(3,'Html');
/*!40000 ALTER TABLE `personnel_competence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_conge`
--

DROP TABLE IF EXISTS `personnel_conge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_conge` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type_conge` varchar(3) NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `jours_utilises` int unsigned NOT NULL,
  `statut` varchar(20) NOT NULL,
  `raison` longtext,
  `piece_justificatif` varchar(100) DEFAULT NULL,
  `date_demande` datetime(6) NOT NULL,
  `raison_refus` longtext,
  `employee_id` bigint DEFAULT NULL,
  `responsable_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_conge_employee_id_3cd1b188` (`employee_id`),
  KEY `personnel_conge_responsable_id_58a1a820` (`responsable_id`),
  CONSTRAINT `personnel_conge_chk_1` CHECK ((`jours_utilises` >= 0))
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_conge`
--

LOCK TABLES `personnel_conge` WRITE;
/*!40000 ALTER TABLE `personnel_conge` DISABLE KEYS */;
INSERT INTO `personnel_conge` VALUES (1,'ANN','2024-10-18','2024-10-19',2,'en_attente','aze','fichier/style.css','2024-10-18 12:33:18.000000','',3,NULL),(2,'FOR','2024-10-18','2024-10-19',2,'en_attente','zae','fichier/morseé.txt','2024-10-18 14:41:00.000000','',3,NULL),(3,'ANN','2024-10-18','2024-10-19',2,'en_attente','zae','fichier/morseé_XhNl6Bx.txt','2024-10-18 14:41:00.000000','',3,NULL),(4,'ANN','2024-10-18','2024-10-19',2,'en_attente','zae','fichier/morseé_pUx2cyb.txt','2024-10-18 14:41:00.000000','',3,NULL),(5,'EXC','2024-10-19','2024-10-20',1,'accepte','','fichier/Page_connexion.png','2024-10-19 09:01:00.000000','',3,3);
/*!40000 ALTER TABLE `personnel_conge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_departement`
--

DROP TABLE IF EXISTS `personnel_departement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_departement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_departement`
--

LOCK TABLES `personnel_departement` WRITE;
/*!40000 ALTER TABLE `personnel_departement` DISABLE KEYS */;
INSERT INTO `personnel_departement` VALUES (1,'Dev'),(2,'Direction'),(3,'Direction');
/*!40000 ALTER TABLE `personnel_departement` ENABLE KEYS */;
UNLOCK TABLES;

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

--
-- Table structure for table `personnel_historique`
--

DROP TABLE IF EXISTS `personnel_historique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_historique` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(50) NOT NULL,
  `consequence` longtext,
  `utilisateur_affecte` varchar(255) DEFAULT NULL,
  `date_action` datetime(6) NOT NULL,
  `categorie` varchar(50) NOT NULL,
  `utilisateur_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_historique_utilisateur_id_c0753b9e` (`utilisateur_id`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_historique`
--

LOCK TABLES `personnel_historique` WRITE;
/*!40000 ALTER TABLE `personnel_historique` DISABLE KEYS */;
INSERT INTO `personnel_historique` VALUES (1,'login','Utilisateur connecté',NULL,'2024-10-10 11:43:05.382692','session',1),(2,'logout','Utilisateur déconnecté',NULL,'2024-10-10 12:21:27.800915','session',1),(3,'create','Création d\'un congé pour ZANDRY Zepelin.','Zepelin19','2024-10-18 12:47:59.173564','conge',4),(4,'create','Création d\'un congé pour ZANDRY Zepelin.','Zepelin19','2024-10-19 07:01:56.072297','conge',4),(5,'update','Une demande de congé de ZANDRY Zepelin a été approuvée.','Zepelin19','2024-10-19 07:17:59.981877','conge',4);
/*!40000 ALTER TABLE `personnel_historique` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_notification`
--

DROP TABLE IF EXISTS `personnel_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `message` longtext NOT NULL,
  `date_created` datetime(6) NOT NULL,
  `is_global` tinyint(1) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_notification_user_id_96e8d970` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_notification`
--

LOCK TABLES `personnel_notification` WRITE;
/*!40000 ALTER TABLE `personnel_notification` DISABLE KEYS */;
INSERT INTO `personnel_notification` VALUES (1,'demande_congé','Un nouveau congé pour ZANDRY Zepelin a été créé.','2024-10-18 12:47:59.171565',0,4),(2,'demande_congé','Un nouveau congé pour ZANDRY Zepelin a été créé.','2024-10-19 07:01:56.070298',0,4),(3,'conge_approuve','Le congé de ZANDRY a été accepté.','2024-10-19 07:17:59.979877',0,4);
/*!40000 ALTER TABLE `personnel_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_paie`
--

DROP TABLE IF EXISTS `personnel_paie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_paie` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `mois` varchar(20) NOT NULL,
  `matricule` varchar(20) NOT NULL,
  `salaire_base` decimal(10,2) NOT NULL,
  `indemnite_transport` decimal(10,2) NOT NULL,
  `salaire_brut` decimal(10,2) NOT NULL,
  `smids` decimal(10,2) NOT NULL,
  `cnaps` decimal(10,2) NOT NULL,
  `irsa` decimal(10,2) NOT NULL,
  `avance` decimal(10,2) NOT NULL,
  `regul_smids` decimal(10,2) NOT NULL,
  `salaire_net` decimal(10,2) NOT NULL,
  `montant_imposable` decimal(10,2) NOT NULL,
  `date_creation` datetime(6) NOT NULL,
  `signature_directeur` varchar(100) DEFAULT NULL,
  `signature_beneficiaire` varchar(100) DEFAULT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricule` (`matricule`),
  KEY `personnel_paie_employee_id_de02341f` (`employee_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_paie`
--

LOCK TABLES `personnel_paie` WRITE;
/*!40000 ALTER TABLE `personnel_paie` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_paie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_poste`
--

DROP TABLE IF EXISTS `personnel_poste`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_poste` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `departement_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_poste_departement_id_bfdaed49` (`departement_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_poste`
--

LOCK TABLES `personnel_poste` WRITE;
/*!40000 ALTER TABLE `personnel_poste` DISABLE KEYS */;
INSERT INTO `personnel_poste` VALUES (1,'Devellopeur_Fullstack',1),(2,'Manager',2),(3,'Assistant_Direction',2);
/*!40000 ALTER TABLE `personnel_poste` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_schedule`
--

DROP TABLE IF EXISTS `personnel_schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_schedule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `location` varchar(100) NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `jour_debut` varchar(10) DEFAULT NULL,
  `jour_fin` varchar(10) DEFAULT NULL,
  `description` longtext,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_schedule_employee_id_0c26ab51` (`employee_id`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_schedule`
--

LOCK TABLES `personnel_schedule` WRITE;
/*!40000 ALTER TABLE `personnel_schedule` DISABLE KEYS */;
INSERT INTO `personnel_schedule` VALUES (1,'ANKA','18:05:03.000000','19:05:04.000000','2024-10-21','2024-10-25','Lundi','Mercredi','Maintenance',3),(2,'ANKA','18:05:03.000000','19:05:04.000000','2024-10-21','2024-10-25','Lundi','Mercredi','Maintenance',3),(3,'ANKA','18:05:03.000000','19:05:04.000000','2024-10-21','2024-10-25','Lundi','Mercredi','Maintenance',3),(4,'IST','18:10:41.000000','18:10:42.000000','2024-10-21','2024-10-25','Jeudi','Vendredi','Cours',1),(5,'IST','12:00:00.000000','18:10:42.000000','2024-10-21','2024-10-25','Vendredi','Vendredi','Cours MATH',1);
/*!40000 ALTER TABLE `personnel_schedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_usernotification`
--

DROP TABLE IF EXISTS `personnel_usernotification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_usernotification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_read` tinyint(1) NOT NULL,
  `notification_id` bigint NOT NULL,
  `user_affected_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `personnel_usernotification_notification_id_dc0bfc54` (`notification_id`),
  KEY `personnel_usernotification_user_affected_id_f49ab14b` (`user_affected_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_usernotification`
--

LOCK TABLES `personnel_usernotification` WRITE;
/*!40000 ALTER TABLE `personnel_usernotification` DISABLE KEYS */;
INSERT INTO `personnel_usernotification` VALUES (1,0,1,4),(2,0,2,4),(3,0,3,4);
/*!40000 ALTER TABLE `personnel_usernotification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_usersettings`
--

DROP TABLE IF EXISTS `personnel_usersettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_usersettings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `language` varchar(5) NOT NULL,
  `theme` varchar(5) NOT NULL,
  `receive_desktop_notifications` tinyint(1) NOT NULL,
  `receive_email_notifications` tinyint(1) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_usersettings`
--

LOCK TABLES `personnel_usersettings` WRITE;
/*!40000 ALTER TABLE `personnel_usersettings` DISABLE KEYS */;
INSERT INTO `personnel_usersettings` VALUES (1,'fr','light',1,1,2),(2,'fr','light',1,1,3),(3,'fr','light',0,1,4),(4,'fr','light',1,1,5);
/*!40000 ALTER TABLE `personnel_usersettings` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-10-23 10:12:34
