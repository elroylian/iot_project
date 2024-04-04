-- Create the iot database if it doesn't exist
CREATE DATABASE IF NOT EXISTS iot_project;

-- Switch to the iot database
USE iot_project;

-- Create the sensor_data table to store temperature, humidity, MAC address, and timestamp
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mac_address VARCHAR(17) NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    rssi INT NOT NULL,
    timestamp VARCHAR(19)
);

INSERT INTO sensor_data (mac_address, temperature, humidity, rssi, timestamp)
VALUES
('4c:75:25:cb:7f:50', 26.5, 85, -78, '2024-04-03 16:25:30'),
('4c:75:25:cb:94:ac', 26.5, 59, -78, '2024-04-03 16:25:30'),
('4c:75:25:cb:7f:50', 29.8, 85, -78, '2024-04-03 16:26:02'),
('4c:75:25:cb:94:ac', 29.8, 59, -78, '2024-04-03 16:26:02'),
('4c:75:25:cb:7f:50', 25.7, 82, -75, '2024-04-03 16:27:14'),
('4c:75:25:cb:94:ac', 25.7, 56, -75, '2024-04-03 16:27:14'),
('4c:75:25:cb:7f:50', 28.9, 82, -75, '2024-04-03 16:28:05'),
('4c:75:25:cb:94:ac', 28.9, 56, -75, '2024-04-03 16:28:05'),
('4c:75:25:cb:7f:50', 24.8, 79, -72, '2024-04-03 16:29:20'),
('4c:75:25:cb:94:ac', 24.8, 53, -72, '2024-04-03 16:29:20');

