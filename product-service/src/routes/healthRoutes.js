const express = require('express');
const router = express.Router();

/**
 * @swagger
 * /:
 *   get:
 *     summary: Get service information
 *     description: Returns basic information about the Product Service
 *     tags: [Service Info]
 *     responses:
 *       200:
 *         description: Service information
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 service:
 *                   type: string
 *                 status:
 *                   type: string
 *                 version:
 *                   type: string
 *                 technology:
 *                   type: string
 */
router.get('/', (req, res) => {
  res.json({
    service: 'Product Service',
    status: 'running',
    version: '1.0.0',
    technology: 'Node.js + Express.js (Sequelize)',
  });
});

/**
 * @swagger
 * /health:
 *   get:
 *     summary: Health check
 *     description: Check if the service is healthy
 *     tags: [Service Info]
 *     responses:
 *       200:
 *         description: Service is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: healthy
 */
router.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

module.exports = router;
