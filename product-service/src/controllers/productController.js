const ProductService = require('../services/productService');

class ProductController {
  async createProduct(req, res) {
    try {
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

      const product = await ProductService.createProduct({
        name,
        description,
        price,
        auto_translate,
        target_languages
      });

      res.status(201).json(product);
    } catch (error) {
      console.error('❌ Error creating product:', error);
      res.status(500).json({ error: 'Failed to create product' });
    }
  }

  async getProduct(req, res) {
    try {
      const productId = parseInt(req.params.id);
      const lang = req.query.lang || 'en';

      if (isNaN(productId)) {
        return res.status(400).json({ error: 'Invalid product ID' });
      }

      const product = await ProductService.getProduct(productId, lang);

      if (!product) {
        return res.status(404).json({ error: 'Product not found' });
      }

      res.json(product);
    } catch (error) {
      console.error('❌ Error fetching product:', error);
      res.status(500).json({ error: 'Failed to fetch product' });
    }
  }

  async listProducts(req, res) {
    try {
      const skip = parseInt(req.query.skip) || 0;
      const limit = parseInt(req.query.limit) || 100;
      const lang = req.query.lang || 'en';

      const products = await ProductService.listProducts(skip, limit, lang);

      res.json(products);
    } catch (error) {
      console.error('❌ Error listing products:', error);
      res.status(500).json({ error: 'Failed to list products' });
    }
  }

  async updateProduct(req, res) {
    try {
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

      const product = await ProductService.updateProduct(productId, {
        name,
        description,
        price,
        auto_translate,
        target_languages
      });

      if (!product) {
        return res.status(404).json({ error: 'Product not found' });
      }

      res.json(product);
    } catch (error) {
      console.error('❌ Error updating product:', error);
      res.status(500).json({ error: 'Failed to update product' });
    }
  }

  async deleteProduct(req, res) {
    try {
      const productId = parseInt(req.params.id);

      if (isNaN(productId)) {
        return res.status(400).json({ error: 'Invalid product ID' });
      }

      const deleted = await ProductService.deleteProduct(productId);

      if (deleted === null) {
         return res.status(404).json({ error: 'Product not found' });
      }

      console.log(`✅ Deleted product: ${productId}`);
      res.json({ message: `Product ${productId} deleted successfully` });
    } catch (error) {
      console.error('❌ Error deleting product:', error);
      // Check if it's the translation deletion error
      if (error.message.includes('Product deletion aborted')) {
        return res.status(500).json({
           error: 'Failed to delete associated translations. Product deletion aborted.'
        });
      }
      res.status(500).json({ error: 'Failed to delete product' });
    }
  }
}

module.exports = new ProductController();
