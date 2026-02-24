const swaggerJsdoc = require('swagger-jsdoc');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Product Service API',
      version: '1.0.0',
      description: 'Main Product Service with multi-language translation support using Node.js and Express.js',
      contact: {
        name: 'Manus AI',
      },
    },
    servers: [
      {
        url: 'http://localhost:3000',
        description: 'Development server',
      },
    ],
    components: {
      schemas: {
        Product: {
          type: 'object',
          properties: {
            id: {
              type: 'integer',
              description: 'Product ID',
              example: 1,
            },
            name: {
              type: 'string',
              description: 'Product name',
              example: 'Wireless Headphones',
            },
            description: {
              type: 'string',
              description: 'Product description',
              example: 'High-quality noise-cancelling headphones',
            },
            price: {
              type: 'number',
              format: 'float',
              description: 'Product price',
              example: 199.99,
            },
            lang: {
              type: 'string',
              description: 'Language code',
              example: 'en',
            },
          },
        },
        ProductCreate: {
          type: 'object',
          required: ['name', 'description'],
          properties: {
            name: {
              type: 'string',
              description: 'Product name',
              example: 'Wireless Headphones',
            },
            description: {
              type: 'string',
              description: 'Product description',
              example: 'High-quality noise-cancelling headphones',
            },
            price: {
              type: 'number',
              format: 'float',
              description: 'Product price',
              example: 199.99,
            },
            auto_translate: {
              type: 'boolean',
              description: 'Automatically translate product to other languages',
              default: true,
            },
            target_languages: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'Target languages for translation',
              example: ['es', 'fr', 'de'],
            },
          },
        },
        Error: {
          type: 'object',
          properties: {
            error: {
              type: 'string',
              description: 'Error message',
            },
          },
        },
      },
    },
  },
  apis: ['./src/routes/*.js'], // Path to the API routes
};

const swaggerSpec = swaggerJsdoc(options);

module.exports = swaggerSpec;
