require('dotenv').config();
const { Sequelize } = require('sequelize');

const sequelize = new Sequelize(
  process.env.DB_NAME || 'products_db',
  process.env.DB_USER || 'product_user',
  process.env.DB_PASSWORD || 'product_pass',
  {
    host: process.env.DB_HOST || 'product-db',
    port: process.env.DB_PORT || 5432,
    dialect: 'postgres',
    logging: false,
  }
);

module.exports = sequelize;
