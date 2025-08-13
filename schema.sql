-- ============================
-- Trade Order Management System Schema
-- ============================

-- Drop existing tables
IF OBJECT_ID('Orders', 'U') IS NOT NULL DROP TABLE Orders;
IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;
IF OBJECT_ID('Products', 'U') IS NOT NULL DROP TABLE Products;

-- ============================
-- Products Table
-- ============================
CREATE TABLE Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    ProductName NVARCHAR(100) NOT NULL,
    ProductType NVARCHAR(50),
    Price DECIMAL(18,2)
);

-- ============================
-- Customers Table
-- ============================
CREATE TABLE Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    IsAdmin BIT DEFAULT 0
);

-- ============================
-- Orders Table
-- ============================
CREATE TABLE Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL,
    OrderDate DATETIME DEFAULT GETDATE(),
    Status NVARCHAR(20) CHECK (Status IN ('HOLD', 'SELL')) NOT NULL,
    BuyPrice DECIMAL(18,2) NOT NULL,
    SellPrice DECIMAL(18,2),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE,
    CONSTRAINT FK_Orders_Products FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

-- ============================
-- Sample Products
-- ============================
INSERT INTO Products (ProductName, ProductType, Price) VALUES
('Bitcoin', 'Crypto', 25000.00),
('Ethereum', 'Crypto', 1800.00),
('Solana', 'Crypto', 100.00),
('BNB', 'Crypto', 300.00),
('XRP', 'Crypto', 0.60);

-- ============================
-- Admin Account
-- Password: admin123
-- ============================
INSERT INTO Customers (Name, Email, PasswordHash, IsAdmin)
VALUES (
    'Admin',
    'admin@example.com',
    'scrypt:32768:8:1$wcc5OORwbYRdmYgD$0155c2d45dc52ec54763741dac1c07f031104472f99be8c886b469d10abac0f72f7053890da9dc618208591a63c73df050891f44822e0fac4ebacbdf0b1043c8',
    1
);
