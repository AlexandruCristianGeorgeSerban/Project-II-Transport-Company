# Transport Company Management System
## 1. Introduction
## 1.1. Purpose of the document
	Defines requirements for a system managing routes, vehicles, tickets, and passengers
## 1.2. Aim of the project
The system will be implemented as a client–server application in order to support the operations of a transport company. It will include three major components:
an administrative module for managing the vehicle fleet and employed drivers
a client module where customers can request transport services for specific merchandise
a company‑side allocation module where staff can assign vehicles, drivers, and generate price offers for each request
## 2.  Description
The Transport Company Management System is an information system designed to assist a logistics or freight transport company in managing its operational resources and handling customer service requests efficiently.
The administration of the company’s resources will be carried out in two stages. In the first stage, administrators will define the vehicle fleet, specifying details such as vehicle type, capacity, fuel type, availability status, and maintenance schedule. In the second stage, the system will manage the list of employed drivers, storing information such as licenses, experience, assigned vehicles, and availability.
Customers will interact with the system through a dedicated interface where they can submit transport requests. Each request will include details about the merchandise, weight, volume, pickup and delivery locations, and preferred dates. The system will store these requests and notify the company’s logistics staff.

The company will use a specialized allocation module to process incoming requests. For each request, staff will select an appropriate vehicle and an available driver based on capacity, route, and scheduling constraints. The system will then generate a price offer, which will be communicated to the customer. Once the customer accepts the offer, the transport job will be scheduled and tracked.
The information system will allow graphical visualization of the fleet, driver availability, and active transport requests through intuitive interfaces
## 3. System requirements
CF_1 The list of vehicle types will be chosen from a predefined set. It will also be possible to add new vehicle types that can be saved.
CF_2 Each vehicle will have a graphic representation, and relationships between vehicles, drivers, and assigned transport jobs will be represented by oriented and annotated lines.
CF_3 Each vehicle entry will allow the addition and visualization of information such as capacity, fuel type, availability, maintenance status, and assigned driver.
CF_4 The complete fleet configuration and driver list will be saved in a file in a predetermined format.
CF_5 Administrators will be able to add, modify, activate, or deactivate drivers. Each driver will have a profile containing personal data, licenses, experience, and availability.
CF_6 Customers will be able to create an account and submit transport requests specifying merchandise details, pickup/delivery locations, and preferred dates.
CF_7 The system will store all incoming requests and notify company staff for processing.
CF_8 Company staff will be able to allocate a vehicle and a driver to each request, based on availability and capacity constraints.
CF_9 The system will automatically generate a price offer for each request, based on distance, merchandise characteristics, and resource usage.
CF_10 Customers will receive the price offer and will be able to accept or reject it through the system.
CF_11 Once accepted, the system will schedule the transport job and update the availability of the assigned vehicle and driver.
CF_12 The system will allow searching for vehicles, drivers, or transport requests by name, type, status, or date.
CF_13 The system will allow administrators and company staff to generate reports regarding fleet usage, driver activity, and completed transport jobs.
CF_14 Each transport request and resource assignment will have a “fingerprint” indicating the last person who made changes to it.
CF_15 Both the client and the server will have a simple and intuitive graphical interface.
CF_16 A database server will be configured for storing and managing all information
