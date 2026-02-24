require('dotenv').config();
const app = require('./app');
const sequelize = require('./config/sequelize');

const PORT = process.env.PORT || 3000;

async function startServer() {
  try {
    // Initialize database
    await sequelize.authenticate();
    console.log('✅ Connected to PostgreSQL database via Sequelize');

    // Sync models (create tables if not exist)
    await sequelize.sync();
    console.log('✅ Database schema synced');

    // Start listening
    app.listen(PORT, '0.0.0.0', () => {
      console.log('='.repeat(50));
      console.log(`🚀 Product Service (Node.js + Express) running on port ${PORT}`);
      console.log(`📍 http://localhost:${PORT}`);
      console.log('='.repeat(50));
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
