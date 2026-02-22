require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./swagger');
const sequelize = require('./config/sequelize');
const Product = require('./models/Product');
const { requestTranslation, getTranslation, deleteTranslations } = require('./translationClient');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Swagger UI
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.use('/api-docs.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(swaggerSpec);
});

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

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
app.get('/', (req, res) => {
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
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

/**
 * @swagger
 * /products:
 *   post:
 *     summary: Create a new product
 *     description: Create a new product and optionally trigger translations
 *     tags: [Products]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ProductCreate'
 *     responses:
 *       201:
 *         description: Product created successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Product'
 *       400:
 *         description: Bad request
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
app.post('/products', async (req, res) => {
  const {
    name,
    description,
    price = null,
    auto_translate = true,
    target_languages = ['es', 'fr', 'de'],
  } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Product name is required' });
  }

  if (!description) {
    return res.status(400).json({ error: 'Product description is required' });
  }

  try {
    // Insert product into database
    const product = await Product.create({
      name,
      description,
      price
    });

    console.log(`✅ Created product: ${product.id} - ${product.name}`);

    // Request translations if enabled
    if (auto_translate && target_languages.length > 0) {
      console.log(`🌐 Requesting translations for product ${product.id}`);
      
      // Fire and forget - don't wait for translation to complete
      requestTranslation(product.id, name, description, target_languages)
        .catch(err => console.error('Translation request error:', err));
    }

    res.status(201).json({
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    });
  } catch (error) {
    console.error('❌ Error creating product:', error);
    res.status(500).json({ error: 'Failed to create product' });
  }
});

/**
 * @swagger
 * /products/{id}:
 *   get:
 *     summary: Get a product by ID
 *     description: Retrieve a product by its ID, optionally in a specific language
 *     tags: [Products]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: Product ID
 *       - in: query
 *         name: lang
 *         schema:
 *           type: string
 *           default: en
 *         description: Language code (en, es, fr, de, etc.)
 *     responses:
 *       200:
 *         description: Product retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Product'
 *       400:
 *         description: Invalid product ID
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       404:
 *         description: Product not found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
app.get('/products/:id', async (req, res) => {
  const productId = parseInt(req.params.id);
  const lang = req.query.lang || 'en';

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  try {
    // Get product from database
    const product = await Product.findByPk(productId);

    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // If English or no language specified, return original
    if (lang === 'en') {
      return res.json({
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      });
    }

    // Get translation
    const translation = await getTranslation(product.id, lang);

    if (translation) {
      const translatedName = (translation.is_edited && translation.edited_name)
        ? translation.edited_name
        : translation.translated_name;

      const translatedDescription = (translation.is_edited && translation.edited_description)
        ? translation.edited_description
        : translation.translated_description;

      return res.json({
        id: product.id,
        name: translatedName,
        description: translatedDescription,
        price: product.price ? parseFloat(product.price) : null,
        lang: lang,
      });
    } else {
      // Fallback to English if translation not found
      console.warn(`⚠️  Translation not found for product ${productId} in ${lang}, falling back to English`);
      return res.json({
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      });
    }
  } catch (error) {
    console.error('❌ Error fetching product:', error);
    res.status(500).json({ error: 'Failed to fetch product' });
  }
});

/**
 * @swagger
 * /products:
 *   get:
 *     summary: List all products
 *     description: Retrieve a list of products with pagination, optionally in a specific language
 *     tags: [Products]
 *     parameters:
 *       - in: query
 *         name: skip
 *         schema:
 *           type: integer
 *           default: 0
 *         description: Number of products to skip
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 100
 *         description: Maximum number of products to return
 *       - in: query
 *         name: lang
 *         schema:
 *           type: string
 *           default: en
 *         description: Language code (en, es, fr, de, etc.)
 *     responses:
 *       200:
 *         description: List of products
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Product'
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
app.get('/products', async (req, res) => {
  const skip = parseInt(req.query.skip) || 0;
  const limit = parseInt(req.query.limit) || 100;
  const lang = req.query.lang || 'en';

  try {
    const products = await Product.findAll({
      offset: skip,
      limit: limit,
      order: [['id', 'ASC']]
    });

    const responseProducts = [];

    for (const product of products) {
      if (lang === 'en') {
        responseProducts.push({
          id: product.id,
          name: product.name,
          description: product.description,
          price: product.price ? parseFloat(product.price) : null,
          lang: 'en',
        });
      } else {
        // Try to get translation
        const translation = await getTranslation(product.id, lang);
        if (translation) {
          const translatedName = (translation.is_edited && translation.edited_name)
            ? translation.edited_name
            : translation.translated_name;

          const translatedDescription = (translation.is_edited && translation.edited_description)
            ? translation.edited_description
            : translation.translated_description;

          responseProducts.push({
            id: product.id,
            name: translatedName,
            description: translatedDescription,
            price: product.price ? parseFloat(product.price) : null,
            lang: lang,
          });
        } else {
          // Fallback to English
          responseProducts.push({
            id: product.id,
            name: product.name,
            description: product.description,
            price: product.price ? parseFloat(product.price) : null,
            lang: 'en',
          });
        }
      }
    }

    res.json(responseProducts);
  } catch (error) {
    console.error('❌ Error listing products:', error);
    res.status(500).json({ error: 'Failed to list products' });
  }
});

/**
 * @swagger
 * /products/{id}:
 *   put:
 *     summary: Update a product
 *     description: Update an existing product and optionally trigger translations
 *     tags: [Products]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: Product ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/ProductCreate'
 *     responses:
 *       200:
 *         description: Product updated successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Product'
 *       400:
 *         description: Bad request
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       404:
 *         description: Product not found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
app.put('/products/:id', async (req, res) => {
  const productId = parseInt(req.params.id);
  const {
    name,
    description,
    price = null,
    auto_translate = true,
    target_languages = ['es', 'fr', 'de'],
  } = req.body;

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  if (!name) {
    return res.status(400).json({ error: 'Product name is required' });
  }

  if (!description) {
    return res.status(400).json({ error: 'Product description is required' });
  }

  try {
    // Update product in database
    const [affectedCount, affectedRows] = await Product.update(
      { name, description, price, updated_at: new Date() },
      { where: { id: productId }, returning: true }
    );

    if (affectedCount === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const product = affectedRows[0];
    console.log(`✅ Updated product: ${product.id} - ${product.name}`);

    // Request new translations if enabled
    if (auto_translate && target_languages.length > 0) {
      console.log(`🌐 Requesting translations for updated product ${product.id}`);
      
      requestTranslation(product.id, name, description, target_languages)
        .catch(err => console.error('Translation request error:', err));
    }

    res.json({
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    });
  } catch (error) {
    console.error('❌ Error updating product:', error);
    res.status(500).json({ error: 'Failed to update product' });
  }
});

/**
 * @swagger
 * /products/{id}:
 *   delete:
 *     summary: Delete a product
 *     description: Delete an existing product by ID
 *     tags: [Products]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: Product ID
 *     responses:
 *       200:
 *         description: Product deleted successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Product 1 deleted successfully
 *       400:
 *         description: Invalid product ID
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       404:
 *         description: Product not found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
app.delete('/products/:id', async (req, res) => {
  const productId = parseInt(req.params.id);

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  try {
    // Check if product exists first
    const product = await Product.findByPk(productId);
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // Attempt to delete translations first
    try {
      console.log(`🗑️  Deleting translations for product ${productId}...`);
      await deleteTranslations(productId);
      console.log(`✅ Translations deleted for product ${productId}`);
    } catch (translationError) {
      console.error(`❌ Aborting product deletion. Failed to delete translations:`, translationError.message);
      return res.status(500).json({
        error: 'Failed to delete associated translations. Product deletion aborted.'
      });
    }

    // Delete product from database
    const deletedCount = await Product.destroy({ where: { id: productId } });

    if (deletedCount === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    console.log(`✅ Deleted product: ${productId}`);
    res.json({ message: `Product ${productId} deleted successfully` });
  } catch (error) {
    console.error('❌ Error deleting product:', error);
    res.status(500).json({ error: 'Failed to delete product' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('❌ Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
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
